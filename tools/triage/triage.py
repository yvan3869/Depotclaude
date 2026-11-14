#!/usr/bin/env python3
"""Interface de tri des clips et images generes. Aucune dependance.

    python triage.py --dir /workspace/ComfyUI/output
    python triage.py --dir ./output --host 0.0.0.0 --token MONSECRET   # sur un pod

Les fichiers places directement dans --dir sont a trier. Chaque decision
deplace le fichier dans un sous-dossier (soft, paid, redo, reject) et ajoute
une ligne a triage_log.csv. Touches : S, P, R, X, Z (annuler), fleches.
"""
import argparse
import csv
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

BUCKETS = ("soft", "paid", "redo", "reject")
EXTS = {".mp4", ".webm", ".mov", ".png", ".jpg", ".jpeg", ".webp"}
PAGE = (Path(__file__).parent / "index.html").read_bytes()


HERE = Path(__file__).resolve().parent


class Triage:
    def __init__(self, root: Path):
        self.root = root.resolve()
        for b in BUCKETS:
            (self.root / b).mkdir(parents=True, exist_ok=True)
        self.history = []  # (name, bucket)

    def safe(self, base: Path, name: str) -> Path:
        p = (base / name).resolve()
        if p.parent != base.resolve() or not p.is_file():
            raise FileNotFoundError(name)
        return p

    def inbox(self):
        files = [f for f in self.root.iterdir() if f.is_file() and f.suffix.lower() in EXTS]
        return [f.name for f in sorted(files, key=lambda f: f.stat().st_mtime)]

    def counts(self):
        return {b: sum(1 for f in (self.root / b).iterdir() if f.is_file()) for b in BUCKETS}

    def move(self, name: str, bucket: str):
        if bucket not in BUCKETS:
            raise ValueError(bucket)
        src = self.safe(self.root, name)
        shutil.move(str(src), str(self.root / bucket / name))
        self.history.append((name, bucket))
        self.log(name, bucket)

    def undo(self):
        if not self.history:
            return None
        name, bucket = self.history.pop()
        src = self.safe(self.root / bucket, name)
        shutil.move(str(src), str(self.root / name))
        self.log(name, "undo")
        return name

    def log(self, name, decision):
        with open(self.root / "triage_log.csv", "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([time.strftime("%Y-%m-%dT%H:%M:%S"), name, decision])


def write_job(jobs: Path, b: dict) -> dict:
    """Ecrit un fichier de plans en trois temps a partir du formulaire (/nouveau).

    Le fichier est du JSON, que le pilote lit comme du YAML. Chaque temps est un plan ; un temps
    dont la description d'image est vide est omis.
    """
    name = re.sub(r"[^a-z0-9_]+", "_", str(b.get("name", "")).lower()).strip("_")
    if not name:
        raise ValueError("nom du lot obligatoire")
    common = ", ".join(x.strip() for x in (str(b.get("decor", "")), str(b.get("tenue", ""))) if x.strip())
    # LoRA supplementaires : noms du catalogue (lora_catalog), separes par des virgules. Champ vide :
    # le plan garde le reglage general (extra_loras_still).
    loras = []
    for x in str(b.get("loras", "")).split(","):
        nm, _, st = x.strip().partition(":")
        if nm.strip():
            loras.append({"name": nm.strip(), "strength": float(st)} if st.strip() else nm.strip())
    loras = loras or None
    corps = str(b.get("corps", "")).strip()
    shots = []
    for key, dest in (("accroche", "soft"), ("montee", "abonnes"), ("final", "payant")):
        still = str(b.get(f"{key}_still", "")).strip()
        if not still:
            continue
        shot = {"name": f"{len(shots) + 1}_{key}", "dest": dest,
                "still": ", ".join(x for x in (still, common) if x)}
        if corps and dest != "soft":  # description du corps reprise d'un test valide (temps 2 et 3)
            shot["still"] += ", " + corps
        motion = str(b.get(f"{key}_motion", "")).strip()
        parts = [x for x in SPLIT.split(motion) if x.strip()]
        if len(parts) > 1:  # plusieurs actions ("..., puis ...") : sous-scenes enchainees debut/fin
            shot["steps"] = parts
        elif motion:
            shot["motion"] = motion
        end = str(b.get(f"{key}_end", "")).strip()
        if end and motion and "steps" not in shot:  # clip debut/fin : le pilote fabrique l'image de fin a partir de la premiere
            shot["end_edit"] = end
        if not b.get(f"{key}_tattoos", True):
            shot["tattoos"] = False
        if loras is not None:
            shot["loras"] = loras
        shots.append(shot)
    if not shots:
        raise ValueError("au moins un temps doit avoir une description d'image")
    size = [720, 1280] if b.get("hd") else [480, 832]
    job = {"name": name, "defaults": {"still_size": [720, 1280], "clip_size": size, "mode": "natural",
                                      "smooth": True, "grain": True, "seed": int(b.get("seed") or 1)},
           "shots": shots}
    jobs.mkdir(parents=True, exist_ok=True)
    path = jobs / f"{name}.yaml"
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"file": path.name, "shots": len(shots),
            "command": f"docker compose run --rm pilot run /data/jobs/{path.name}"}


