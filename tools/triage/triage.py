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
    shots = []
    for key, dest in (("accroche", "soft"), ("montee", "abonnes"), ("final", "payant")):
        still = str(b.get(f"{key}_still", "")).strip()
        if not still:
            continue
        shot = {"name": f"{len(shots) + 1}_{key}", "dest": dest,
                "still": ", ".join(x for x in (still, common) if x)}
        motion = str(b.get(f"{key}_motion", "")).strip()
        if motion:
            shot["motion"] = motion
        if not b.get(f"{key}_tattoos", True):
            shot["tattoos"] = False
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


def make_handler(t: Triage, token: str):
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
            if u.path == "/":
                extra = {"Set-Cookie": f"t={token}; HttpOnly; SameSite=Strict"} if token else None
                return self.send(200, PAGE, "text/html; charset=utf-8", extra)
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
                if u.path == "/api/job":
                    return self.js({"ok": True, **write_job(t.root.parent / "jobs", body)})
                if u.path == "/api/undo":
                    return self.js({"ok": True, "name": t.undo()})
            except (FileNotFoundError, ValueError, KeyError) as e:
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
