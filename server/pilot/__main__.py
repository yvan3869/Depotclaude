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
MODELE = "2026-11-15f"  # version du format des plans : la meme que dans server/jobs/modele.yaml
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


def last_frame(video: Path, png: Path):
    """Derniere image d'un clip : image de depart du plan qui le prolonge ("suite_de")."""
    ff = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    subprocess.run([ff, "-y", "-loglevel", "error", "-sseof", "-1", "-i", str(video), "-update", "1", str(png)], check=True)
    return png.read_bytes()


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
                    "trigger": ref.get("trigger", ""), "low": ref.get("file_low", ""), "video": ref.get("famille") == "wan22"})
    return out


def loras_image(l):
    """LoRA d'image d'un plan (None : le plan ne dit rien, on garde extra_loras_still)."""
    return None if l is None else [x for x in l if not x["video"]]


def loras_video(l):
    """LoRA video d'un plan : celles que le catalogue range dans la famille Wan 2.2. Elles s'appliquent au clip."""
    return [x for x in l or [] if x["video"]]


def inventaire(c, data):
    """Note les LoRA presentes sur le volume dans data/lora_volume.json : la bibliotheque de l'atelier s'en sert pour
    signaler une LoRA absente avant de lancer un calcul. Rend la liste ; un echec d'ecriture n'arrete rien."""
    fichiers = sorted(c.models("loras"))
    try:
        (Path(data) / "lora_volume.json").write_text(json.dumps({"date": time.strftime("%d/%m/%Y %H:%M"), "fichiers": fichiers}), encoding="utf-8")
    except OSError as e:
        log(f"inventaire des LoRA non ecrit : {e}")
    return fichiers


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
        volume = inventaire(c, data)
        if char.get(lora_key) and char[lora_key] not in volume:
            raise RuntimeError(f"LoRA introuvable sur le volume : {char[lora_key]}")
        for sh in job["shots"]:  # verifier les LoRA supplementaires avant de calculer quoi que ce soit
            for lo in [x for y in resolve_loras(cfg, {**d, **sh}.get("loras")) or [] for x in (y, {"name": y["low"]} if y["low"] else None) if x]:
                if lo["name"] not in volume:
                    raise RuntimeError(f"LoRA introuvable sur le volume : {lo['name']}")
        # Deux passes : toutes les images, puis tous les clips. Evite de recharger les modeles
        # (image <-> animation) a chaque plan, ce qui coutait plus d'une minute par plan.
        shots = []
        for i, shot in enumerate(job["shots"]):
            s = {**d, **shot}
            # same_seed : meme tirage pour tous les plans (comparaison de LoRA ou de forces).
            seed = int(s["seed"]) + (0 if s.get("same_seed") else i)
            # "sortie" : nom du fichier produit, quand le plan vient d'une serie (plusieurs variantes regroupees)
            shots.append((s, s.get("sortie") or f"{job['name']}_{s['name']}", seed, {"name": s["name"]}))
        report["shots"] = [e for _, _, _, e in shots]
        stills, fins = {}, {}
        keep_ref = ("Keep exactly the same person, same face, same hair, same body, same tattoos, same clothes, same room, same furniture, "
                    "same light and same photo style. New photo of her in the same place, a moment later: ")
        # "tenue_libre" : la tenue n'est pas gardee, elle est celle que decrit le plan (elle se defait d'un plan a l'autre)
        keep_ref_libre = keep_ref.replace("same clothes, ", "").replace("New photo", "Her clothing is what the description below says "
                                                                         "and may differ from the image. New photo")

        def over():
            if (time.time() - t0) / 60 > max_min:
                log("duree maximale atteinte, arret")
                return True
            return False

        # Images creees d'abord, images tirees d'une autre par retouche ensuite : un seul changement de modele
        # (creation <-> retouche) au lieu d'un par plan, qui coutait une minute a chaque fois.
        for s, name, seed, entry in sorted(shots, key=lambda x: bool(x[0].get("image") and x[0].get("edit"))):
            if over():
                entry.setdefault("error", "non traite : duree maximale atteinte")
                continue
            try:
                t = time.time()
                if s.get("suite_de"):  # image de depart = derniere image du clip d'un plan precedent : passe des clips
                    continue
                if s.get("image"):  # image deja produite et choisie (atelier) : pas de nouveau tirage
                    src = Path(s["image"])
                    stills[name] = (src if src.is_absolute() else data / src).read_bytes()
                    if s.get("edit"):  # nouvelle image tiree de celle-ci par retouche : meme personne, meme lieu, meme tenue
                        up = c.upload(f"ga_{name}_ref.png", stills[name])
                        files = c.run(workflows.edit_image(models, up, (keep_ref_libre if s.get("tenue_libre") else keep_ref) + s["edit"], *s["still_size"], seed, f"ga_{name}"))
                        stills[name] = c.fetch(files[0])
                        entry["still_s"] = round(time.time() - t)
                        log(f"{name} : image par retouche ({entry['still_s']} s)")
                    (work / f"{name}.png").write_bytes(stills[name])
                    if s.get("edit") and a.stills_only:
                        shutil.copy(work / f"{name}.png", inbox / f"{name}.png")
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
                    extra = loras_image(resolve_loras(cfg, s.get("loras")))
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

        def ends_of(s, name, seed):
            imgs = [stills[name]]
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
            return imgs

        chains = {}
        for s, name, seed, entry in shots:
            if name not in stills or not steps_of(s):
                continue
            try:
                chains[name] = ends_of(s, name, seed)
            except Exception as e:
                entry["error"] = str(e)[:300]
                log(f"{name} : ECHEC image de fin {entry['error']}")
        for s, name, seed, entry in shots:
            if a.stills_only or (name not in stills and not s.get("suite_de")):
                continue
            steps = steps_of(s)
            if steps and name not in chains and not s.get("suite_de"):
                continue  # une image de fin a echoue : pas de clip plutot qu'un clip sans fin imposee
            if not steps and not s.get("motion"):
                continue
            if over():
                entry.setdefault("error", "clip non traite : duree maximale atteinte")
                continue
            try:
                t = time.time()
                if s.get("suite_de"):  # plan continu : il part de la derniere image du clip du plan nomme
                    src = f"{job['name']}_{s['suite_de']}"
                    if src not in fins:
                        raise RuntimeError(f"suite_de : le clip du plan {s['suite_de']} manque (il doit etre place avant et reussir)")
                    stills[name] = fins[src]
                    (work / f"{name}.png").write_bytes(stills[name])
                    shutil.copy(work / f"{name}.png", inbox / f"{name}.png")
                    if steps:
                        chains[name] = ends_of(s, name, seed)
                suffix = char.get("motion_suffix", "")
                vlo = loras_video(resolve_loras(cfg, s.get("loras")))  # LoRA video du plan, avec leurs mots declencheurs
                suffix += "".join(f" {x['trigger']}" for x in vlo if x.get("trigger"))
                parts = []
                if steps:
                    for k, st in enumerate(steps, 1):
                        up = c.upload(f"ga_{name}_e{k - 1}.png", chains[name][k - 1])
                        end = c.upload(f"ga_{name}_e{k}.png", chains[name][k])
                        files = c.run(workflows.clip(models, char, up, st["motion"] + suffix, *s["clip_size"], seed + k,
                                                     f"ga_{name}_p{k}", mode=s["mode"], end_image_name=end, loras=vlo))
                        webm = work / f"{name}_p{k}.webm"
                        webm.write_bytes(c.fetch(files[0]))
                        parts.append(webm)
                        log(f"{name} : sous-scene {k}/{len(steps)}")
                else:
                    up = c.upload(f"ga_{name}.png", stills[name])
                    end = None
                    if s.get("end_image"):  # clip debut/fin vers une image existante (celle du plan suivant)
                        src = Path(s["end_image"])
                        end = c.upload(f"ga_{name}_end.png", (src if src.is_absolute() else data / src).read_bytes())
                    files = c.run(workflows.clip(models, char, up, s["motion"] + suffix, *s["clip_size"], seed,
                                                 f"ga_{name}", mode=s["mode"], end_image_name=end, loras=vlo))
                    webm = work / f"{name}.webm"
                    webm.write_bytes(c.fetch(files[0]))
                    parts.append(webm)
                fins[name] = last_frame(parts[-1], work / f"{name}_fin.png")
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


