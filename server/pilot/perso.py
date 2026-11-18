"""Atelier du personnage : images de sa bibliotheque (lieux vides, tenues a plat, portraits, planches du corps) et
entrainement de sa LoRA sur le volume. Lance par l'interface (tools/triage/biblio.py) ; le journal a la forme de celui
du pilote ("<nom> : image", "ECHEC", "rapport : {...}")."""
import struct
import base64
import json
import secrets
import time
from pathlib import Path

from . import runpod, workflows
from .comfy import PERDUE, Comfy

PREFIX = "girls-ai-"
DOSSIER = "girls-ai-train"  # sur le volume : jeu d'images d'un entrainement, retire a la fin
PLACE_MIN = 25  # Go libres exiges sur le volume avant d'entrainer (le modele de base en pese 12 s'il manque)
# Lance l'entrainement (tools/train/train_zimage_lora.sh) puis retire ce que ce lancement a pose : jeu d'images, cache,
# reglages et fichier intermediaire. Seule la LoRA finale reste sur le volume.
RUN = """#!/bin/bash
D=/workspace/%(d)s
[ -d /workspace/musubi-tuner/venv ] || { echo "ARRET : outil d'entrainement absent du volume (/workspace/musubi-tuner)"; exit 3; }
FREE=$(df -BG --output=avail /workspace | tail -1 | tr -dc 0-9)
echo "PLACE ${FREE} Go libres"
[ "$FREE" -ge %(place)d ] || { echo "ARRET : moins de %(place)d Go libres sur le volume"; exit 4; }
bash $D/train.sh $D/%(nom)s %(nom)s %(passages)d
code=$?
rm -rf $D/%(nom)s /workspace/train_cache_%(nom)s /workspace/train_%(nom)s.toml /workspace/lea_lora/%(nom)s.safetensors
exit $code
"""


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def _fin(report, t0, pod_id, own):
    if own and pod_id:
        try:
            runpod.delete_pod(pod_id)
            log(f"pod {pod_id} supprime")
        except Exception as e:
            log(f"ATTENTION : suppression du pod {pod_id} echouee : {e}")
    report["minutes"] = round((time.time() - t0) / 60, 1)
    if report.get("cost_per_hr"):
        report["cost_usd"] = round(report["minutes"] / 60 * report["cost_per_hr"], 2)
    log(f"rapport : {json.dumps(report, ensure_ascii=False)}")
    return 1 if any("error" in s for s in report["shots"]) or not report["shots"] else 0