LISTS = ("decor", "cadrage", "pose", "pose_perso", "tenue", "expression", "lumiere")
FORMATS = {"portrait": [864, 1152], "vertical": [720, 1280], "carre": [1024, 1024], "paysage": [1152, 864]}
SPLIT = re.compile(r"\s*(?:;|,?\s+puis\s+|,?\s+ensuite\s+)\s*", re.I)


class Studio:
    """Banc de test des prompts : listes, composition aleatoire, lancement du pilote, resultats."""

    def __init__(self, data: Path):
        self.data = data
        self.tests = data / "tests"
        self.repo = Path(os.environ.get("REPO_DIR", HERE.parents[1]))
        self.proc = None
        self.podfile = data / "studio_pod.json"
        self.lock = threading.Lock()
        threading.Thread(target=self._watch, daemon=True).start()

    # --- Pod garde en veille entre deux tests -------------------------------------------------
    # Le premier test cree le pod ; les suivants le reutilisent. Sans test pendant IDLE_S secondes,
    # il est supprime. Son nom commence par "girls-ai-" : le service girls-ai-pod-reaper du serveur
    # le supprime de toute facon s'il depasse l'age maximal (filet de securite).
    IDLE_S = int(os.environ.get("STUDIO_IDLE_S", "600"))

    def _rp(self):
        srv = str(self.repo / "server")
        if srv not in sys.path:
            sys.path.insert(0, srv)
        from pilot import runpod
        return runpod

    def pod(self):
        try:
            return json.loads(self.podfile.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            return None

    def pod_info(self):
        p = self.pod()
        if not p:
            return {"on": False}
        now = time.time()
        return {"on": True, "gpu": p.get("gpu"), "cost_per_hr": p.get("cost"), "minutes": round((now - p["created"]) / 60, 1),
                "cost_usd": round((now - p["created"]) / 3600 * (p.get("cost") or 0), 2),
                "idle_s": 0 if self.running() else int(now - p["last_used"]), "idle_max_s": self.IDLE_S}

    def _save_pod(self, p):
        self.podfile.write_text(json.dumps(p), encoding="utf-8")

    def ensure_pod(self):
        """Renvoie l'identifiant du pod de veille, en le creant s'il n'existe pas ou plus."""
        import yaml
        rp = self._rp()
        with self.lock:
            p = self.pod()
            if p and not any(x.get("id") == p["id"] for x in rp.list_pods()):
                p = None  # supprime entre-temps (delai, filet de securite, console RunPod)
            if not p:
                infra = yaml.safe_load((self.repo / "persona" / "production.yaml").read_text(encoding="utf-8"))["infra"]
                pid, cost, gpu = rp.create_pod(infra, f"girls-ai-studio-{int(time.time())}")
                p = {"id": pid, "cost": cost, "gpu": gpu, "created": time.time()}
            p["last_used"] = time.time()
            self._save_pod(p)
            return p["id"]

    def stop_pod(self):
        if self.running():
            raise ValueError("un test est en cours : attendre sa fin avant d'arreter le pod")
        with self.lock:
            p = self.pod()
            if p:
                try:
                    self._rp().delete_pod(p["id"])
                except Exception as e:  # deja supprime : rien a faire ; autre erreur : on garde la trace
                    if "404" not in str(e):
                        raise ValueError(f"suppression du pod refusee : {str(e)[:200]}")
                self.podfile.unlink(missing_ok=True)

    def _watch(self):
        while True:
            time.sleep(30)
            try:
                p = self.pod()
                if not p:
                    continue
                if self.running():
                    p["last_used"] = time.time()
                    self._save_pod(p)
                elif time.time() - p["last_used"] > self.IDLE_S:
                    self.stop_pod()
            except Exception:
                pass

    def lists(self):
        base = json.loads((HERE / "listes_test.json").read_text(encoding="utf-8"))
        perso = self._perso()
        return {k: [{"t": x, "perso": False} for x in base.get(k, [])] + [{"t": x, "perso": True} for x in perso.get(k, [])]
                for k in LISTS}

    def _perso(self):
        p = self.data / "listes_perso.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def edit_list(self, name, text, remove=False):
        if name not in LISTS:
            raise ValueError("liste inconnue")
        text = " ".join(str(text).split())
        if not text:
            raise ValueError("texte vide")
        perso = self._perso()
        cur = perso.setdefault(name, [])
        if remove:
            if text in cur:
                cur.remove(text)
        elif text not in cur:
            cur.append(text)
        self.data.mkdir(parents=True, exist_ok=True)
        (self.data / "listes_perso.json").write_text(json.dumps(perso, ensure_ascii=False, indent=2), encoding="utf-8")

    def loras(self):
        try:
            import yaml
        except ImportError:
            return []
        cat = {}
        prod = self.repo / "persona" / "production.yaml"
        if prod.exists():
            cat.update(yaml.safe_load(prod.read_text(encoding="utf-8")).get("lora_catalog") or {})
        extra = self.data / "lora_catalog.yaml"
        if extra.exists():
            cat.update(yaml.safe_load(extra.read_text(encoding="utf-8")) or {})
        return [{"name": k, "label": v.get("label", k), "strength": v.get("strength", 0.6), "trigger": v.get("trigger", "")}
                for k, v in cat.items()]

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def can_run(self):
        return bool(os.environ.get("RUNPOD_API_KEY")) and (self.repo / "server" / "pilot").exists()

    def compose(self, b, rng):
        """Une description : un element tire au hasard dans chaque liste cochee, plus les champs libres."""
        def pick(key):
            vals = [str(x) for x in (b.get(key) or []) if str(x).strip()]
            return rng.choice(vals) if vals else ""
        poses = [str(x) for x in (b.get("pose") or []) + (b.get("pose_perso") or []) if str(x).strip()]
        parts = [pick("cadrage"), rng.choice(poses) if poses else "", pick("expression"), pick("tenue"),
                 pick("decor"), pick("lumiere"), str(b.get("corps", "")).strip(), str(b.get("libre", "")).strip()]
        return ", ".join(x for x in parts if x)

    def start(self, b):
        import random
        if self.running():
            raise ValueError("un test est deja en cours : attendre sa fin")
        n = max(1, min(int(b.get("n") or 4), 40))
        seed = int(b.get("seed") or int(time.time()) % 100000)
        rng = random.Random(seed)
        tid = time.strftime("%Y%m%d_%H%M%S")
        loras = [{"name": str(x["name"]), "strength": float(x["strength"])} for x in (b.get("loras") or [])]
        prompts = [self.compose(b, rng) for _ in range(n)]
        if not any(prompts):
            raise ValueError("rien a generer : cocher au moins un element ou remplir un champ")
        job = {"name": f"test_{tid}", "defaults": {"still_size": FORMATS.get(b.get("format"), FORMATS["portrait"]), "seed": seed},
               "shots": [{"name": f"{i + 1:02d}", "still": p, "loras": loras, "tattoos": bool(b.get("tattoos", True))}
                         for i, p in enumerate(prompts)]}
        d = self.tests / tid
        d.mkdir(parents=True, exist_ok=True)
        jobp = d / "job.yaml"
        jobp.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        rec = {"id": tid, "date": time.strftime("%d/%m/%Y %H:%M"), "params": b, "prompts": prompts, "verdict": None, "note": ""}
        (d / "test.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        cmd = [sys.executable, "-m", "pilot", "run", str(jobp), "--stills-only", "--data", str(self.data), "--out", str(d)]
        if self.can_run():
            cmd += ["--pod-id", os.environ.get("STUDIO_POD_ID") or self.ensure_pod()]
            self.proc = subprocess.Popen(cmd, cwd=str(self.repo / "server"), stdout=open(d / "log.txt", "w"), stderr=subprocess.STDOUT)
            return {"id": tid, "started": True}
        return {"id": tid, "started": False,
                "command": f"docker compose run --rm pilot run /data/tests/{tid}/job.yaml --stills-only --out /data/tests/{tid}"}

    def _dir(self, tid):
        if not re.fullmatch(r"[0-9_]+", str(tid)):
            raise ValueError("identifiant invalide")
        d = self.tests / str(tid)
        if not d.is_dir():
            raise FileNotFoundError(tid)
        return d

    def list(self):
        out = []
        for d in sorted(self.tests.glob("*/test.json"), reverse=True):
            rec = json.loads(d.read_text(encoding="utf-8"))
            logp = d.parent / "log.txt"
            log = logp.read_text(encoding="utf-8", errors="replace") if logp.exists() else ""
            rec["images"] = sorted(x.name for x in d.parent.glob("*.png"))
            rec["status"] = ("termine" if "rapport :" in log else "arrete" if "ARRET" in log
                             else "en cours" if log and self.running() else "a lancer" if not log else "interrompu")
            rec["log"] = "\n".join(log.strip().splitlines()[-3:])
            out.append(rec)
        return out

    def verdict(self, tid, ok, note):
        p = self._dir(tid) / "test.json"
        rec = json.loads(p.read_text(encoding="utf-8"))
        rec["verdict"], rec["note"] = ok, str(note or "")[:500]
        p.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")

    def delete(self, tid):
        shutil.rmtree(self._dir(tid))


def make_handler(t: Triage, token: str):
    studio = Studio(t.root.parent)
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def authed(self, query):
            if not token:
                return True
            if query.get("t", [""])[0] == token:
                return True
            c = SimpleCookie(self.headers.get("Cookie", ""))
            return "t" in c and c["t"].value == token

        def send(self, code, body=b"", ctype="application/json", extra=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def js(self, obj, code=200):
            self.send(code, json.dumps(obj).encode())

        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if not self.authed(q):
                return self.send(403, b"forbidden", "text/plain")
            if u.path in ("/", "/tri", "/test"):
                extra = {"Set-Cookie": f"t={token}; HttpOnly; SameSite=Strict"} if token else None
                page = {"/": "home.html", "/tri": "index.html", "/test": "test.html"}[u.path]
                return self.send(200, (HERE / page).read_bytes(), "text/html; charset=utf-8", extra)
            if u.path == "/api/studio":
                return self.js({"lists": studio.lists(), "loras": studio.loras(), "can_run": studio.can_run(),
                                "running": studio.running(), "formats": list(FORMATS)})
            if u.path == "/api/tests":
                return self.js({"tests": studio.list(), "running": studio.running(), "pod": studio.pod_info()})
            if u.path.startswith("/tfile/"):
                try:
                    tid, _, name = unquote(u.path[7:]).partition("/")
                    return self.serve_file(t.safe(studio._dir(tid), name))
                except (FileNotFoundError, ValueError):
                    return self.send(404, b"not found", "text/plain")
            if u.path == "/nouveau":
                return self.send(200, (HERE / "form.html").read_bytes(), "text/html; charset=utf-8")
            if u.path == "/api/list":
                return self.js({"files": t.inbox(), "counts": t.counts(), "undo": len(t.history)})
            if u.path.startswith("/file/"):
                try:
                    return self.serve_file(t.safe(t.root, unquote(u.path[6:])))
                except FileNotFoundError:
                    return self.send(404, b"not found", "text/plain")
            self.send(404, b"not found", "text/plain")

        def serve_file(self, p: Path):
            size = p.stat().st_size
            ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            start, end, code = 0, size - 1, 200
            rng = self.headers.get("Range", "")
            if rng.startswith("bytes="):
                a, _, b = rng[6:].partition("-")
                try:
                    start = int(a) if a else max(0, size - int(b))
                    end = min(int(b), size - 1) if a and b else size - 1
                    code = 206
                except ValueError:
                    pass
                if start > end or start >= size:
                    return self.send(416, extra={"Content-Range": f"bytes */{size}"})
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            if code == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            with open(p, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(1 << 16, left))
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    left -= len(chunk)

        def do_POST(self):
            u = urlparse(self.path)
            if not self.authed(parse_qs(u.query)):
                return self.send(403, b"forbidden", "text/plain")
            n = int(self.headers.get("Content-Length", 0) or 0)
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
                if u.path == "/api/move":
                    t.move(str(body["name"]), str(body["to"]))
                    return self.js({"ok": True})
                if u.path == "/api/test":
                    return self.js({"ok": True, **studio.start(body)})
                if u.path == "/api/list":
                    studio.edit_list(body.get("liste"), body.get("texte"), bool(body.get("remove")))
                    return self.js({"ok": True})
                if u.path == "/api/test/verdict":
                    studio.verdict(body["id"], body.get("ok"), body.get("note"))
                    return self.js({"ok": True})
                if u.path == "/api/pod/stop":
                    studio.stop_pod()
                    return self.js({"ok": True})
                if u.path == "/api/test/delete":
                    studio.delete(body["id"])
                    return self.js({"ok": True})
                if u.path == "/api/job":
                    return self.js({"ok": True, **write_job(t.root.parent / "jobs", body)})
                if u.path == "/api/undo":
                    return self.js({"ok": True, "name": t.undo()})
            except (FileNotFoundError, ValueError, KeyError, RuntimeError) as e:
                return self.js({"ok": False, "error": str(e)}, 400)
            self.send(404, b"not found", "text/plain")

    return H


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True, help="dossier contenant les fichiers a trier")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--token", default=os.environ.get("TRIAGE_TOKEN", ""),
                    help="obligatoire si --host n'est pas local")
    a = ap.parse_args()
    if a.host not in ("127.0.0.1", "localhost") and not a.token:
        ap.error("--token requis quand l'interface est exposee sur le reseau")
    t = Triage(Path(a.dir))
    srv = ThreadingHTTPServer((a.host, a.port), make_handler(t, a.token))
    suffix = f"/?t={a.token}" if a.token else "/"
    print(f"Tri : http://{a.host}:{a.port}{suffix}  ({len(t.inbox())} fichiers a trier)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
