import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

from . import runpod, workflows
from .comfy import Comfy

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "girls-ai-"
MODELE = "2026-11-14"  # version du format des plans : la meme que dans server/jobs/modele.yaml
INTERP = "minterpolate=fps=32:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def to_mp4(webm: Path, mp4: Path, smooth: bool, grain: bool):
    ff = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    if not ff:
        raise RuntimeError("ffmpeg introuvable")
    vf = [INTERP] if smooth else []
    if grain:
        vf.append("noise=alls=5:allf=t,eq=saturation=0.92:contrast=0.97")
    cmd = [ff, "-y", "-loglevel", "error", "-i", str(webm)]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", str(mp4)]
    subprocess.run(cmd, check=True)


def concat(mp4s, out: Path):
    """Met bout a bout des clips de memes dimensions (sous-scenes d'une meme scene)."""
    ff = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    cmd = [ff, "-y", "-loglevel", "error"]
    for m in mp4s:
        cmd += ["-i", str(m)]
    n = len(mp4s)
    cmd += ["-filter_complex", "".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]", "-map", "[v]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)


def load_config(a):
    """production.yaml + catalogue de LoRA du dossier de donnees (lora_catalog.yaml, ecrit par
    "pilot lora add" : il vit hors du depot pour ne pas creer de conflit au git pull)."""
    cfg = yaml.safe_load(open(a.config, encoding="utf-8"))
    extra = Path(getattr(a, "data", None) or os.environ.get("DATA_DIR", str(ROOT / "server" / "data"))) / "lora_catalog.yaml"
    cat = dict(cfg.get("lora_catalog") or {})
    if extra.exists():
        cat.update(yaml.safe_load(extra.read_text(encoding="utf-8")) or {})
    cfg["lora_catalog"] = cat
    return cfg


def resolve_loras(cfg, wanted):
    """LoRA supplementaires d'un plan. `wanted` absent : None (on garde extra_loras_still).
    Sinon une liste dont chaque element est un nom du catalogue (lora_catalog de production.yaml),
    ou {name: nom_du_catalogue_ou_fichier, strength: 0.8} pour changer la force."""
    if wanted is None:
        return None
    cat = cfg.get("lora_catalog") or {}
    out = []
    for w in wanted:
        w = {"name": w} if isinstance(w, str) else dict(w)
        ref = cat.get(w["name"], {})
        out.append({"name": ref.get("file", w["name"]), "strength": float(w.get("strength", ref.get("strength", 1.0))),
                    "trigger": ref.get("trigger", "")})
    return out


