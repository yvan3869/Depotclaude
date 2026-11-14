#!/usr/bin/env python3
"""Redacteur IA de l'atelier (service girls-ai-writer, sur le serveur, hors conteneur).

L'atelier depose ses demandes dans data/ecriture/<id>.req.json ({"systeme", "demande"}). Ce service
les passe a Claude Code en mode non interactif, sans aucun outil (`claude -p --tools ""`), et ecrit
la reponse dans <id>.res.txt, ou l'erreur dans <id>.err.txt. Il utilise l'abonnement Claude du
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
    r = subprocess.run([claude, "-p", "--tools", "", "--model", MODELE, "--system-prompt", req["systeme"]],
                       input=req["demande"], capture_output=True, text=True, timeout=DELAI_S, cwd=travail)
    if r.returncode or not r.stdout.strip():
        raise RuntimeError((r.stderr or r.stdout or "réponse vide").strip()[-400:])
    return r.stdout


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
