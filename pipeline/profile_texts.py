"""Genere les textes de profil d'un personnage, en francais et en anglais.

    ANTHROPIC_API_KEY=... python pipeline/profile_texts.py [--bible persona/bible.yaml]
                                                           [--examples persona/profile_texts.md]
                                                           [--out persona/profile_texts_generated.md]

Produit : bio, messages automatiques (nouveau follower, nouvel abonne, premier message,
renouvellement, relance), fiche "Creator Personality" et legendes de publications.
Independant du personnage : tout vient de la bible. Le fichier d'exemples, s'il existe,
sert de reference de ton. Les textes generes sont des propositions a relire avant usage.
"""
import argparse
import os
import sys
from pathlib import Path

import anthropic
import yaml

MODEL = os.environ.get("PROFILE_MODEL", "claude-opus-5-5")

SYSTEM = """Tu ecris les textes de profil d'un personnage fictif, adulte, assume comme genere par IA,
pour une plateforme de createurs et pour ses reseaux sociaux.

Regles imperatives :
- Le personnage ne pretend jamais etre une personne reelle. La bio contient la mention IA.
- Ton suggestif et complice au maximum, jamais explicite ni vulgaire.
- Respecter la voix du personnage decrite dans la bible : tics de langage, autoderision, defauts.
- Chaque texte existe en francais (FR) et en anglais (EN). L'anglais est une adaptation
  naturelle, pas une traduction mot a mot ; les tics propres au personnage peuvent rester en francais.
- Rester concret : details de sa vie quotidienne tires de la bible, pas de formules generiques.

Format de sortie : Markdown, avec exactement ces sections :
## Bio (3 variantes, 150 caracteres maximum chacune)
## Nouveau follower (2 variantes)
## Nouvel abonne (2 variantes)
## Premier message (2 variantes)
## Renouvellement d'abonnement (2 variantes)
## Relance d'un abonne inactif (2 variantes)
## Creator Personality (fiche a coller dans l'outil de messagerie : ton, sujets, limites, exemples de repliques)
## Legendes de publications (10, courtes, variees : studio, cuisine, appartement, sorties)
Dans chaque section, donner chaque variante en FR puis en EN."""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bible", default="persona/bible.yaml")
    ap.add_argument("--examples", default="persona/profile_texts.md")
    ap.add_argument("--out", default="persona/profile_texts_generated.md")
    a = ap.parse_args()

    bible = yaml.safe_load(Path(a.bible).read_text(encoding="utf-8"))
    bible.pop("accounts", None)  # aucun identifiant de compte dans la requete
    user = "Bible du personnage :\n" + yaml.safe_dump(bible, allow_unicode=True, sort_keys=False)
    ex = Path(a.examples)
    if ex.exists():
        user += "\n\nTextes deja valides, a prendre comme reference de ton (ne pas les recopier) :\n"
        user += ex.read_text(encoding="utf-8")

    client = anthropic.Anthropic()
    # Repli automatique sur un autre modele si la requete est declinee par un classifieur.
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        thinking={"type": "adaptive"},
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    if response.stop_reason == "refusal":
        print("Requete declinee par le modele ; aucun texte genere.", file=sys.stderr)
        return 1
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        print(f"Reponse vide (stop_reason={response.stop_reason}).", file=sys.stderr)
        return 1
    name = (bible.get("identity") or {}).get("name", "personnage")
    Path(a.out).write_text(f"# Textes de profil generes - {name}\n\n"
                           "Propositions a relire avant usage.\n\n" + text + "\n", encoding="utf-8")
    print(f"{a.out} ecrit ({len(text)} caracteres, modele {response.model})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
