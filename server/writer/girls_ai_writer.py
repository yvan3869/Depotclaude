#!/usr/bin/env python3
"""Redacteur IA de l'atelier (service girls-ai-writer, sur le serveur, hors conteneur).

L'atelier depose ses demandes dans data/ecriture/<id>.req.json ({"systeme", "demande"}). Ce service
les passe a Claude Code en mode non interactif, sans aucun outil ni connecteur (`claude -p --tools ""
--strict-mcp-config`), et ecrit la reponse dans <id>.res.txt, ou l'erreur dans <id>.err.txt. Une demande peut
porter des images ("images" : [{"scene", "jpeg" en base64}], relecture des images d'un projet) : elles sont
jointes au message lui-meme, toujours sans outil, donc sans aucune lecture de fichier. Il utilise l'abonnement Claude du
compte qui le fait tourner : aucune cle dans le depot. Le fichier redacteur.vivant, touche toutes
les dix secondes, dit a l'atelier que le service repond ; sans lui, l'atelier passe au redacteur
de secours.

  python3 girls_ai_writer.py <dossier data/ecriture>
"""
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

MODELE = os.environ.get("WRITER_MODEL", "sonnet")
DELAI_S = int(os.environ.get("WRITER_TIMEOUT_S", "240"))


def battre(d):
    while True:
        try:
            (d / "redacteur.vivant").touch()
        except OSError:
            pass
        time.sleep(10)


def rediger(claude, travail, req):
    # --strict-mcp-config : sans lui, les connecteurs du compte sont charges a chaque demande (des centaines de milliers de jetons)
    cmd = [claude, "-p", "--tools", "", "--strict-mcp-config", "--no-session-persistence", "--model", MODELE, "--system-prompt", req["systeme"]]
    if not req.get("images"):
        r = subprocess.run(cmd, input=req["demande"], capture_output=True, text=True, timeout=DELAI_S, cwd=travail)
        if r.returncode or not r.stdout.strip():
            raise RuntimeError((r.stderr or r.stdout or "réponse vide").strip()[-400:])
        return r.stdout
    contenu = []
    for im in req["images"]:
        contenu += [{"type": "text", "text": f"Image de la scène {im['scene']} :"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": im["jpeg"]}}]
    contenu.append({"type": "text", "text": req["demande"]})
    msg = json.dumps({"type": "user", "message": {"role": "user", "content": contenu}})
    r = subprocess.run(cmd + ["--input-format", "stream-json", "--output-format", "stream-json", "--verbose"],
                       input=msg + "\n", capture_output=True, text=True, timeout=DELAI_S, cwd=travail)
    for ligne in reversed(r.stdout.splitlines()):
        try:
            e = json.loads(ligne)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("type") == "result":
            if e.get("is_error") or not str(e.get("result") or "").strip():
                break
            return e["result"]
    raise RuntimeError((r.stderr or r.stdout or "réponse vide").strip()[-400:])


def main():
    d = Path(sys.argv[1])
    claude = shutil.which("claude") or str(Path.home() / ".local/bin/claude")
    travail = Path.home() / ".cache" / "girls-ai-writer"  # dossier vide : aucun contexte de projet charge
    travail.mkdir(parents=True, exist_ok=True)
    while not d.is_dir():  # cree par l'atelier a son demarrage
        time.sleep(5)
    threading.Thread(target=battre, args=(d,), daemon=True).start()
    while True:
        for f in sorted(d.glob("*.req.json")):
            rid = f.name[:-9]
            res, err = d / f"{rid}.res.txt", d / f"{rid}.err.txt"
            if res.exists() or err.exists():
                if time.time() - f.stat().st_mtime > 86400:  # reponse jamais relue : menage
                    for x in (f, res, err):
                        x.unlink(missing_ok=True)
                continue
            try:
                out = rediger(claude, travail, json.loads(f.read_text(encoding="utf-8")))
                tmp = d / f"{rid}.tmp"
                tmp.write_text(out, encoding="utf-8")
                tmp.replace(res)
                print(f"{rid} : écrit ({len(out)} caractères)", flush=True)
            except FileNotFoundError:
                continue  # demande retiree entre-temps
            except Exception as e:
                err.write_text(str(e)[:400] or type(e).__name__, encoding="utf-8")
                print(f"{rid} : erreur {str(e)[:200]}", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
