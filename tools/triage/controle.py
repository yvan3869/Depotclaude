"""Controle des plans avant calcul : regles simples, sans GPU ni modele de langage.

Chaque remarque : {"scene": id ou "", "grave": bool, "msg": texte}. Une remarque grave annonce un
resultat rate a coup sur ; les autres sont des avertissements. Rien n'est bloque : le proprietaire tranche.
"""
import re

CIBLE = {1: 20}  # duree visee d'un temps, en secondes (accroche : court)
CLIP = 5         # duree d'un clip
FIXE = 2         # duree d'une image fixe au montage

_PLUSIEURS = re.compile(r"\b(and then|then|after that|before|afterwards|next)\b|;", re.I)
_CAMERA = re.compile(r"\b(camera (zooms|pans|moves|cuts|tilts|follows|pulls)|zoom(s|ing)? (in|out)|cut(s)? to|dolly|tracking shot)\b", re.I)
_RATES = [(re.compile(r"\bturn(s|ing)? (her back|around|away)\b", re.I), "se retourner"),
          (re.compile(r"\b(ties?|tying|puts?) (up )?her hair\b", re.I), "attacher ses cheveux"),
          (re.compile(r"\b(throws?|tilts?) her head back\b", re.I), "renverser la tête"),
          (re.compile(r"\b(bursts? (out )?laughing|laughs? out loud)\b", re.I), "éclater de rire"),
          (re.compile(r"\b(hand|hands|fingers) (over|across|in front of) her face\b", re.I), "passer la main devant le visage"),
          (re.compile(r"\b(puts? on|changes? (into|her)|gets? dressed)\b", re.I), "changer de vêtement")]
_TEL_EN_MAIN = re.compile(r"\b(hold(s|ing)?|with|grabs?|lifts?|raises?) (her|a|the) (smart)?phone\b|\bselfie\b|\bphone in (her )?hands?\b", re.I)
_PDV_OBJET = re.compile(r"\b(phone|camera)\b[^,.;]*\b(propped|leaning|placed|resting|standing|sitting|mounted|set (up|down)|filming|recording|"
                        r"on (a|the|her) (counter|table|desk|shelf|nightstand|dresser|floor|bed|stand|sink|windowsill))\b"
                        r"|\b(propped|leaning|mounted)\b[^,.;]*\b(phone|camera)\b|\btripod\b", re.I)
_NUIT = re.compile(r"\b(night|evening|dusk|candle\w*|lamp\w*|moonlight|dark outside)\b", re.I)
_JOUR = re.compile(r"\b(daylight|sunlight|sunny|morning|noon|midday|afternoon sun|sunbeam\w*)\b", re.I)
# Mots qui disent ce qu'elle porte ou ne porte plus (temps 2 a 4 : chaque image le dit, la fiche ne l'ajoute pas)
_TENUE = re.compile(r"\b(wear(s|ing)?|worn|dressed|undress\w*|naked|nude|topless|bottomless|bare\w*|lingerie|underwear|towel|bathrobe|robe|sheet|"
                    r"clothes|clothing|outfit|shirt|t-shirt|tee|top|bra|bralette|panties|thong|briefs|skirt|dress|jeans|pants|trousers|shorts|"
                    r"leggings|jacket|cardigan|hoodie|sweater|pullover|blouse|bikini|swimsuit|bodysuit|stockings|tights|socks|heels|"
                    r"unbuttoned|unzipped|stripped|nothing on)\b", re.I)


def tenue_dite(still):
    """Vrai si la description d'image dit quelque chose de la tenue."""
    return bool(_TENUE.search(still or ""))
_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿]")


def _phrases(t):
    return [x for x in re.split(r"(?<=[.!?])\s+", t.strip()) if x]


def _noms(txt):
    """Noms des LoRA d'une scene ("nom:0.6, autre")."""
    return [x.partition(":")[0] for x in str(txt or "").split(", ") if x]


