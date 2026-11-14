"""Controle des plans avant calcul : regles simples, sans GPU ni modele de langage.

Chaque remarque : {"scene": id ou "", "grave": bool, "msg": texte}. Une remarque grave annonce un
resultat rate a coup sur ; les autres sont des avertissements. Rien n'est bloque : le proprietaire tranche.
"""
import re

CIBLE = {1: 20}  # duree visee d'un temps, en secondes (accroche : court)
CLIP = 5         # duree d'un clip

_PLUSIEURS = re.compile(r"\b(and then|then|after that|before|afterwards|next)\b|;", re.I)
_CAMERA = re.compile(r"\b(camera (zooms|pans|moves|cuts|tilts|follows|pulls)|zoom(s|ing)? (in|out)|cut(s)? to|dolly|tracking shot)\b", re.I)
_RATES = [(re.compile(r"\bturn(s|ing)? (her back|around|away)\b", re.I), "se retourner"),
          (re.compile(r"\b(ties?|tying|puts?) (up )?her hair\b", re.I), "attacher ses cheveux"),
          (re.compile(r"\b(throws?|tilts?) her head back\b", re.I), "renverser la tête"),
          (re.compile(r"\b(bursts? (out )?laughing|laughs? out loud)\b", re.I), "éclater de rire"),
          (re.compile(r"\b(hand|hands|fingers) (over|across|in front of) her face\b", re.I), "passer la main devant le visage"),
          (re.compile(r"\b(puts? on|changes? (into|her)|gets? dressed)\b", re.I), "changer de vêtement")]
_TEL_EN_MAIN = re.compile(r"\b(hold(s|ing)?|with|grabs?|lifts?|raises?) (her|a|the) (smart)?phone\b|\bselfie\b|\bphone in (her )?hands?\b", re.I)
_NUIT = re.compile(r"\b(night|evening|dusk|candle\w*|lamp\w*|moonlight|dark outside)\b", re.I)
_JOUR = re.compile(r"\b(daylight|sunlight|sunny|morning|noon|midday|afternoon sun|sunbeam\w*)\b", re.I)
_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿]")


def _phrases(t):
    return [x for x in re.split(r"(?<=[.!?])\s+", t.strip()) if x]


def controle(p, temps):
    """Remarques sur les scenes d'un temps du projet p (dictionnaire tel qu'enregistre)."""
    sc = [s for s in p.get("scenes") or [] if s.get("temps", 1) == temps]
    c = p.get("continuite") or {}
    out = []

    def r(msg, s=None, grave=False):
        out.append({"scene": s["id"] if s else "", "grave": grave, "msg": msg})

    if not sc:
        return out
    normales = [s for s in sc if not s.get("libre")]
    if len(normales) > 1:
        vides = [lab for k, lab in (("lieu", "lieu"), ("tenue", "tenue")) if not c.get(k)]
        if vides:
            r(f"Fiche de continuité : {' et '.join(vides)} non rempli{'s' if len(vides) > 1 else ''}. "
              "Chaque image décrit alors son décor et sa tenue de son côté : ils changent d'une scène à l'autre.")
    if not c.get("pdv"):
        r("Point de vue non déclaré dans la fiche de continuité (téléphone posé, miroir, quelqu'un qui filme).")
    clips = [s for s in sc if s.get("motion")]
    duree = sum(s.get("duree") or CLIP for s in clips) + 3 * (len(sc) - len(clips))
    if temps in CIBLE and duree > CIBLE[temps]:
        r(f"Durée estimée {duree:.0f} s pour {len(sc)} scènes : au-delà de {CIBLE[temps]} s pour ce temps. "
          "Retirer une scène ou raccourcir les plans au montage.")
    crans = [int(s.get("cran") or 0) for s in sc]
    if len(sc) > 1 and not any(crans):
        r("Progression non renseignée : donner un cran de 1 à 5 à chaque scène pour vérifier que la vidéo monte.")
    elif not all(crans):
        r(f"Progression : cran non renseigné sur {crans.count(0)} scène(s).")
    elif len(sc) > 1 and max(crans) == min(crans):
        r("Progression plate : toutes les scènes ont le même cran.")
    tel = bool(re.search(r"phone", c.get("pdv") or "", re.I)) and not re.search(r"mirror", c.get("pdv") or "", re.I)
    nuit_f, jour_f = (bool(rx.search(f"{c.get('lumiere', '')} {c.get('lieu', '')}")) for rx in (_NUIT, _JOUR))
    suite, haut = 0, 0
    for i, s in enumerate(sc):
        still, motion, texte = s.get("still") or "", s.get("motion") or "", s.get("texte") or ""
        continu = i > 0 and s.get("raccord") == "continu"
        if not still and not continu:
            r("Pas de description d'image : la scène ne peut pas être produite.", s, True)
        if continu and not sc[i - 1].get("motion"):
            r("Raccord continu impossible : la scène précédente n'a pas de mouvement, donc pas de clip à prolonger.", s, True)
        if i > 0 and s.get("raccord") == "arrivee" and not sc[i - 1].get("motion"):
            r("Raccord d'arrivée sans effet : la scène précédente n'a pas de mouvement.", s)
        suite = suite + 1 if continu else 0
        if suite == 3:
            r("Trois scènes continues de suite : les couleurs et le visage dérivent d'un clip à l'autre. Remettre une coupe.", s)
        if i == 0 and temps == 1:
            if not motion:
                r("La première scène n'a pas de mouvement : rien ne se passe dans la première seconde.", s, True)
            if not texte and not p.get("accroche"):
                r("Pas de texte d'accroche sur la première scène : la vidéo doit se comprendre sans le son.", s)
        if motion:
            if len(_phrases(motion)) > 1 or _PLUSIEURS.search(motion):
                r("Plusieurs gestes dans un clip de 5 s : le second est rarement exécuté. "
                  "Un geste par scène ; le suivant va dans une scène en raccord continu.", s)
            if _CAMERA.search(motion):
                r("Mouvement de caméra demandé : le modèle le rend mal. Changer de cadrage se fait par une nouvelle scène.", s)
            for rx, nom in _RATES:
                if rx.search(motion):
                    r(f"Geste qui rate souvent : {nom}.", s)
        if not s.get("libre"):
            if c.get("tenue") and re.search(r"\bwearing\b", still, re.I):
                r("La tenue est décrite dans la scène et dans la fiche de continuité : le modèle mélange les deux. "
                  "La retirer de la scène, ou cocher « Scène libre » si la tenue change vraiment.", s)
            if (nuit_f and _JOUR.search(still)) or (jour_f and _NUIT.search(still)):
                r("Heure incohérente : la scène et la fiche de continuité ne disent pas le même moment de la journée.", s)
        if tel and _TEL_EN_MAIN.search(f"{still} {motion}"):
            r("Le point de vue déclaré est un téléphone qui filme : il ne peut pas être aussi dans sa main.", s)
        if len(texte.split()) > 7:
            r(f"Texte à l'écran de {len(texte.split())} mots : illisible en 5 s (7 au plus).", s)
        if _EMOJI.search(texte):
            r("Emoji dans le texte à l'écran : la police de montage ne l'affiche pas.", s)
        cran = int(s.get("cran") or 0)
        if cran and cran < haut:
            r(f"Progression : cran {cran} après un cran {haut}. La vidéo redescend.", s)
        haut = max(haut, cran)
    return out