def images(a, cfg, resolve_loras, to_mp4=None):
    """Lot d'images d'un personnage : {"nom", "out", "character", "taches": [{"sortie", "prompt", "seed", "taille",
    "lora" (LoRA du personnage ou non), "loras" (en plus), "force", "ref" (image dont celle-ci est tiree par retouche),
    "refs" (images en plus pour la retouche : « image 2 », « image 3 » du texte), "sans_tete" (celles des refs dont le haut, la tete, est coupe), "finir" (image a finir par Z-Image hors visage, "finition" : sa force)}]}.
    Tache de clip (banc des LoRA de clip) : "clip" (image de depart), "prompt" (le mouvement), "loras" (LoRA de clip), "images" (duree,
    81 par defaut : 5 s) ; elle rend <sortie>.mp4, fabrique comme un clip de la Production."""
    lot = json.load(open(a.lot, encoding="utf-8"))
    models, char = cfg["models"], {**cfg["character"], **(lot.get("character") or {})}
    sans = {**char, "lora_still_zimage": None, "extra_loras_still": []}
    out = Path(lot["out"])
    out.mkdir(parents=True, exist_ok=True)
    t0, pod_id, own = time.time(), a.pod_id, False
    report = {"job": lot["nom"], "shots": []}
    try:
        if not pod_id:
            pod_id, cost, gpu = runpod.create_pod(cfg["infra"], f"{PREFIX}{lot['nom']}-{int(t0)}")
            own = True
            report.update(gpu=gpu, cost_per_hr=cost)
            log(f"pod {pod_id} cree ({gpu}, {cost} $/h)")
        c = Comfy(pod_id)
        c.wait_ready()
        log("ComfyUI pret")
        volume, refs, perdue = c.models("loras"), {}, False
        for t in sorted(lot["taches"], key=lambda t: (bool(t.get("clip")), bool(t.get("finir")), bool(t.get("ref")))):  # creations, retouches, finitions puis clips
            e = {"name": t["sortie"]}
            report["shots"].append(e)
            if (time.time() - t0) / 60 > cfg["infra"].get("max_session_min", 90):
                e["error"] = "non traite : duree maximale atteinte"
                continue
            if perdue:
                e["error"] = "non traite : " + PERDUE
                continue
            try:
                d = time.time()
                w, h = t.get("taille") or ([480, 832] if t.get("clip") else [720, 1280])
                if t.get("clip"):
                    vlo = [x for x in resolve_loras(cfg, t.get("loras") or []) if x["video"]]
                    if any(f and f not in volume for x in vlo for f in (x["name"], x.get("low"))):
                        raise RuntimeError("LoRA introuvable sur le volume")
                    if t["clip"] not in refs:
                        refs[t["clip"]] = c.upload(f"ga_perso_ref{len(refs)}.png", Path(t["clip"]).read_bytes())
                    mouv = t["prompt"] + char.get("motion_suffix", "") + "".join(f" {x['trigger']}" for x in vlo if x.get("trigger"))
                    g = workflows.clip(models, char, refs[t["clip"]], mouv, w, h, int(t["seed"]), f"ga_{t['sortie']}", mode=t.get("mode") or "natural",
                                       frames=int(t.get("images") or 81), loras=vlo)
                    webm = out / "lots" / f"{t['sortie']}.webm"
                    webm.write_bytes(c.fetch(c.run(g)[0]))
                    to_mp4(webm, out / f"{t['sortie']}.mp4", True, True)
                    webm.unlink()
                    log(f"{t['sortie']} : clip ({round(time.time() - d)} s)")
                    continue
                if t.get("ref"):
                    if t["ref"] not in refs:
                        refs[t["ref"]] = c.upload(f"ga_perso_ref{len(refs)}.png", Path(t["ref"]).read_bytes())
                    for r in t.get("refs") or []:
                        if r not in refs:
                            refs[r] = c.upload(f"ga_perso_ref{len(refs)}.png", Path(r).read_bytes())
                    if t.get("tete"):  # la tete du portrait posee sur un corps dessine (image entiere), puis son visage repose en grand
                        if t["tete"] not in refs:
                            refs[t["tete"]] = c.upload(f"ga_perso_ref{len(refs)}.png", Path(t["tete"]).read_bytes())
                        g = workflows.edit_image(models, refs[t["ref"]], t["prompt"], w, h, int(t["seed"]), f"ga_{t['sortie']}_t")
                        g["img2"] = {"class_type": "LoadImage", "inputs": {"image": refs[t["tete"]]}}
                        g["pos"]["inputs"]["image2"] = g["neg"]["inputs"]["image2"] = ["img2", 0]
                        img = c.fetch(c.run(g)[0])
                        try:  # en pied la tete est petite : son visage est repose en grand, garde seulement s'il est reste a sa place
                            up, bon = c.upload(f"ga_perso_tete{len(report['shots'])}.png", img), False
                            for e in range(3):
                                fs = c.run(workflows.poser_visage(models, up, refs[t["tete"]], w, h, int(t["seed"]) + 977 * e, f"ga_{t['sortie']}"))
                                tm = [workflows.boite_png(c.fetch(f)) for f in sorted(fs, key=lambda f: f["filename"]) if "_temoin" in f["filename"]]
                                if len(tm) == 2 and workflows.visage_en_place(*tm):
                                    img, bon = c.fetch([f for f in fs if "_temoin" not in f["filename"]][0]), True
                                    break
                            log(f"{t['sortie']} : visage repose en grand" if bon else f"{t['sortie']} : visage laisse tel quel (il bougeait a chaque essai)")
                        except Exception as x:
                            log(f"{t['sortie']} : visage laisse tel quel ({str(x)[:200]})")
                        (out / f"{t['sortie']}.png").write_bytes(img)
                        log(f"{t['sortie']} : image ({round(time.time() - d)} s)")
                        continue
                    ed = [x for x in resolve_loras(cfg, t.get("loras_edit") or []) if x.get("retouche")]  # LoRA du modele de retouche, au choix du proprietaire
                    if any(x["name"] not in volume for x in ed):
                        raise RuntimeError("LoRA introuvable sur le volume")
                    trig = ", ".join(x["trigger"] for x in ed if x.get("trigger"))
                    g = workflows.edit_image(models, refs[t["ref"]], t["prompt"] + (f" {trig}" if trig else ""), w, h, int(t["seed"]), f"ga_{t['sortie']}", loras=ed)
                    for i, r in enumerate(t.get("refs") or [], 2):
                        g[f"img{i}"] = {"class_type": "LoadImage", "inputs": {"image": refs[r]}}
                        src = f"img{i}"
                        if r in (t.get("sans_tete") or []):  # image du corps : la tete est coupee, un seul visage reste en jeu (celui de l'image 1)
                            rw, rh = struct.unpack(">II", Path(r).read_bytes()[16:24])  # taille lue dans l'en-tete du PNG
                            haut = int(rh * 0.27) // 8 * 8
                            src = f"img{i}c"
                            g[src] = {"class_type": "ImageCrop", "inputs": {"image": [f"img{i}", 0], "width": rw, "height": rh - haut, "x": 0, "y": haut}}
                        g["pos"]["inputs"][f"image{i}"] = g["neg"]["inputs"][f"image{i}"] = [src, 0]
                else:
                    ch = char if t.get("lora") else sans
                    extra = [x for x in resolve_loras(cfg, t.get("loras") or []) if not x["video"] and not x.get("retouche")]
                    for f in [ch.get("lora_still_zimage")] + [x["name"] for x in extra]:
                        if f and f not in volume:
                            raise RuntimeError("LoRA introuvable sur le volume")
                    trig = ", ".join(x["trigger"] for x in extra if x.get("trigger"))
                    if t.get("finir"):  # finition d'une planche faite par retouche (lue maintenant : elle vient d'etre calculee) ; le visage est garde
                        src = c.upload(f"ga_perso_fin{len(report['shots'])}.png", Path(t["finir"]).read_bytes())
                        g = workflows.finir_planche(models, sans, src, t["prompt"] + (f" {trig}" if trig else ""), w, h, int(t["seed"]), f"ga_{t['sortie']}",
                                                    loras=extra, denoise=min(max(float(t.get("finition") or 0.5), 0.2), 0.8))
                    else:
                        g = workflows.still_zimage(models, ch, t["prompt"] + (f" {trig}" if trig else ""), w, h, int(t["seed"]), f"ga_{t['sortie']}",
                                                   loras=extra, char_strength=t.get("force"))
                (out / f"{t['sortie']}.png").write_bytes(c.fetch(c.run(g)[0]))
                log(f"{t['sortie']} : image ({round(time.time() - d)} s)")
            except Exception as x:  # une image ratee n'arrete pas le lot
                e["error"] = str(x)[:300]
                perdue = perdue or PERDUE in e["error"]
                log(f"{t['sortie']} : ECHEC image {e['error']}")
    finally:
        code = _fin(report, t0, pod_id, own)
    return code


