"""Genere le planning de contenu de la semaine a partir de la bible.

Sortie : plan.json (une entree par jour : lieu, tenue, scenario, legende,
prompt visuel). Contenu suggestif uniquement ; les pistes payantes restent
des intentions a valider et a produire manuellement dans ComfyUI.
"""
import json
import os
import sys

import anthropic
import yaml

MODEL = os.environ.get("PLAN_MODEL", "claude-sonnet-5-5")

SYSTEM = (
    "Tu es showrunner d'un personnage fictif adulte assume comme IA. "
    "Tu proposes un planning hebdomadaire de 'moments de vie' coherents avec la bible. "
    "Chaque jour : lieu, tenue, scenario (3 plans), legende courte avec mention IA, "
    "prompt visuel pour la generation, canal (short soft ou page payante). "
    "Reste suggestif, jamais explicite. Reponds en JSON valide uniquement."
)


def main(path: str = "persona/bible.yaml") -> None:
    with open(path, encoding="utf-8") as f:
        bible = yaml.safe_load(f)
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(bible, ensure_ascii=False)}],
    )
    with open("plan.json", "w", encoding="utf-8") as f:
        f.write(msg.content[0].text)
    print("plan.json ecrit")


if __name__ == "__main__":
    main(*sys.argv[1:])