def cmd_run(a):
    cfg = load_config(a)
    job = yaml.safe_load(open(a.job, encoding="utf-8"))
    # "character" dans le fichier de plans : reglages d'un autre personnage (atelier), poses sur ceux
    # de production.yaml. Un champ absent garde la valeur de production.yaml.
    infra, models, char = cfg["infra"], cfg["models"], {**cfg["character"], **(job.get("character") or {})}
    d = {**{"still_size": [720, 1280], "clip_size": [480, 832], "mode": "natural", "smooth": True, "grain": True,
            "seed": 1}, **job.get("defaults", {})}
    data = Path(a.data)
    work = data / "work" / job["name"]
    inbox = Path(a.out) if getattr(a, "out", None) else data / "inbox"
    work.mkdir(parents=True, exist_ok=True)
    inbox.mkdir(parents=True, exist_ok=True)
    max_min = infra.get("max_session_min", 90)
    t0 = time.time()
    pod_id, own = a.pod_id, False
    report = {"job": job["name"], "shots": []}
    if str(job.get("modele", MODELE)) != MODELE:
        log(f"ATTENTION : plan ecrit d'apres le modele {job['modele']}, modele en cours {MODELE} (server/jobs/modele.yaml)")
    try:
        if not pod_id:
            # Clips a calculer : carte rapide en premier ; images seules : carte la moins chere.
            video = not a.stills_only and any(sh.get("motion") or sh.get("steps") for sh in job["shots"])
            if video and infra.get("gpu_types_video"):
                infra = {**infra, "gpu_types": infra["gpu_types_video"]}
            pod_id, cost, gpu = runpod.create_pod(infra, f"{PREFIX}{job['name']}-{int(t0)}")
            own = True
            report.update(gpu=gpu, cost_per_hr=cost)
            log(f"pod {pod_id} cree ({gpu}, {cost} $/h)")
        c = Comfy(pod_id)
        c.wait_ready()
        log("ComfyUI pret")
        lora_key = "lora_still_zimage" if cfg.get("image_model", "wan") == "zimage" else "lora_still"
        if char.get(lora_key) and not c.has_model("loras", char[lora_key]):
            raise RuntimeError(f"LoRA introuvable sur le volume : {char[lora_key]}")
        for sh in job["shots"]:  # verifier les LoRA supplementaires avant de calculer quoi que ce soit
            for lo in resolve_loras(cfg, {**d, **sh}.get("loras")) or []:
                if not c.has_model("loras", lo["name"]):
                    raise RuntimeError(f"LoRA introuvable sur le volume : {lo['name']}")
        # Deux passes : toutes les images, puis tous les clips. Evite de recharger les modeles
        # (image <-> animation) a chaque plan, ce qui coutait plus d'une minute par plan.
        shots = []
        for i, shot in enumerate(job["shots"]):
            s = {**d, **shot}
            # same_seed : meme tirage pour tous les plans (comparaison de LoRA ou de forces).
            seed = int(s["seed"]) + (0 if s.get("same_seed") else i)
            shots.append((s, f"{job['name']}_{s['name']}", seed, {"name": s["name"]}))
        report["shots"] = [e for _, _, _, e in shots]
        stills = {}

        def over():
            if (time.time() - t0) / 60 > max_min:
                log("duree maximale atteinte, arret")
                return True
            return False

        for s, name, seed, entry in shots:
            if over():
                entry.setdefault("error", "non traite : duree maximale atteinte")
                continue
            try:
                t = time.time()
                if s.get("image"):  # image deja produite et choisie (atelier) : pas de nouveau tirage
                    src = Path(s["image"])
                    stills[name] = (src if src.is_absolute() else data / src).read_bytes()
                    (work / f"{name}.png").write_bytes(stills[name])
                    continue
                if cfg.get("image_model", "wan") == "zimage":
                    # tattoos: false dans un plan = tenue couvrante ; sans cela le modele dessine
                    # les tatouages par-dessus ou les double.
                    tat = char.get("zimage_tattoos", "") if s.get("tattoos", True) else ""
                    # Description fixe du corps, redigee par le proprietaire : ajoutee aux plans dont
                    # la destination figure dans zimage_body_dests (ou qui portent body: true).
                    use_body = s.get("body", s.get("dest") in (char.get("zimage_body_dests") or []))
                    body = char.get("zimage_body", "") if use_body else ""
                    prompt = f"{char.get('zimage_prefix', char['prefix'])}{tat}{body}{s['still']}{char.get('zimage_suffix', '')}"
                    extra = resolve_loras(cfg, s.get("loras"))
                    trig = ", ".join(x["trigger"] for x in extra or [] if x.get("trigger"))
                    if trig:  # mots declencheurs des LoRA supplementaires
                        prompt = f"{prompt} {trig}"
                    graph = workflows.still_zimage(models, char, prompt, *s["still_size"], seed, f"ga_{name}", loras=extra,
                                                   char_strength=s.get("char_strength"))
                else:
                    prompt = f"{char['prefix']}{s['still']}{char.get('still_suffix', '')}"
                    graph = workflows.still(models, char, prompt, *s["still_size"], seed, f"ga_{name}")
                files = c.run(graph)
                stills[name] = c.fetch(files[0])
                (work / f"{name}.png").write_bytes(stills[name])
                entry["still_s"] = round(time.time() - t)
                log(f"{name} : image ({entry['still_s']} s)")
                if a.stills_only:
                    shutil.copy(work / f"{name}.png", inbox / f"{name}.png")
            except Exception as e:  # un plan rate n'arrete pas la session
                entry["error"] = str(e)[:300]
                log(f"{name} : ECHEC image {entry['error']}")
        # Passe intermediaire : images de fin. Un plan peut porter "steps" (liste d'etapes : la scene
        # est decoupee en sous-scenes enchainees) ou "end_edit" + "motion" (une seule etape).
        # Chaque etape : l'image de fin est fabriquee par edition de l'image precedente, puis un clip
        # debut/fin relie les deux. L'image de fin d'une etape est l'image de depart de la suivante.
        keep = ("Keep exactly the same person, same face, same hair, same body, same clothes unless stated otherwise, "
                "same room, same light, same camera position, same framing, same distance to the camera and same photo style. "
                "Change only this: ")

        def steps_of(s):
            if s.get("steps"):
                return [{"end": st, "motion": st} if isinstance(st, str) else st for st in s["steps"]]
            if s.get("end_edit") and s.get("motion"):
                return [{"end": s["end_edit"], "motion": s["motion"]}]
            return []

        chains = {}
        for s, name, seed, entry in shots:
            if name not in stills or not steps_of(s):
                continue
            imgs = [stills[name]]
            try:
                for k, st in enumerate(steps_of(s), 1):
                    if over():
                        raise RuntimeError("duree maximale atteinte")
                    t = time.time()
                    up = c.upload(f"ga_{name}_e{k - 1}.png", imgs[-1])
                    files = c.run(workflows.edit_image(models, up, keep + st["end"], *s["still_size"], seed + k, f"ga_{name}_e{k}"))
                    imgs.append(c.fetch(files[0]))
                    (work / f"{name}_e{k}.png").write_bytes(imgs[-1])
                    log(f"{name} : image de fin {k} ({round(time.time() - t)} s)")
                    if a.stills_only:
                        shutil.copy(work / f"{name}_e{k}.png", inbox / f"{name}_e{k}.png")
                chains[name] = imgs
            except Exception as e:
                entry["error"] = str(e)[:300]
                log(f"{name} : ECHEC image de fin {entry['error']}")
        for s, name, seed, entry in shots:
            if a.stills_only or name not in stills:
                continue
            steps = steps_of(s)
            if steps and name not in chains:
                continue  # une image de fin a echoue : pas de clip plutot qu'un clip sans fin imposee
            if not steps and not s.get("motion"):
                continue
            if over():
                entry.setdefault("error", "clip non traite : duree maximale atteinte")
                continue
            try:
                t = time.time()
                suffix = char.get("motion_suffix", "")
                parts = []
                if steps:
                    for k, st in enumerate(steps, 1):
                        up = c.upload(f"ga_{name}_e{k - 1}.png", chains[name][k - 1])
                        end = c.upload(f"ga_{name}_e{k}.png", chains[name][k])
                        files = c.run(workflows.clip(models, char, up, st["motion"] + suffix, *s["clip_size"], seed + k,
                                                     f"ga_{name}_p{k}", mode=s["mode"], end_image_name=end))
                        webm = work / f"{name}_p{k}.webm"
                        webm.write_bytes(c.fetch(files[0]))
                        parts.append(webm)
                        log(f"{name} : sous-scene {k}/{len(steps)}")
                else:
                    up = c.upload(f"ga_{name}.png", stills[name])
                    files = c.run(workflows.clip(models, char, up, s["motion"] + suffix, *s["clip_size"], seed,
                                                 f"ga_{name}", mode=s["mode"]))
                    webm = work / f"{name}.webm"
                    webm.write_bytes(c.fetch(files[0]))
                    parts.append(webm)
                entry["clip_s"] = round(time.time() - t)
                if len(parts) == 1:
                    to_mp4(parts[0], inbox / f"{name}.mp4", s["smooth"], s["grain"])
                else:  # sous-scenes : chaque partie est convertie puis les parties sont mises bout a bout
                    mp4s = []
                    for pth in parts:
                        to_mp4(pth, pth.with_suffix(".mp4"), s["smooth"], s["grain"])
                        mp4s.append(pth.with_suffix(".mp4"))
                    concat(mp4s, inbox / f"{name}.mp4")
                log(f"{name} : clip ({entry['clip_s']} s) -> {inbox.name}")
            except Exception as e:
                entry["error"] = str(e)[:300]
                log(f"{name} : ECHEC clip {entry['error']}")
    finally:
        if own and pod_id and not a.keep_pod:
            try:
                runpod.delete_pod(pod_id)
                log(f"pod {pod_id} supprime")
            except Exception as e:
                log(f"ATTENTION : suppression du pod {pod_id} echouee : {e}")
        report["minutes"] = round((time.time() - t0) / 60, 1)
        if report.get("cost_per_hr"):
            report["cost_usd"] = round(report["minutes"] / 60 * report["cost_per_hr"], 2)
        (work / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        log(f"rapport : {json.dumps(report, ensure_ascii=False)}")
    return 1 if any("error" in s for s in report["shots"]) or not report["shots"] else 0


def cmd_reap(a):
    cfg = yaml.safe_load(open(a.config, encoding="utf-8"))
    killed = runpod.reap(PREFIX, a.max_age_min or cfg["infra"].get("max_session_min", 90) + 15)
    log(f"pods supprimes : {killed or 'aucun'}")


def cmd_depenses(a):
    cfg = yaml.safe_load(open(a.config, encoding="utf-8"))
    print(f"depense GPU du jour : {runpod.spent_today()} $ sur un plafond de {runpod.daily_cap(cfg['infra'])} $")


def cmd_pods(a):
    for p in runpod.list_pods():
        print(p["id"], p.get("name"), p.get("desiredStatus"), p.get("costPerHr"), p.get("createdAt"))


def cmd_lora(a):
    """lora add : telecharge un LoRA de Civitai, le depose sur le volume et l'inscrit au catalogue.
    lora list : affiche le catalogue."""
    import re
    from .http import multipart, request
    data = Path(a.data)
    catp = data / "lora_catalog.yaml"
    cat = (yaml.safe_load(catp.read_text(encoding="utf-8")) or {}) if catp.exists() else {}
    if a.action == "list":
        for k, v in {**(yaml.safe_load(open(a.config, encoding="utf-8")).get("lora_catalog") or {}), **cat}.items():
            print(f"{v.get('label', k)}\n    nom court : {k} | fichier : {v.get('file')} | force {v.get('strength', 1.0)} | {v.get('base', '')} {v.get('trigger', '')}")
        return 0
    if a.action == "remove":
        if cat.pop(a.ref, None) is None:
            raise RuntimeError(f"{a.ref} n'est pas dans le catalogue")
        catp.write_text(yaml.safe_dump(cat, allow_unicode=True, sort_keys=False), encoding="utf-8")
        log(f"{a.ref} retire du catalogue (le fichier reste sur le volume)")
        return 0
    if a.name and not re.fullmatch(r"[a-z0-9_]+", a.name):
        raise RuntimeError("--name : lettres minuscules, chiffres, tirets bas")
    tok = os.environ.get("CIVITAI_TOKEN", "")
    hdr = {"Authorization": f"Bearer {tok}"} if tok else {}
    m = re.search(r"models/(\d+)", a.ref) or re.fullmatch(r"(\d+)", a.ref)
    ver = re.search(r"modelVersionId=(\d+)", a.ref)
    if not m and ver:  # seulement un numero de version : retrouver le modele
        mid = request("GET", f"https://civitai.com/api/v1/model-versions/{ver.group(1)}", headers=hdr).get("modelId")
        m = re.fullmatch(r"(\d+)", str(mid))
    if not m:
        raise RuntimeError("reference attendue : adresse civitai.com/models/<numero>, numero du modele, ou modelVersionId=<numero>")
    info = request("GET", f"https://civitai.com/api/v1/models/{m.group(1)}", headers=hdr)
    versions = info.get("modelVersions") or []
    v = next((x for x in versions if ver and str(x["id"]) == ver.group(1)), versions[0] if versions else None)
    if not v:
        raise RuntimeError("aucune version trouvee pour ce modele")
    f = next((x for x in v.get("files", []) if x["name"].endswith(".safetensors")), None)
    problems = []
    if info.get("type") != "LORA":
        problems.append(f"ce n'est pas un LoRA (type {info.get('type')})")
    if "zimage" not in re.sub(r"[^a-z]", "", (v.get("baseModel") or "").lower()):
        problems.append(f"modele de base {v.get('baseModel')!r} : il faut Z-Image ou Z-Image Turbo")
    if not f:
        problems.append("pas de fichier .safetensors")
    if "Image" not in (info.get("allowCommercialUse") or []):
        problems.append(f"licence : usage commercial des images non autorise ({info.get('allowCommercialUse')})")
    log(f"{info.get('name')} / {v.get('name')} / base {v.get('baseModel')} / mots declencheurs {v.get('trainedWords')}")
    if problems and not a.force:
        raise RuntimeError("refuse : " + " ; ".join(problems) + " (--force pour passer outre)")
    for pb in problems:
        log(f"ATTENTION : {pb}")
    label = f"{info.get('name')} ({v.get('name')})"
    if not a.name:  # sans --name : nom court tire du nom du LoRA sur Civitai
        a.name = re.sub(r"[^a-z0-9]+", "_", f"{info.get('name')} {v.get('name')}".lower()).strip("_")[:48].strip("_")
    blob = request("GET", f["downloadUrl"], headers=hdr, raw=True, timeout=900)
    if len(blob) < 100000:
        raise RuntimeError("telechargement refuse par Civitai : definir CIVITAI_TOKEN dans server/.env")
    fname = f"{a.name}.safetensors"
    cfg = load_config(a)
    pod_id, own = a.pod_id, False
    jtok = a.jupyter_token or os.environ.get("JUPYTER_TOKEN", "")
    try:
        if not pod_id:
            import secrets
            jtok = secrets.token_urlsafe(24)
            pod_id, cost, gpu = runpod.create_pod(cfg["infra"], f"{PREFIX}lora-{int(time.time())}", env={"JUPYTER_PASSWORD": jtok})
            own = True
            log(f"pod {pod_id} cree ({gpu}, {cost} $/h)")
        elif not jtok:
            raise RuntimeError("avec --pod-id, donner aussi --jupyter-token (mot de passe Jupyter du pod)")
        c = Comfy(pod_id)
        c.wait_ready()
        # Depot par l'API de fichiers de Jupyter, en morceaux : le proxy RunPod coupe les envois de
        # plus de 100 Mo. Le dossier racine de Jupyter est /workspace (le volume).
        import base64
        url = f"https://{pod_id}-8888.proxy.runpod.net/api/contents/runpod-slim/ComfyUI/models/loras/{fname}"
        size = 20 * 1024 * 1024
        chunks = [blob[i:i + size] for i in range(0, len(blob), size)]
        for i, ch in enumerate(chunks, 1):
            request("PUT", url, headers={"Authorization": f"token {jtok}"}, timeout=600, data={
                "type": "file", "format": "base64", "name": fname, "chunk": -1 if i == len(chunks) else i,
                "content": base64.b64encode(ch).decode()})
            log(f"depot {i}/{len(chunks)}")
        seen = False
        for _ in range(6):  # la liste de ComfyUI peut mettre un moment a voir un fichier neuf
            if c.has_model("loras", fname):
                seen = True
                break
            time.sleep(10)
        if not seen:
            log("fichier depose sur le volume ; ComfyUI ne le liste pas encore, il le verra au prochain demarrage de pod")
    finally:
        if own and pod_id:
            runpod.delete_pod(pod_id)
            log(f"pod {pod_id} supprime")
    cat[a.name] = {"label": label, "file": fname, "strength": a.strength, "base": v.get("baseModel"),
                   "trigger": ", ".join(v.get("trainedWords") or []), "source": f"https://civitai.com/models/{m.group(1)}?modelVersionId={v['id']}"}
    data.mkdir(parents=True, exist_ok=True)
    catp.write_text(yaml.safe_dump(cat, allow_unicode=True, sort_keys=False), encoding="utf-8")
    log(f"{a.name} inscrit au catalogue ({len(blob) // 1000000} Mo, force par defaut {a.strength})")
    return 0


def main():
    ap = argparse.ArgumentParser(prog="pilot", description=__doc__)
    ap.add_argument("--config", default=str(ROOT / "persona" / "production.yaml"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="execute un fichier de plans")
    r.add_argument("job")
    r.add_argument("--data", default=os.environ.get("DATA_DIR", str(ROOT / "server" / "data")))
    r.add_argument("--pod-id", help="reutilise un pod existant (ni cree ni supprime)")
    r.add_argument("--keep-pod", action="store_true")
    r.add_argument("--stills-only", action="store_true")
    r.add_argument("--out", help="dossier de sortie a la place de la boite de tri")
    r.set_defaults(fn=cmd_run)
    k = sub.add_parser("reap", help="supprime les pods du projet trop anciens")
    k.add_argument("--max-age-min", type=int)
    k.set_defaults(fn=cmd_reap)
    sub.add_parser("pods", help="liste les pods du compte").set_defaults(fn=cmd_pods)
    sub.add_parser("depenses", help="depense GPU du jour et plafond").set_defaults(fn=cmd_depenses)
    lo = sub.add_parser("lora", help="LoRA supplementaires : add <adresse Civitai> --name nom | list | remove <nom>")
    lo.add_argument("action", choices=["add", "list", "remove"])
    lo.add_argument("ref", nargs="?", default="")
    lo.add_argument("--name")
    lo.add_argument("--strength", type=float, default=0.6)
    lo.add_argument("--force", action="store_true", help="accepter malgre une alerte (base, licence)")
    lo.add_argument("--pod-id")
    lo.add_argument("--jupyter-token")
    lo.add_argument("--data", default=os.environ.get("DATA_DIR", str(ROOT / "server" / "data")))
    lo.set_defaults(fn=cmd_lora)
    a = ap.parse_args()
    try:
        sys.exit(a.fn(a) or 0)
    except RuntimeError as e:  # erreur attendue (pas de machine, cle refusee...) : message court
        log(f"ARRET : {str(e)[:400]}")
        sys.exit(2)


if __name__ == "__main__":
    main()