def deposer(pod_id, jtok, fname, blob, dossier="loras"):
    """Depose un fichier dans un dossier de modeles du volume (les LoRA par defaut) par l'API de fichiers de Jupyter, en
    morceaux : le proxy RunPod coupe les envois de plus de 100 Mo. Le dossier racine de Jupyter est /workspace (le
    volume). `blob` : des octets, ou le chemin d'un fichier local, lu morceau par morceau (gros modeles)."""
    import base64
    from .http import request
    url = f"https://{pod_id}-8888.proxy.runpod.net/api/contents/runpod-slim/ComfyUI/models/{dossier}/{fname}"
    size = 20 * 1024 * 1024
    total = blob.stat().st_size if isinstance(blob, Path) else len(blob)
    n = max(1, -(-total // size))
    src = blob.open("rb") if isinstance(blob, Path) else None
    try:
        for i in range(1, n + 1):
            ch = src.read(size) if src else blob[(i - 1) * size:i * size]
            request("PUT", url, headers={"Authorization": f"token {jtok}"}, timeout=600, data={
                "type": "file", "format": "base64", "name": fname, "chunk": -1 if i == n else i,
                "content": base64.b64encode(ch).decode()})
            if n < 20 or i % 10 == 0 or i == n:
                log(f"depot de {fname} : {i}/{n}")
    finally:
        if src:
            src.close()


# Modeles du son, deposes sur le volume au premier usage. Stable Audio Open 1.0 : licence Stability AI Community
# (usage commercial gratuit sous 1 M$ de chiffre d'affaires annuel) ; t5-base : Apache 2.0.
SON = {("checkpoints", "stable-audio-open-1.0.safetensors"): "https://huggingface.co/Comfy-Org/stable-audio-open-1.0/resolve/main/stable-audio-open-1.0.safetensors",
       ("text_encoders", "t5-base.safetensors"): "https://huggingface.co/google-t5/t5-base/resolve/main/model.safetensors"}
SON_NEG = "music, melody, speech, voice, talking, singing, distortion, low quality"
SON_NEG_BRUIT = "music, melody, speech, voice, talking, singing, room tone, background noise, reverb, echo, low quality"


def telecharger(url, dest: Path):
    """Telecharge un gros fichier sur le disque, sans le garder en memoire."""
    import urllib.request
    from .http import UA, _ctx
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120, context=_ctx) as r, dest.open("wb") as f:
        shutil.copyfileobj(r, f, 4 * 1024 * 1024)
    return dest


def cmd_son(a):
    """son "<phrase en anglais>" --nom ambiance : fabrique une ou plusieurs ambiances sonores et les range dans
    data/audio/, ou le montage de l'atelier les propose (reglage « Musique »). Un pod pour tout le lot."""
    import re
    import secrets
    data = Path(a.data)
    nom = re.sub(r"[^a-z0-9_]+", "_", (a.nom or "ambiance").lower()).strip("_") or "ambiance"
    if a.lot:  # lot ecrit par l'atelier : [{"texte", "sortie" (dans data/audio), "duree", "bruit", "seed"}]
        lot = json.loads(Path(a.lot).read_text(encoding="utf-8"))
        for x in lot:
            if not re.fullmatch(r"(bruits/)?[a-z0-9_]{1,60}\.m4a", x["sortie"]) or not str(x.get("texte") or "").strip():
                raise RuntimeError(f"lot : element invalide ({x.get('sortie')})")
    elif a.texte:
        n = max(1, min(6, a.variantes))
        lot = [{"texte": a.texte, "sortie": f"{nom}.m4a" if n == 1 else f"{nom}_{k + 1}.m4a", "duree": a.duree, "seed": a.seed + k} for k in range(n)]
    else:
        raise RuntimeError("son : une phrase ou --lot")
    cfg = load_config(a)
    ff = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    if not ff:
        raise RuntimeError("ffmpeg introuvable")
    jtok = secrets.token_urlsafe(24)
    marque = data / "son_modeles.json"  # ecrit quand les modeles ont ete vus sur le volume
    pre = {}
    if not marque.exists():  # premier usage : telecharger avant de louer le pod
        for (dossier, fname), url in SON.items():
            log(f"telechargement de {fname}")
            pre[fname] = telecharger(url, data / "work" / "son" / fname)
    t0 = time.time()
    pod_id, cost, gpu = runpod.create_pod(cfg["infra"], f"{PREFIX}son-{int(time.time())}", env={"JUPYTER_PASSWORD": jtok})
    log(f"pod {pod_id} cree ({gpu}, {cost} $/h)")
    faits = []
    try:
        c = Comfy(pod_id)
        c.wait_ready()
        for (dossier, fname), url in SON.items():
            if c.has_model(dossier, fname):
                continue
            log(f"{fname} absent du volume : depot (une seule fois)")
            deposer(pod_id, jtok, fname, pre.get(fname) or pre.setdefault(fname, telecharger(url, data / "work" / "son" / fname)), dossier)
            for _ in range(18):  # ComfyUI ne liste un fichier neuf qu'apres un moment
                if c.has_model(dossier, fname):
                    break
                time.sleep(10)
            else:
                raise RuntimeError(f"{fname} depose mais pas vu par ComfyUI")
        marque.write_text(json.dumps({"date": time.strftime("%d/%m/%Y %H:%M"), "fichiers": [f for _, f in SON]}), encoding="utf-8")
        (data / "audio").mkdir(parents=True, exist_ok=True)
        for n, x in enumerate(lot):
            bruit, seed = bool(x.get("bruit")), int(x.get("seed") or a.seed + n)
            secondes = max(2.0 if bruit else 3.0, min(47.0, float(x.get("duree") or (4 if bruit else 30))))
            try:
                files = c.run(workflows.son(x["texte"], SON_NEG_BRUIT if bruit else a.neg, secondes, seed, f"{PREFIX}son"), timeout=900)
                if not files:
                    raise RuntimeError("aucun son produit")
                brut = data / "work" / "son" / f"{nom}_{n}_{seed}.flac"
                brut.parent.mkdir(parents=True, exist_ok=True)
                brut.write_bytes(c.fetch(files[0]))
                out = data / "audio" / x["sortie"]
                out.parent.mkdir(parents=True, exist_ok=True)
                if bruit:  # bruit d'un geste : silence du debut retire (l'attaque est a zero), crete a -3 dB, fin en fondu
                    coupe = "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.02"
                    r = subprocess.run([ff, "-hide_banner", "-i", str(brut), "-af", coupe + ",volumedetect", "-f", "null", "-"],
                                       capture_output=True, text=True)
                    mx = re.search(r"max_volume: (-?[\d.]+) dB", r.stderr)
                    gain = min(30.0, -3.0 - float(mx.group(1))) if mx else 0.0
                    filtre = f"{coupe},volume={gain:.1f}dB,areverse,afade=t=in:d=0.25,areverse"
                else:  # niveau regle a -23 LUFS : une ambiance reste en retrait ; fondus courts pour boucler sans claquement
                    filtre = f"loudnorm=I=-23:TP=-2:LRA=11,afade=t=in:d=0.3,afade=t=out:st={secondes - 0.5:.2f}:d=0.5"
                subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(brut), "-af", filtre,
                                "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
                brut.unlink(missing_ok=True)
                faits.append(x["sortie"])
                log(f"SON {x['sortie']} ({secondes:.0f} s, tirage {seed})")
            except Exception as e:  # un son rate n'arrete pas les suivants
                log(f"ECHEC {x['sortie']} : {e}")
    finally:
        runpod.delete_pod(pod_id)
        log(f"pod {pod_id} supprime")
        for f in pre.values():
            f.unlink(missing_ok=True)
    mins = (time.time() - t0) / 60
    print(json.dumps({"son": faits, "minutes": round(mins, 1), "cost_usd": round(mins / 60 * float(cost or 0), 2)}))
    return 0


def cmd_sonimage(a):
    """sonimage --lot f.json --nom pNNNN : le son d'apres l'image (MMAudio) des clips d'un projet, range dans
    data/audio/image/<clip>.m4a. Hors ComfyUI : le script tourne sur le pod, lance par un terminal de Jupyter."""
    import base64
    import re
    import secrets
    from . import sonimage as si
    from .http import _ctx, request
    data = Path(a.data)
    if not re.fullmatch(r"p\d{4}", a.nom or ""):
        raise RuntimeError("sonimage : --nom est l'identifiant du projet (pNNNN)")
    media = data / "projets" / a.nom / "media"
    lot = json.loads(Path(a.lot).read_text(encoding="utf-8"))  # [{"clip" (dans media), "sortie", "texte", "duree", "seed"}]
    for x in lot:
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,80}\.mp4", str(x.get("clip") or "")) \
                or x.get("sortie") != f"image/{Path(x['clip']).stem}.m4a" or not (media / x["clip"]).is_file():
            raise RuntimeError(f"lot : element invalide ({x.get('clip')})")
    if not lot:
        raise RuntimeError("lot vide")
    cfg = load_config(a)
    ff = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    if not ff:
        raise RuntimeError("ffmpeg introuvable")
    jtok = secrets.token_urlsafe(24)
    H, D = {"Authorization": f"token {jtok}"}, si.DOSSIER
    t0 = time.time()
    pod_id, cost, gpu = runpod.create_pod(cfg["infra"], f"{PREFIX}sonimage-{int(t0)}", env={"JUPYTER_PASSWORD": jtok})
    log(f"pod {pod_id} cree ({gpu}, {cost} $/h)")
    hote = f"{pod_id}-8888.proxy.runpod.net"

    def api(m, p, d=None, essais=None, **k):
        """API de Jupyter. Le proxy rend des 404 passagers dans la minute qui suit le demarrage : on insiste."""
        for n in range(essais or (10 if m != "GET" else 1)):
            try:
                return request(m, f"https://{hote}/api/{p}", data=d, headers=H, **k)
            except Exception as e:
                err = e
                if "404" not in str(e):
                    break
                time.sleep(10)
        raise err

    def texte(p):
        return api("GET", f"contents/{D}/{p}?content=1&format=text", retries=1)["content"]

    faits = []
    try:
        for _ in range(60):
            try:
                api("GET", "contents?content=0", timeout=15, retries=1)
                break
            except Exception:
                time.sleep(10)
        else:
            raise RuntimeError("Jupyter n'a pas demarre")
        for d in (D, f"{D}/in", f"{D}/out"):
            for _ in range(8):
                try:
                    api("GET", f"contents/{d}?content=0", retries=1)
                    break
                except Exception:
                    try:
                        api("PUT", f"contents/{d}", {"type": "directory"}, essais=1, retries=1)
                        break
                    except Exception:
                        time.sleep(10)
            else:
                raise RuntimeError(f"dossier {d} inaccessible sur le volume")
        for f in sorted({x["clip"] for x in lot}):
            api("PUT", f"contents/{D}/in/{f}", {"type": "file", "format": "base64", "content": base64.b64encode((media / f).read_bytes()).decode()}, timeout=300)
        envoi = [{"clip": x["clip"], "texte": str(x.get("texte") or "")[:300], "duree": max(1.0, min(10.0, float(x.get("duree") or 5))),
                  "seed": int(x.get("seed") or 42), "neg": si.NEG} for x in lot]
        for nom, contenu in (("lot.json", json.dumps(envoi)), ("lot.py", si.LOT), ("run.sh", si.RUN)):
            api("PUT", f"contents/{D}/{nom}", {"type": "file", "format": "text", "content": contenu})
        for nom in ("fin", "run.log"):
            try:
                api("DELETE", f"contents/{D}/{nom}", essais=1, retries=1)
            except Exception:
                pass
        log(f"{len(envoi)} clip(s) deposes")
        ordre = f"(nohup sh -c 'bash /workspace/{D}/run.sh > /workspace/{D}/run.log 2>&1; echo $? > /workspace/{D}/fin' >/dev/null 2>&1 &)\r"
        for _ in range(3):
            term = api("POST", "terminals")["name"]
            si.ws_envoyer(hote, f"/terminals/websocket/{term}", H, json.dumps(["stdin", ordre]), _ctx)
            time.sleep(10)
            try:
                api("GET", f"contents/{D}/run.log?content=0", essais=3, retries=1)
                break
            except Exception:
                log("le script n'a pas demarre : nouvel essai")
        else:
            raise RuntimeError("le script n'a pas demarre sur le pod")
        log("calcul lance (la premiere fois, l'installation prend dix minutes)")
        vu, code, journal = 0, None, ""
        while time.time() - t0 < 50 * 60:
            time.sleep(20)
            try:
                journal = texte("run.log")
                for l in journal[vu:].splitlines():
                    if l.startswith(("MODELE", "FAIT", "RATE")):
                        log(l[:120])
                vu = len(journal)
            except Exception:
                pass
            try:
                code = texte("fin").strip()
                break
            except Exception:
                pass
        if code is None:
            raise RuntimeError("delai depasse")
        if code != "0" and "FAIT " not in journal:
            raise RuntimeError(f"script en echec (code {code}) : {(journal.strip().splitlines() or ['?'])[-1][-200:]}")
        (data / "audio" / "image").mkdir(parents=True, exist_ok=True)
        for x in lot:
            stem = Path(x["clip"]).stem
            try:
                if f"FAIT {x['clip']}" not in journal:
                    raise RuntimeError("pas de son produit")
                brut = data / "work" / "son" / f"{stem}.flac"
                brut.parent.mkdir(parents=True, exist_ok=True)
                brut.write_bytes(base64.b64decode(api("GET", f"contents/{D}/out/{stem}.flac?content=1&format=base64", essais=3, timeout=300)["content"]))
                subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(brut), "-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k",
                                str(data / "audio" / x["sortie"])], check=True)
                brut.unlink(missing_ok=True)
                faits.append(x["sortie"])
                log(f"SON {x['sortie']} (d'apres l'image, tirage {x.get('seed')})")
            except Exception as e:  # un son rate n'arrete pas les suivants
                log(f"ECHEC {x['sortie']} : {e}")
        for f in [f"in/{x['clip']}" for x in lot] + [f"out/{Path(x['clip']).stem}.flac" for x in lot]:  # rien ne reste sur le volume
            try:
                api("DELETE", f"contents/{D}/{f}", essais=1, retries=1)
            except Exception:
                pass
    finally:
        runpod.delete_pod(pod_id)
        log(f"pod {pod_id} supprime")
    mins = (time.time() - t0) / 60
    print(json.dumps({"son": faits, "minutes": round(mins, 1), "cost_usd": round(mins / 60 * float(cost or 0), 2)}))
    return 0