def entrainer(a, cfg):
    """Entraine la LoRA d'un personnage sur un pod a lui, puis tire des images d'essai a plusieurs forces. Lot :
    {"nom" (nom de la LoRA), "images" (dossier de paires .png + .txt), "passages", "delai_min", "out", "character",
    "essais": [{"sortie", "prompt", "seed", "force"}]}. Le pod est toujours supprime ; le jeu d'images ne reste pas sur le volume."""
    from . import sonimage as si
    from .http import _ctx, request
    lot = json.load(open(a.lot, encoding="utf-8"))
    nom, D = lot["nom"], DOSSIER
    paires = [f for f in sorted(Path(lot["images"]).glob("*.png")) if f.with_suffix(".txt").is_file()]
    if len(paires) < 10:
        raise RuntimeError("il faut au moins 10 images legendees")
    models, char = cfg["models"], {**cfg["character"], **(lot.get("character") or {})}
    out = Path(lot["out"])
    out.mkdir(parents=True, exist_ok=True)
    infra = {**cfg["infra"], "gpu_types": cfg["infra"].get("gpu_types_video") or cfg["infra"]["gpu_types"]}  # carte rapide en premier
    delai = min(int(lot.get("delai_min") or 75), infra.get("max_session_min", 90) - 10)
    jtok = secrets.token_urlsafe(24)
    H = {"Authorization": f"token {jtok}"}
    t0, pod_id = time.time(), None
    report = {"job": nom, "shots": [], "lora": ""}

    def api(m, p, d=None, essais=None, **k):
        for _ in range(essais or (10 if m != "GET" else 1)):
            try:
                return request(m, f"https://{pod_id}-8888.proxy.runpod.net/api/{p}", data=d, headers=H, **k)
            except Exception as e:
                err = e
                if "404" not in str(e):
                    break
                time.sleep(10)
        raise err

    def texte(p):
        return api("GET", f"contents/{D}/{p}?content=1&format=text", retries=1)["content"]

    try:
        pod_id, cost, gpu = runpod.create_pod(infra, f"{PREFIX}lora-{int(t0)}", env={"JUPYTER_PASSWORD": jtok})
        t0 = time.time()
        report.update(gpu=gpu, cost_per_hr=cost)
        log(f"pod {pod_id} cree ({gpu}, {cost} $/h)")
        for _ in range(60):
            try:
                api("GET", "contents?content=0", timeout=15, retries=1)
                break
            except Exception:
                time.sleep(10)
        else:
            raise RuntimeError("Jupyter n'a pas demarre")
        for d in (D, f"{D}/{nom}"):
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
        for f in paires:
            api("PUT", f"contents/{D}/{nom}/{f.name}", {"type": "file", "format": "base64", "content": base64.b64encode(f.read_bytes()).decode()}, timeout=300)
            api("PUT", f"contents/{D}/{nom}/{f.stem}.txt", {"type": "file", "format": "text", "content": f.with_suffix(".txt").read_text(encoding="utf-8")})
        script = (Path(__file__).resolve().parents[2] / "tools" / "train" / "train_zimage_lora.sh").read_text(encoding="utf-8")
        api("PUT", f"contents/{D}/train.sh", {"type": "file", "format": "text", "content": script})
        api("PUT", f"contents/{D}/run.sh", {"type": "file", "format": "text",
                                            "content": RUN % {"d": D, "nom": nom, "passages": int(lot.get("passages") or 30), "place": PLACE_MIN}})
        for x in ("fin", "run.log"):
            try:
                api("DELETE", f"contents/{D}/{x}", essais=1, retries=1)
            except Exception:
                pass
        log(f"{len(paires)} images deposees, entrainement lance ({int(lot.get('passages') or 30)} passages)")
        ordre = f"(nohup sh -c 'bash /workspace/{D}/run.sh > /workspace/{D}/run.log 2>&1; echo $? > /workspace/{D}/fin' >/dev/null 2>&1 &)\r"
        for _ in range(3):
            term = api("POST", "terminals")["name"]
            si.ws_envoyer(f"{pod_id}-8888.proxy.runpod.net", f"/terminals/websocket/{term}", H, json.dumps(["stdin", ordre]), _ctx)
            time.sleep(10)
            try:
                api("GET", f"contents/{D}/run.log?content=0", essais=3, retries=1)
                break
            except Exception:
                log("le script n'a pas demarre, nouvel essai")
        else:
            raise RuntimeError("le script n'a pas demarre sur le pod")
        import re
        code, journal, dit, vu = None, "", 0, ""
        while time.time() - t0 < delai * 60:
            time.sleep(20)
            try:
                journal = texte("run.log")
                for l in journal.splitlines():
                    if l.startswith(("PLACE", "ARRET", "TERMINE", "images legendees")) and l not in vu:
                        log(l[:120])
                        vu += l + "\n"
                pas = re.findall(r"(\d+)/(\d+) \[", journal[-3000:])
                if pas and time.time() - dit > 120:
                    dit = time.time()
                    log(f"entrainement : pas {pas[-1][0]} sur {pas[-1][1]}")
            except Exception:
                pass
            try:
                code = texte("fin").strip()
                break
            except Exception:
                pass
        if code != "0":
            for l in journal.strip().replace("\r", "\n").splitlines()[-12:]:
                log("  | " + l[:200])
            raise RuntimeError("delai depasse" if code is None else f"entrainement en echec (code {code})")
        log(f"entrainement termine ({round((time.time() - t0) / 60)} min)")
        c = Comfy(pod_id)
        c.wait_ready()
        fichier = next((f for f in c.models("loras") if Path(f.replace("\\", "/")).name == f"{nom}_comfy.safetensors"), "")
        if not fichier:
            raise RuntimeError("LoRA entrainee mais introuvable dans ComfyUI")
        report["lora"] = fichier
        for t in lot.get("essais") or []:
            e = {"name": t["sortie"]}
            report["shots"].append(e)
            try:
                d = time.time()
                w, h = t.get("taille") or [720, 1280]
                g = workflows.still_zimage(models, {**char, "lora_still_zimage": fichier}, t["prompt"], w, h, int(t["seed"]), f"ga_{t['sortie']}",
                                           loras=[], char_strength=float(t["force"]))
                (out / f"{t['sortie']}.png").write_bytes(c.fetch(c.run(g)[0]))
                log(f"{t['sortie']} : image ({round(time.time() - d)} s)")
            except Exception as x:
                e["error"] = str(x)[:300]
                log(f"{t['sortie']} : ECHEC image {e['error']}")
        if not report["shots"]:
            report["shots"].append({"name": nom})
    except Exception as x:
        report["shots"].append({"name": nom, "error": str(x)[:300]})
        log(f"ECHEC entrainement : {str(x)[:300]}")
    finally:
        code = _fin(report, t0, pod_id, True)
    return code