def controle(p, temps, lib=None):
    """Remarques sur les scenes d'un temps du projet p (dictionnaire tel qu'enregistre).
    `lib` : {"cat": {nom du catalogue: fichier}, "volume": fichiers du volume ou None, "date": date de l'inventaire}."""
    sc = [s for s in p.get("scenes") or [] if s.get("temps", 1) == temps]
    c = p.get("continuite") or {}
    out = []

    def r(msg, s=None, grave=False):
        out.append({"scene": s["id"] if s else "", "grave": grave, "msg": msg})

    if not sc:
        return out
    normales = [s for s in sc if not s.get("libre")]
    if len(normales) > 1:
        vides = [lab for k, lab in (("lieu", "lieu"), ("tenue", "tenue")) if not c.get(k) and not (k == "tenue" and temps >= 2)]
        if vides:
            r(f"Fiche de continuité : {' et '.join(vides)} non rempli{'s' if len(vides) > 1 else ''}. "
              "Chaque image décrit alors son décor et sa tenue de son côté : ils changent d'une scène à l'autre.")
    if not c.get("pdv"):
        r("Point de vue non déclaré dans la fiche de continuité (téléphone posé, miroir, quelqu'un qui filme).")
    elif _PDV_OBJET.search(c["pdv"]):
        r("Point de vue : l'appareil est décrit comme un objet (posé, appuyé, sur un trépied, « filming her »). Le modèle le dessine "
          "alors dans l'image. Décrire la vue, pas l'appareil : « shot straight on at chest height on a phone ».")
    if temps == 1 and len(p.get("accroche") or "") > 44:
        r(f"Accroche de {len(p['accroche'])} caractères : au-delà de 44 elle ne tient plus en deux lignes lisibles en haut de l'image.")
    clips = [s for s in sc if s.get("motion")]
    duree = sum(s.get("duree") or CLIP for s in clips) + FIXE * (len(sc) - len(clips))
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
            if temps >= 2 and still and not continu and not tenue_dite(still):
                r("Tenue non décrite : à partir du temps 2 la fiche de continuité ne l'ajoute plus, parce qu'elle se défait d'une scène "
                  "à l'autre. Dire dans la scène ce qu'elle porte à cet instant" + (" ; sinon elle garde à peu près celle de l'image de référence."
                                                                                 if p.get("reference") else "."), s)
            if temps == 1 and c.get("tenue") and re.search(r"\bwearing\b", still, re.I):
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
        for nom in _noms(s.get("loras")) if lib else []:
            fichier = lib["cat"].get(nom) or (nom if nom.endswith(".safetensors") else "")
            tmin, lab = (lib.get("tmin") or {}).get(nom, (1, ""))
            if tmin > temps:
                r(f"LoRA « {nom} » (catégorie {lab}) : admise à partir du temps {tmin} seulement. La retirer de cette scène, "
                  "ou changer sa catégorie dans le hub.", s, True)
            bas = (lib.get("bas") or {}).get(nom)
            if bas and lib.get("volume") is not None and bas not in lib["volume"]:
                r(f"LoRA « {nom} » : {bas} n'est pas sur le volume (inventaire du {lib.get('date') or '?'}).", s, True)
            if not fichier:
                r(f"LoRA « {nom} » absente du catalogue : le pilote ne saura pas quel fichier charger. L'inscrire dans la bibliothèque de LoRA.", s, True)
            elif lib.get("volume") is not None and fichier not in lib["volume"]:
                r(f"LoRA « {nom} » : {fichier} n'est pas sur le volume (inventaire du {lib.get('date') or '?'}). "
                  "Le calcul s'arrêterait au démarrage du pod. La déposer par « pilot lora add » ou corriger la scène.", s, True)
        cran = int(s.get("cran") or 0)
        if cran and cran < haut:
            r(f"Progression : cran {cran} après un cran {haut}. La vidéo redescend.", s)
        haut = max(haut, cran)
    return out