def controle_lot(data, pid, runs=None):
    """Images d'un projet a faire noter (toutes, ou celles des lancements `runs`, par exemple {"r12", "r13"}) avec la
    description attendue de chacune. Rend (lot, fichiers)."""
    import re
    if not re.fullmatch(r"p\d{4}", pid):
        raise RuntimeError("controle : identifiant de projet attendu (pNNNN)")
    d, lot, fichiers = data / "projets" / pid, [], {}
    p = json.loads((d / "projet.json").read_text(encoding="utf-8"))
    temps, vus, stills = {s["id"]: s["temps"] for s in p["scenes"]}, {}, {s["id"]: s.get("still") or "" for s in p["scenes"]}
    noms = ("position", "appui", "bassin", "genoux", "mains", "regard", "contact", "autres")  # pose decomposee : verifiee champ par champ
    poses = {s["id"]: {k: s[k] for k in noms if s.get(k)} for s in p["scenes"]}
    lieu = str((p.get("continuite") or {}).get("lieu") or "")
    for f in sorted((d / "media").iterdir()):
        m = re.fullmatch(rf"{pid}(r\d+)_(s\d+)\.png", f.name)
        if not m or (runs is not None and m.group(1) not in runs):
            continue
        if m.group(1) not in vus:
            rf_ = d / "runs" / f"{m.group(1)}.json"
            vus[m.group(1)] = {s["name"]: s for s in json.loads(rf_.read_text(encoding="utf-8")).get("shots", [])} if rf_.exists() else {}
        sh = vus[m.group(1)].get(m.group(2)) or {}  # image creee a partir d'une autre ("edit") : la description est celle de la scene
        desc = str(sh.get("still") or stills.get(m.group(2)) or sh.get("edit") or "")
        if desc:
            if not sh.get("still") and lieu:  # la description d'une scene ne redit pas le lieu : il est dans la fiche de continuite
                desc += f", place: {lieu}"
            lot.append({"image": f.name, "projet": pid, "desc": desc[:1500], "perso": p.get("personnage") or "", "temps": temps.get(m.group(2), 0),
                        "champs": sh["champs"] if isinstance(sh.get("champs"), dict) else poses.get(m.group(2), {})})
            fichiers[f.name] = f
    return lot, fichiers


