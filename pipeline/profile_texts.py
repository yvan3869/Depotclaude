"""Genere les textes de profil d'un personnage, en francais et en anglais.

    ANTHROPIC_API_KEY=... python pipeline/profile_texts.py [--bible persona/bible.yaml]
                                                           [--examples persona/profile_texts.md]
                                                           [--out persona/profile_texts_generated.md]

Produit : bio, messages automatiques (nouveau follower, nouvel abonne, premier message,
renouvellement, relance), fiche "Creator Personality" Fanvue complete (17 champs) et legendes.
Signale les informations absentes de la bible au lieu de les inventer. --dry-run affiche la
requete sans appeler l'API.
Independant du personnage : tout vient de la bible. Le fichier d'exemples, s'il existe,
sert de reference de ton. Les textes generes sont des propositions a relire avant usage.
"""
import argparse
import os
import sys
from pathlib import Path

import yaml

MODEL = os.environ.get("PROFILE_MODEL", "claude-opus-5-5")

FICHE_FIELDS = [
    "À propos de moi", "Mes passe-temps", "Mes animaux", "Mon statut relationnel",
    "Mes modifications corporelles", "Mes caractéristiques physiques",
    "Comment j'appelle mes fans (liste séparée par des virgules)", "Comment je salue mes fans",
    "Ma personnalité", "Mon style d'expression", "Mes emojis préférés",
    "Comment j'interagis avec mes fans réguliers", "Ce que j'aime", "Ce que je n'aime pas",
    "Mes médias préférés", "Mes plats préférés",
    "Ce que je ne suis pas prête à faire (liste séparée par des virgules)",
]

SYSTEM = """Tu ecris les textes de profil d'un personnage fictif, adulte, assume comme genere par IA,
pour une plateforme de createurs et pour ses reseaux sociaux.

Regles imperatives :
- Le personnage ne pretend jamais etre une personne reelle. La bio contient la mention IA.
- Ton suggestif et complice au maximum, jamais explicite ni vulgaire.
- Respecter la voix du personnage decrite dans la bible : tics de langage, autoderision, defauts.
- Chaque texte existe en francais (FR) et en anglais (EN). L'anglais est une adaptation
  naturelle, pas une traduction mot a mot ; les tics propres au personnage peuvent rester en francais.
- Rester concret : details de sa vie quotidienne tires de la bible, pas de formules generiques.
- Ne decrire que ce qui est visible sur les images du personnage : uniquement les signes physiques,
  tatouages, piercings et bijoux listes comme presents dans la bible. Tout ce qui figure dans le bloc
  "A NE PAS DECRIRE COMME EXISTANT" (elements futurs, retires ou non decides) ne doit jamais etre
  presente comme existant ; il peut au plus etre evoque comme une envie ou un projet.
- Ne rien inventer. Si la bible ne contient pas l'information necessaire a un champ ou a un texte,
  ecrire a la place "[INFORMATION MANQUANTE : ...]" en precisant quoi, et le reporter dans la
  section finale. Ne pas combler le manque par une supposition.

Format de sortie : Markdown, avec exactement ces sections, dans cet ordre :
## Bio (3 variantes, 150 caracteres maximum chacune)
## Nouveau follower (2 variantes)
## Nouvel abonne (2 variantes)
## Premier message (2 variantes)
## Renouvellement d'abonnement (2 variantes)
## Relance d'un abonne inactif (2 variantes)
## Fiche Creator Personality Fanvue
## Legendes de publications (10, courtes, variees selon les lieux et habitudes de la bible)
## Informations manquantes dans la bible
Dans les sections de messages, de bio et de legendes, donner chaque variante en FR puis en EN.

Section "Fiche Creator Personality Fanvue" : exactement les champs suivants, dans cet ordre, chacun
en sous-titre de niveau 3, avec le texte FR puis le texte EN, ecrits a la premiere personne :
{fields}
Regles propres a la fiche :
- "À propos de moi", "Ma personnalité" et "Mon style d'expression" disent chacun explicitement
  qu'elle est un personnage cree par IA, et "Mon style d'expression" precise qu'elle repond oui
  si on lui demande si elle est une IA.
- "Ce que je ne suis pas prête à faire" reprend les limites de la bible et exclut toujours ce
  qu'un personnage genere ne peut pas honorer : rencontre en personne, appel video ou audio en
  direct, echange de coordonnees ou de comptes personnels.
- Les deux champs de type liste sont de simples listes separees par des virgules, sans phrase.
- "Mes emojis préférés" : uniquement les emojis de la bible, colles, sans texte.

Section "Informations manquantes dans la bible" : liste a puces de chaque information absente
qui a empeche de remplir un champ, avec le champ concerne ; ecrire "Aucune" s'il n'y en a pas.""".replace(
    "{fields}", "\n".join(f"### {f}" for f in FICHE_FIELDS))


