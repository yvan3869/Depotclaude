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


def cmd_run(a):
    cfg = yaml.safe_load(open(a.config, encoding="utf-8"))
    job = yaml.safe_load(open(a.job, encoding="utf-8"))
    infra, models, char = cfg["infra"], cfg["models"], cfg["character"]
    d = {**{"still_size": [720, 1280], "clip_size": [480, 832], "mode": "natural", "smooth": True, "grain": True,
            "seed": 1}, **job.get("defaults", {})}
    data = Path(a.data)
    work = data / "work" / job["name"]
    inbox = data / "inbox"
    work.mkdir(parents=True, exist_ok=True)
    inbox.mkdir(parents=True, exist_ok=True)
    max_min = infra.get("max_session_min", 90)
    t0 = time.time()
    pod_id, own = a.pod_id, False
    report = {"job": job["name"], "shots": []}
    try:
        if not pod_id:
            pod_id, cost, gpu = runpod.create_pod(infra, f"{PREFIX}{job['name']}-{int(t0)}")
            own = True
            report.update(gpu=gpu, cost_per_hr=cost)
            log(f"pod {pod_id} cree ({gpu}, {cost} $/h)")
        c = Comfy(pod_id)
        c.wait_ready()
        log("ComfyUI pret")
        if not c.has_model("loras", char["lora_still"]):
            raise RuntimeError(f"LoRA introuvable sur le volume : {char['lora_still']}")
        # Deux passes : toutes les images, puis tous les clips. Evite de recharger les modeles
        # (image <-> animation) a chaque plan, ce qui coutait plus d'une minute par plan.
        shots = []
        for i, shot in enumerate(job["shots"]):
            s = {**d, **shot}
            shots.append((s, f"{job['name']}_{s['name']}", int(s["seed"]) + i, {"name": s["name"]}))
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
                prompt = f"{char['prefix']}{s['still']}{char.get('still_suffix', '')}"
                files = c.run(workflows.still(models, char, prompt, *s["still_size"], seed, f"ga_{name}"))
                stills[name] = c.fetch(files[0])
                (work / f"{name}.png").write_bytes(stills[name])
                entry["still_s"] = round(time.time() - t)
                log(f"{name} : image ({entry['still_s']} s)")
                if a.stills_only:
                    shutil.copy(work / f"{name}.png", inbox / f"{name}.png")
            except Exception as e:  # un plan rate n'arrete pas la session
                entry["error"] = str(e)[:300]
                log(f"{name} : ECHEC image {entry['error']}")
        for s, name, seed, entry in shots:
            if a.stills_only or name not in stills or not s.get("motion"):
                continue
            if over():
                entry.setdefault("error", "clip non traite : duree maximale atteinte")
                continue
            try:
                t = time.time()
                up = c.upload(f"ga_{name}.png", stills[name])
                files = c.run(workflows.clip(models, char, up, s["motion"] + char.get("motion_suffix", ""),
                                             *s["clip_size"], seed, f"ga_{name}", mode=s["mode"]))
                webm = work / f"{name}.webm"
                webm.write_bytes(c.fetch(files[0]))
                entry["clip_s"] = round(time.time() - t)
                to_mp4(webm, inbox / f"{name}.mp4", s["smooth"], s["grain"])
                log(f"{name} : clip ({entry['clip_s']} s) -> inbox")
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


def cmd_pods(a):
    for p in runpod.list_pods():
        print(p["id"], p.get("name"), p.get("desiredStatus"), p.get("costPerHr"), p.get("createdAt"))


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
    r.set_defaults(fn=cmd_run)
    k = sub.add_parser("reap", help="supprime les pods du projet trop anciens")
    k.add_argument("--max-age-min", type=int)
    k.set_defaults(fn=cmd_reap)
    sub.add_parser("pods", help="liste les pods du compte").set_defaults(fn=cmd_pods)
    a = ap.parse_args()
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