def controle_ranger(data, lot, res):
    """Range les notes dans projets/<id>/notes_images.json (que l'atelier affiche sous chaque image)."""
    jour = time.strftime("%Y-%m-%d %H:%M")
    for pid in sorted({x["projet"] for x in lot}):
        f = data / "projets" / pid / "notes_images.json"
        notes = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        for x in lot:
            if x["projet"] == pid and "score" in res.get(x["image"], {}):
                notes[x["image"]] = res[x["image"]] | {"temps": x["temps"], "date": jour}
        f.write_text(json.dumps(notes, indent=1), encoding="utf-8")


class Controleur:
    """Pod du controleur d'images (voir controle.py) : ouvrir() une fois, noter() autant de lots qu'on veut, fermer()
    toujours (dans un finally) : le pod est supprime."""

    def __init__(self, cfg, data):
        import secrets
        self.cfg, self.data, self.pod_id, self.cost, self.t0, self.journal, self.pret = cfg, Path(data), None, 0.0, time.time(), "", False
        self.jtok = secrets.token_urlsafe(24)
        self.H = {"Authorization": f"token {self.jtok}"}

    def api(self, m, p, d=None, essais=None, **k):
        from .http import request
        for n in range(essais or (10 if m != "GET" else 1)):
            try:
                return request(m, f"https://{self.pod_id}-8888.proxy.runpod.net/api/{p}", data=d, headers=self.H, **k)
            except Exception as e:
                err = e
                if "404" not in str(e):
                    break
                time.sleep(10)
        raise err

    def texte(self, p):
        from . import controle as ct
        return self.api("GET", f"contents/{ct.DOSSIER}/{p}?content=1&format=text", retries=1)["content"]

    def ouvrir(self):
        from . import controle as ct
        D = ct.DOSSIER
        self.pod_id, cost, gpu = runpod.create_pod(self.cfg["infra"], f"{PREFIX}controle-{int(self.t0)}", env={"JUPYTER_PASSWORD": self.jtok})
        self.t0 = time.time()  # le cout se compte a partir de la creation du pod
        self.cost = float(cost or 0)
        log(f"controle : pod {self.pod_id} cree ({gpu}, {cost} $/h)")
        for _ in range(60):
            try:
                self.api("GET", "contents?content=0", timeout=15, retries=1)
                break
            except Exception:
                time.sleep(10)
        else:
            raise RuntimeError("Jupyter n'a pas demarre")
        for d in (D, f"{D}/in"):
            for _ in range(8):
                try:
                    self.api("GET", f"contents/{d}?content=0", retries=1)
                    break
                except Exception:
                    try:
                        self.api("PUT", f"contents/{d}", {"type": "directory"}, essais=1, retries=1)
                        break
                    except Exception:
                        time.sleep(10)
            else:
                raise RuntimeError(f"dossier {d} inaccessible sur le volume")
        for nom, contenu in (("cases.json", json.dumps(ct.CASES)), ("ouinon.json", json.dumps(ct.OUINON)), ("ouinon_desc.txt", ct.OUINON_DESC),
                             ("modele.txt", ct.MODELE), ("systeme.txt", ct.SYSTEME), ("question.txt", ct.QUESTION), ("lot.py", ct.LOT), ("run.sh", ct.RUN)):
            self.api("PUT", f"contents/{D}/{nom}", {"type": "file", "format": "text", "content": contenu})
        self.pret = True

    def noter(self, lot, fichiers, delai_min=45):
        """Fait noter un lot ; rend {image: notes}. Aucune image ne reste sur le volume."""
        import base64
        from . import controle as ct
        from . import sonimage as si
        from .http import _ctx
        if not self.pret:
            raise RuntimeError("controleur pas pret")
        D, t0 = ct.DOSSIER, time.time()
        try:
            for nom, f in fichiers.items():
                self.api("PUT", f"contents/{D}/in/{nom}", {"type": "file", "format": "base64", "content": base64.b64encode(f.read_bytes()).decode()}, timeout=300)
            self.api("PUT", f"contents/{D}/lot.json", {"type": "file", "format": "text", "content": json.dumps(lot)})
            for nom in ("fin", "run.log", "out.json"):
                try:
                    self.api("DELETE", f"contents/{D}/{nom}", essais=1, retries=1)
                except Exception:
                    pass
            log(f"controle : {len(lot)} image(s) deposee(s)")
            ordre = f"(nohup sh -c 'bash /workspace/{D}/run.sh > /workspace/{D}/run.log 2>&1; echo $? > /workspace/{D}/fin' >/dev/null 2>&1 &)\r"
            for _ in range(3):
                term = self.api("POST", "terminals")["name"]
                si.ws_envoyer(f"{self.pod_id}-8888.proxy.runpod.net", f"/terminals/websocket/{term}", self.H, json.dumps(["stdin", ordre]), _ctx)
                time.sleep(10)
                try:
                    self.api("GET", f"contents/{D}/run.log?content=0", essais=3, retries=1)
                    break
                except Exception:
                    log("controle : le script n'a pas demarre, nouvel essai")
            else:
                raise RuntimeError("le script n'a pas demarre sur le pod")
            vu, code, journal = 0, None, ""
            while time.time() - t0 < delai_min * 60:
                time.sleep(20)
                try:
                    journal = self.texte("run.log")
                    for l in journal[vu:].splitlines():
                        if l.startswith(("MODELE", "VISAGES", "RATE", "PYTHON")):
                            log("controle : " + l[:60])
                    vu = len(journal)
                except Exception:
                    pass
                try:
                    code = self.texte("fin").strip()
                    break
                except Exception:
                    pass
            if code is None:
                raise RuntimeError("delai depasse")
            try:
                journal = self.texte("run.log")
            except Exception:
                pass
            self.journal += journal + "\n"
            try:
                res = json.loads(self.texte("out.json"))
            except Exception:
                for l in journal.strip().splitlines()[-25:]:
                    log("  | " + l[:200])
                raise RuntimeError(f"script en echec (code {code})")
            for l in journal.splitlines():  # ce qui a empeche un des deux outils de tourner
                if "Error" in l or l.startswith("Traceback"):
                    log("  | " + l[:200])
            return res
        finally:
            for nom in fichiers:
                try:
                    self.api("DELETE", f"contents/{D}/in/{nom}", essais=1, retries=1)
                except Exception:
                    pass

    def fermer(self):
        if self.pod_id:
            try:
                runpod.delete_pod(self.pod_id)
                log(f"controle : pod {self.pod_id} supprime")
            except Exception as e:
                log(f"ATTENTION : suppression du pod {self.pod_id} echouee : {e}")
        if self.journal:
            sortie = self.data / "work" / "controle"
            sortie.mkdir(parents=True, exist_ok=True)
            (sortie / f"run-{time.strftime('%Y%m%d-%H%M')}.log").write_text(self.journal, encoding="utf-8")

    def cout(self):
        return round((time.time() - self.t0) / 3600 * self.cost, 2) if self.pod_id else 0.0