def split_bible(node):
    """Separe ce qui existe de ce qui est futur, retire ou non decide (cles *_future,
    removed_*, undecided), a tous les niveaux. Independant du personnage."""
    excluded = {}

    def walk(n, path):
        if not isinstance(n, dict):
            return n
        kept = {}
        for k, v in n.items():
            if k.endswith("_future") or k.startswith("removed_") or k == "undecided":
                excluded[".".join(path + [k])] = v
            else:
                kept[k] = walk(v, path + [k])
        return kept

    return walk(node, []), excluded


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bible", default="persona/bible.yaml")
    ap.add_argument("--examples", default="persona/profile_texts.md")
    ap.add_argument("--out", default="persona/profile_texts_generated.md")
    ap.add_argument("--dry-run", action="store_true", help="affiche la requete sans appeler l'API")
    a = ap.parse_args()

    bible = yaml.safe_load(Path(a.bible).read_text(encoding="utf-8"))
    bible.pop("accounts", None)  # aucun identifiant de compte dans la requete
    present, excluded = split_bible(bible)
    dump = lambda d: yaml.safe_dump(d, allow_unicode=True, sort_keys=False)
    user = "Bible du personnage (ce qui existe) :\n" + dump(present)
    if excluded:
        user += "\n\nA NE PAS DECRIRE COMME EXISTANT (futur, retire ou non decide) :\n" + dump(excluded)
    ex = Path(a.examples)
    if ex.exists():
        user += "\n\nTextes deja valides, a prendre comme reference de ton (ne pas les recopier) :\n"
        user += ex.read_text(encoding="utf-8")
    if a.dry_run:
        print(SYSTEM + "\n\n----- MESSAGE -----\n\n" + user)
        return 0

    import anthropic  # importe ici pour que --dry-run fonctionne sans le SDK

    client = anthropic.Anthropic()
    # Flux continu : la sortie est longue. Repli automatique sur un autre modele si la requete
    # est declinee par un classifieur.
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=32000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        thinking={"type": "adaptive"},
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        response = stream.get_final_message()
    if response.stop_reason == "refusal":
        print("Requete declinee par le modele ; aucun texte genere.", file=sys.stderr)
        return 1
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        print(f"Reponse vide (stop_reason={response.stop_reason}).", file=sys.stderr)
        return 1
    if response.stop_reason == "max_tokens":
        print("ATTENTION : sortie tronquee (limite de longueur atteinte).", file=sys.stderr)
    if "INFORMATION MANQUANTE" in text:
        print("ATTENTION : des informations manquent dans la bible, voir la derniere section.", file=sys.stderr)
    name = (bible.get("identity") or {}).get("name", "personnage")
    Path(a.out).write_text(f"# Textes de profil generes - {name}\n\n"
                           "Propositions a relire avant usage.\n\n" + text + "\n", encoding="utf-8")
    print(f"{a.out} ecrit ({len(text)} caracteres, modele {response.model})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