def cmd_controle(a):
    """controle --nom pNNNN[,pNNNN] : fait noter toutes les images des projets par le mesureur de visage et le modele
    de vision (voir controle.py). Les notes sont rangees dans projets/<id>/notes_images.json ; rien d'autre n'est change
    dans les projets. Le journal du pod est garde dans data/work/controle/."""
    data, lot, fichiers = Path(a.data), [], {}
    for pid in a.nom.split(","):
        l, f = controle_lot(data, pid)
        lot += l
        fichiers |= f
    if not lot:
        raise RuntimeError("aucune image a controler")
    c, res = Controleur(load_config(a), data), {}
    try:
        c.ouvrir()
        res = c.noter(lot, fichiers)
    finally:
        c.fermer()
    controle_ranger(data, lot, res)
    print(json.dumps({"controle": len([r for r in res.values() if "score" in r]), "images": len(lot),
                      "minutes": round((time.time() - c.t0) / 60, 1), "cost_usd": c.cout()}))
    return 0


SEUIL_RELANCE = 4   # une scene dont aucune image ne depasse cette note sur 10 est refaite
RELANCES = 2        # nouvelles tentatives au plus


def cmd_serie(a):
    """serie pNNNN r12.json r13.json r14.json : plusieurs images par scene, controlees. Chaque fichier de plans est une
    variante des memes scenes (ecrits par l'atelier) ; ils sont executes l'un apres l'autre, puis le controleur note les
    images. Une scene dont aucune image ne depasse SEUIL_RELANCE est refaite seule (autre tirage), RELANCES fois au plus.
    L'atelier propose ensuite la mieux notee ; le proprietaire garde le choix. Un controleur en panne n'arrete rien :
    les images restent, sans note."""
    import copy
    import random
    import re
    import signal
    import threading
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))  # arret demande : le finally supprime le pod du controleur
    data, pid = Path(a.data), a.projet
    jobs = [Path(j) for j in a.jobs]
    d, runs, echecs = jobs[0].parent, {j.stem for j in jobs}, 0
    c = Controleur(load_config(a), data)
    ouverture = {}

    def ouvrir():
        if "abandon" in ouverture:  # les images n'ont pas abouti : pas de pod pour rien
            return
        try:
            c.ouvrir()
        except Exception as e:
            ouverture["erreur"] = str(e)[:300]

    def lancer(j):
        return cmd_run(argparse.Namespace(job=str(j), data=a.data, out=a.out, pod_id=a.pod_id, keep_pod=False, stills_only=True, config=a.config))

    # Les variantes sont regroupees en un seul lancement : le pilote y calcule toutes les images creees puis toutes
    # les retouches, sans recharger les modeles entre deux variantes. Chaque plan garde le nom de fichier de sa variante.
    tout, groupe = [], None
    for j in jobs:
        job = json.loads(j.read_text(encoding="utf-8"))
        groupe = groupe or {k: v for k, v in job.items() if k != "shots"}
        for i, sh in enumerate(job["shots"]):
            s = {**job.get("defaults", {}), **sh}
            tout.append({**s, "seed": int(s.get("seed", 1)) + (0 if s.get("same_seed") else i), "same_seed": True,
                         "sortie": f"{job['name']}_{sh['name']}"})
    (data / "work").mkdir(parents=True, exist_ok=True)
    regroupe = data / "work" / f"girls-ai-serie-{pid}.json"
    regroupe.write_text(json.dumps({**groupe, "shots": tout}, ensure_ascii=False), encoding="utf-8")
    # le pod du controleur demarre vers la fin des images (environ 25 s par image, 2 min 30 de demarrage)
    depart = threading.Event()
    fil = threading.Thread(target=lambda: (depart.wait(max(0, 25 * len(tout) - 150)), ouvrir()), daemon=True)
    try:
        fil.start()
        try:
            echecs = len(jobs) if lancer(regroupe) else 0
        except BaseException:
            ouverture["abandon"] = True
            raise
        depart.set()
        try:
            fil.join()
            if "erreur" in ouverture:
                raise RuntimeError(ouverture["erreur"])
            base = json.loads(jobs[0].read_text(encoding="utf-8"))
            for tour in range(RELANCES + 1):
                lot, fichiers = controle_lot(data, pid, runs)
                nf = data / "projets" / pid / "notes_images.json"
                deja = json.loads(nf.read_text(encoding="utf-8")) if nf.exists() else {}
                neuf = [x for x in lot if x["image"] not in deja]
                if neuf:
                    controle_ranger(data, neuf, c.noter(neuf, {x["image"]: fichiers[x["image"]] for x in neuf}))
                notes = json.loads(nf.read_text(encoding="utf-8")) if nf.exists() else {}
                par = {}
                for x in lot:
                    s = (notes.get(x["image"]) or {}).get("score", -1)
                    if isinstance(s, int) and s >= 0:
                        par.setdefault(re.search(r"_(s\d+)\.png$", x["image"]).group(1), []).append(s)
                rates = [s for s, l in par.items() if max(l) <= SEUIL_RELANCE]
                log(f"controle : {len(par)} scene(s) notee(s), a refaire : {', '.join(rates) or 'aucune'}")
                if not rates or tour == RELANCES:
                    break
                n = max(int(f.stem[1:]) for f in d.glob("r*.json")) + 1
                job = copy.deepcopy(base) | {"name": f"{pid}r{n}"}
                job["shots"] = [sh for sh in job["shots"] if sh["name"] in rates]
                for sh in job["shots"]:
                    sh["seed"] = random.randint(1, 999999)
                    m = re.fullmatch(rf"{base['name']}_(s\d+)\.png", Path(str(sh.get("image") or "")).name)
                    if m and m.group(1) in rates:  # tiree d'une image elle-meme refaite : partir de la nouvelle
                        sh["image"] = str(Path(sh["image"]).with_name(f"{pid}r{n}_{m.group(1)}.png"))
                (d / f"r{n}.json").write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
                runs.add(f"r{n}")
                log(f"relance {tour + 1} sur {RELANCES} : {len(job['shots'])} image(s)")
                lancer(d / f"r{n}.json")
        except Exception as e:  # le controle est un plus : sans lui les images restent, sans note
            log(f"controle impossible : {str(e)[:300]}")
    finally:
        depart.set()
        if fil.is_alive():
            fil.join(timeout=900)
        c.fermer()
        log(f"rapport : {json.dumps({'serie': sorted(runs), 'controle_usd': c.cout()})}")
    return 1 if echecs == len(jobs) else 0


def effacer_attente(pod_id, jtok, data):
    """Efface du volume les fichiers de LoRA sortis du catalogue par la page Hub (data/lora_effacer.json), par l'API de
    fichiers de Jupyter. Rend les noms effaces ; ceux qui echouent restent dans la liste pour la fois suivante."""
    import re
    import urllib.parse
    from .http import request
    file = Path(data) / "lora_effacer.json"
    noms = json.loads(file.read_text(encoding="utf-8")) if file.exists() else []
    faits, reste = [], []
    for nom in noms:
        if not re.fullmatch(r"[A-Za-z0-9_.\-/ ]{1,200}\.safetensors", nom) or ".." in nom or nom.startswith("/"):
            log(f"effacement refuse (nom inattendu) : {nom[:80]}")
            continue
        url = f"https://{pod_id}-8888.proxy.runpod.net/api/contents/runpod-slim/ComfyUI/models/loras/{urllib.parse.quote(nom)}"
        try:
            request("DELETE", url, headers={"Authorization": f"token {jtok}"}, timeout=120, retries=2)
            faits.append(nom)
            log(f"EFFACE {nom}")
        except Exception as e:
            if "HTTP 404" in str(e):  # deja absent du volume
                faits.append(nom)
                log(f"EFFACE {nom} (deja absent)")
            else:
                reste.append(nom)
                log(f"ECHEC effacement de {nom} : {str(e)[:200]}")
    if reste:
        file.write_text(json.dumps(reste), encoding="utf-8")
    else:
        file.unlink(missing_ok=True)
    return faits


def lora_purge(a, data):
    """Efface du volume les fichiers de LoRA en attente d'effacement : un pod de quelques minutes, supprime a la fin."""
    import secrets
    if not (data / "lora_effacer.json").exists():
        log("rien a effacer")
        return 0
    cfg = load_config(a)
    jtok = secrets.token_urlsafe(24)
    pod_id, cost, gpu = runpod.create_pod(cfg["infra"], f"{PREFIX}lora-{int(time.time())}", env={"JUPYTER_PASSWORD": jtok})
    log(f"pod {pod_id} cree ({gpu}, {cost} $/h)")
    try:
        c = Comfy(pod_id)
        c.wait_ready()
        faits = effacer_attente(pod_id, jtok, data)
        time.sleep(5)
        vus = set(inventaire(c, data)) - set(faits)  # ComfyUI peut lister encore un moment un fichier efface
        (data / "lora_volume.json").write_text(json.dumps({"date": time.strftime("%d/%m/%Y %H:%M"), "fichiers": sorted(vus)}), encoding="utf-8")
    finally:
        runpod.delete_pod(pod_id)
        log(f"pod {pod_id} supprime")
    log(f"rapport : {len(faits)} fichier(s) efface(s)")
    return 0


def lora_sync(a, data, catp, cat):
    """Charge sur le volume les LoRA retenues dans le hub (data/hub_charger.json, ecrit par la page Hub), dans un seul pod,
    et les inscrit au catalogue. Chaque element : {cle, name, label, strength, base, famille, cat, trigger, source,
    vignette, fichiers: [{role: ""|"high"|"low", url, auth: ""|"civitai"}]}. Un echec n'arrete pas les suivantes."""
    import secrets
    from .http import request
    file = data / "hub_charger.json"
    todo = json.loads(file.read_text(encoding="utf-8")) if file.exists() else []
    if not todo:
        log("rien a charger")
        return 0
    cfg = load_config(a)
    tok = os.environ.get("CIVITAI_TOKEN", "")
    jtok = secrets.token_urlsafe(24)
    pod_id, cost, gpu = runpod.create_pod(cfg["infra"], f"{PREFIX}lora-{int(time.time())}", env={"JUPYTER_PASSWORD": jtok})
    log(f"pod {pod_id} cree ({gpu}, {cost} $/h)")
    ok, deposes = 0, []
    try:
        c = Comfy(pod_id)
        c.wait_ready()
        effaces = effacer_attente(pod_id, jtok, data)  # fichiers sortis du catalogue depuis le dernier pod
        for x in todo:
            try:
                noms = {}
                for f in x["fichiers"]:
                    blob = request("GET", f["url"], headers={"Authorization": f"Bearer {tok}"} if f.get("auth") == "civitai" and tok else {},
                                   raw=True, timeout=1800)
                    if len(blob) < 100000:
                        raise RuntimeError("telechargement refuse (cle Civitai absente ou fichier reserve)")
                    fname = f"{x['name']}{'_' + f['role'] if f.get('role') else ''}.safetensors"
                    deposer(pod_id, jtok, fname, blob)
                    noms[f.get("role") or ""] = fname
                    deposes.append(fname)
                    del blob
                haut = noms.get("high") or noms.get("") or noms.get("low")
                cat[x["name"]] = {"label": x.get("label") or x["name"], "file": haut, "strength": float(x.get("strength") or 0.6),
                                  "base": x.get("base", ""), "famille": x.get("famille", "zimage"), "cat": x.get("cat", "autre"),
                                  "trigger": x.get("trigger", ""), "source": x.get("source", ""), "vignette": x.get("vignette", ""),
                                  "hub": x["cle"], **({"file_low": noms["low"]} if "low" in noms and haut != noms["low"] else {})}
                catp.write_text(yaml.safe_dump(cat, allow_unicode=True, sort_keys=False), encoding="utf-8")
                ok += 1
                log(f"CHARGE {x['cle']} : {x['name']}")
            except Exception as e:  # une LoRA refusee n'empeche pas les autres
                log(f"ECHEC {x['cle']} : {str(e)[:300]}")
        time.sleep(10)
        vus = inventaire(c, data)
        if set(deposes) - set(vus) or set(effaces) & set(vus):  # ComfyUI ne voit un fichier neuf ou efface qu'apres un moment
            (data / "lora_volume.json").write_text(json.dumps({"date": time.strftime("%d/%m/%Y %H:%M"), "fichiers": sorted((set(vus) | set(deposes)) - (set(effaces) - set(deposes)))}), encoding="utf-8")
    finally:
        runpod.delete_pod(pod_id)
        log(f"pod {pod_id} supprime")
    file.unlink(missing_ok=True)
    log(f"rapport : {ok} LoRA chargee(s) sur {len(todo)}")
    return 0


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
    if a.action == "sync":
        return lora_sync(a, data, catp, cat)
    if a.action == "purge":
        return lora_purge(a, data)
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
        deposer(pod_id, jtok, fname, blob)
        seen = False
        for _ in range(6):  # la liste de ComfyUI peut mettre un moment a voir un fichier neuf
            if c.has_model("loras", fname):
                seen = True
                break
            time.sleep(10)
        if not seen:
            log("fichier depose sur le volume ; ComfyUI ne le liste pas encore, il le verra au prochain demarrage de pod")
        inventaire(c, data)
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
    lo = sub.add_parser("lora", help="LoRA supplementaires : add <adresse Civitai> --name nom | list | remove <nom> | sync (charge les LoRA retenues dans le hub) | purge (efface du volume les fichiers sortis du catalogue)")
    lo.add_argument("action", choices=["add", "list", "remove", "sync", "purge"])
    lo.add_argument("ref", nargs="?", default="")
    lo.add_argument("--name")
    lo.add_argument("--strength", type=float, default=0.6)
    lo.add_argument("--force", action="store_true", help="accepter malgre une alerte (base, licence)")
    lo.add_argument("--pod-id")
    lo.add_argument("--jupyter-token")
    lo.add_argument("--data", default=os.environ.get("DATA_DIR", str(ROOT / "server" / "data")))
    lo.set_defaults(fn=cmd_lora)
    so = sub.add_parser("son", help="ambiance sonore d'apres une phrase en anglais, rangee dans data/audio (Stable Audio Open)")
    so.add_argument("texte", nargs="?")
    so.add_argument("--lot", help="fichier JSON d'un lot de sons (ecrit par l'atelier)")
    so.add_argument("--nom", help="nom du fichier (lettres, chiffres, _)")
    so.add_argument("--duree", type=float, default=30.0, help="secondes, 47 au plus")
    so.add_argument("--variantes", type=int, default=1, help="nombre de tirages (6 au plus)")
    so.add_argument("--seed", type=int, default=100)
    so.add_argument("--neg", default=SON_NEG, help="ce qu'on ne veut pas entendre")
    so.add_argument("--data", default=os.environ.get("DATA_DIR", str(ROOT / "server" / "data")))
    so.set_defaults(fn=cmd_son)
    sm = sub.add_parser("sonimage", help="son d'apres l'image des clips d'un projet (MMAudio, licence non commerciale), range dans data/audio/image")
    sm.add_argument("--lot", required=True, help="fichier JSON du lot (ecrit par l'atelier)")
    sm.add_argument("--nom", required=True, help="identifiant du projet (pNNNN)")
    sm.add_argument("--data", default=os.environ.get("DATA_DIR", str(ROOT / "server" / "data")))
    sm.set_defaults(fn=cmd_sonimage)
    co = sub.add_parser("controle", help="essai : fait noter les images de projets par un mesureur de visage et un modele de vision")
    co.add_argument("--nom", required=True, help="identifiants de projet separes par des virgules (pNNNN,pNNNN)")
    co.add_argument("--data", default=os.environ.get("DATA_DIR", str(ROOT / "server" / "data")))
    co.set_defaults(fn=cmd_controle)
    se = sub.add_parser("serie", help="plusieurs images par scene (un fichier de plans par variante), notees par le controleur ; les scenes ratees sont refaites")
    se.add_argument("projet", help="identifiant du projet (pNNNN)")
    se.add_argument("jobs", nargs="+")
    se.add_argument("--data", default=os.environ.get("DATA_DIR", str(ROOT / "server" / "data")))
    se.add_argument("--pod-id", help="pod des images (ni cree ni supprime)")
    se.add_argument("--out", help="dossier de sortie")
    se.set_defaults(fn=cmd_serie)
    a = ap.parse_args()
    try:
        sys.exit(a.fn(a) or 0)
    except RuntimeError as e:  # erreur attendue (pas de machine, cle refusee...) : message court
        log(f"ARRET : {str(e)[:400]}")
        sys.exit(2)


if __name__ == "__main__":
    main()
