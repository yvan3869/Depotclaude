"""Atelier du personnage : sa bibliotheque d'images. Une image par lieu (la piece vide) et par tenue (a plat sur fond
blanc), creees d'apres les lignes de sa fiche ; ses planches (photos d'elle, pour entrainer sa LoRA) ; ses LoRA
entrainees et leurs essais. Les lignes restent dans la fiche ("lieux", "tenues") : ici il n'y a que les images et les
choix. Tout est range dans data/personnages/<slug>/ ; le nom d'un fichier dit ce qu'il est :
l_<cle>_<tirage>.png lieu, t_<cle>_<tirage>.png tenue, p_<cle>_<tirage>.png tenue portee (cabine d'essayage),
n_1.png elle en tenue neutre (depart de la cabine), v_<tirage>.png portrait, c_<serie>_<rang>.png planche,
e_<version>_<force>_<rang>.png essai d'une LoRA. Les calculs passent par le pilote (server/pilot/perso.py)."""
import random
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

GENRES = ("tenue", "dessous")
FIN_ANC = ", smartphone photo, natural skin texture"  # fin des textes d'avant le 18/11/2026 (relue pour les anciennes series)
PEAU = "natural skin texture, visible pores, small skin imperfections"  # sans cela la peau sort lisse
FIN = f", smartphone photo, {PEAU}"
# Planches : cadrage et pose, puis fond. Varies expres : une LoRA entrainee sur un seul fond ou un seul cadrage les recopie.
CADRES = (
    "close-up portrait, eye-level, front view, she looks at the camera, neutral face",
    "close-up portrait, eye-level, three-quarter view, soft smile, looking at the camera",
    "close-up portrait, eye-level, profile view, looking ahead",
    "close-up portrait, slightly high angle, she laughs, looking at the camera",
    "medium close-up, eye-level, front view, head slightly tilted, looking at the camera",
    "medium close-up, slightly low angle, three-quarter view, looking away",
    "medium shot, eye-level, front view, she stands, arms crossed, looking at the camera",
    "medium shot, eye-level, three-quarter view, one hand in her hair, looking at the camera",
    "medium shot, eye-level, she sits on a chair, hands on her knees, looking at the camera",
    "medium shot, eye-level, profile view, she stands, looking ahead",
    "medium shot, eye-level, back view, she looks over her shoulder at the camera",
    "medium shot, slightly high angle, she sits cross-legged, looking up at the camera",
    "medium shot, eye-level, she leans against a wall, hands in her pockets, looking away",
    "medium shot, eye-level, front view, both hands on her hips, big smile",
    "full-body shot, eye-level, front view, she stands facing the camera, arms relaxed along her body",
    "full-body shot, eye-level, three-quarter view, she stands, one hand on her hip",
    "full-body shot, eye-level, profile view, she walks",
    "full-body shot, eye-level, back view, she stands, looking over her shoulder",
    "full-body shot, eye-level, she sits on the floor, knees up, arms around her knees",
    "full-body shot, slightly low angle, she stands, hands in her hair",
    "full-body shot, eye-level, she sits on a stool, legs crossed, looking at the camera",
    "full-body shot, eye-level, she leans on a table, looking at the camera",
    "medium shot, eye-level, she lies on her side on a bed, head on her hand, looking at the camera",
    "medium shot, high angle, she lies on her back on a bed, hair spread, looking at the camera",
)
FONDS = (
    "in a bright living room with a beige sofa, soft natural daylight",
    "in a bedroom with white sheets, morning light from a window",
    "in a kitchen with white tiles, daylight",
    "on a city street, overcast daylight",
    "in a park with green trees, afternoon sun",
    "in front of a plain light grey wall, soft studio light",
    "in a cafe with wooden tables, warm light",
    "on a balcony at sunset, warm golden light",
)
# Portraits de depart : a description egale, le modele rend presque le meme visage d'un tirage a l'autre. Chaque portrait
# tire donc au sort un choix par trait (ce que la fiche ne dit pas), place en tete de la description pour qu'il pese.
# Chaque ligne : (mots de la fiche qui tranchent deja ce trait, variantes). Un trait dont la fiche parle n'est pas tire au sort.
TRAITS = (
    (r"\bface\b", ("oval face", "heart-shaped face", "square face", "long narrow face", "round face", "diamond-shaped face", "angular face", "broad face")),
    (r"forehead", ("very high forehead", "low forehead", "wide forehead", "narrow forehead")),
    (r"(wide|close)-set|far apart", ("eyes set far apart", "eyes set close together", "evenly spaced eyes")),
    (r"almond|round eyes|upturned|downturned|deep-set|(big|large|small|narrow) eyes", (
        "very large round eyes", "narrow almond eyes", "small deep-set eyes", "upturned cat-like eyes", "downturned sleepy eyes", "big doe eyes",
        "long narrow eyes")),
    (r"eyelid|hooded|lash", ("heavy hooded eyelids", "wide open eyelids with a visible crease", "long thick lashes", "short sparse lashes",
                             "puffy lower eyelids", "faint shadows under the eyes")),
    (r"brow", ("thick straight eyebrows", "thin arched eyebrows", "bushy eyebrows", "soft rounded eyebrows", "high angular eyebrows", "low flat eyebrows")),
    (r"nose", ("small button nose", "long straight nose", "wide nose", "aquiline nose", "upturned nose", "narrow pointed nose", "nose with a low bridge",
               "slightly crooked nose")),
    (r"lips?\b", ("very full pouty lips", "thin lips", "full lower lip and thin upper lip", "heavy upper lip", "medium lips with a pronounced cupid's bow",
                    "plump heart-shaped lips")),
    (r"mouth", ("wide mouth", "small narrow mouth", "mouth with upturned corners", "mouth with downturned corners")),
    (r"teeth|smile|dimple", ("a small gap between her front teeth", "dimples when she smiles", "a slightly crooked smile", "a wide toothy smile",
                             "slightly prominent front teeth", "a closed-lip smile")),
    (r"jaw|chin", ("strong jaw", "soft jawline", "pointed chin", "wide chin", "dimpled chin", "small receding chin")),
    (r"cheek", ("prominent cheekbones", "full cheeks", "hollow cheeks", "flat cheeks")),
    (r"freckle|mole|beauty mark|birthmark|scar", ("a beauty mark above her lip", "a mole on her cheek", "a few faint freckles across the nose",
                                                  "two small moles on her neck", "clear even skin", "a beauty mark near her eye",
                                                  "a tiny scar through one eyebrow", "slightly rosy cheeks")),
    (r"\bears?\b", ("small ears close to the head", "slightly protruding ears", "long earlobes")),
    (r"neck", ("long thin neck", "short neck", "strong neck")),
    (r"bangs|fringe|parted|parting|ponytail|\bbun\b|braid|bob\b|pixie|updo", ("hair parted in the middle", "hair parted on the side", "wispy curtain bangs",
                                                                              "straight blunt bangs", "hair tucked behind her ears", "hair pulled back in a low ponytail",
                                                                              "hair in a loose messy bun", "hair swept to one side")),
    (r"symmetr|\blook\b", ("girl-next-door look", "striking fashion-model look", "sporty tomboyish look", "soft romantic look", "sharp elegant look",
                           "quirky unconventional look", "slightly asymmetric face", "mature serious look")),
)


# Un prenom invente deplace aussi le visage que le modele dessine, sans rien contredire dans la fiche.
PRENOMS = ("Maelle", "Ingrid", "Chiara", "Salome", "Odile", "Tamsin", "Liv", "Rosalind", "Anouk", "Greta", "Noor", "Bianca", "Sunniva", "Mirela",
           "Oriane", "Thea", "Zelie", "Marit", "Ottilie", "Carmen", "Yael", "Linnea", "Capucine", "Dagny")


# Mots qui signalent une partie de description sur le corps : ecartee des portraits (voir _prefixe_visage).
CORPS_MOTS = re.compile(r"breast|bust|chest|boob|tits|cleavage|nipple|areola|bod(y|ied)|figure|silhouette|physique|build\b|frame\b|hips?\b|waist|butt|bottom\b|\bass\b|"
                        r"glute|legs?\b|thigh|stomach|belly|abs\b|curv|slim|slender|petite|athletic|toned|hourglass|voluptuous|thick|skinny|\btall\b|\bshort\b(?! hair)|"
                        r"\bcm\b|height|shoulders|arms?\b|\bcup\b", re.I)


def traits(s, fiche=""):
    """Traits tires au sort pour le portrait numero s ; ceux dont la fiche parle deja sont laisses a la fiche."""
    r = random.Random(7919 * s)
    tires = [r.choice(v) for _, v in TRAITS]      # tirage complet d'abord : le meme numero donne les memes traits quelle que soit la fiche
    return f"{r.choice(PRENOMS)}, a woman with a distinctive face: " + ", ".join(x for (m, _), x in zip(TRAITS, tires) if not re.search(m, fiche, re.I))


# Corps de reference (personnage sans LoRA) : comme pour le visage, chaque essai tire au sort ce que la fiche ne dit pas.
# La taille de la poitrine vient de la fiche : seule sa forme varie. Liste « _F » : la forme seule, quand la fiche donne deja la taille.
BUSTES = ("round high breasts", "teardrop-shaped breasts", "wide-set breasts", "breasts set close together", "natural slightly low breasts", "firm conical breasts",
          "breasts fuller at the bottom", "perky upturned breasts", "soft natural breasts with a gentle slope", "asymmetric natural breasts")
TAILLES = ("narrow waist", "straight waist", "soft stomach", "flat toned stomach", "long torso", "short torso")
FESSES = ("small firm buttocks", "small flat buttocks", "round high buttocks", "round full buttocks", "heart-shaped buttocks", "wide full buttocks",
          "athletic muscular buttocks", "large round buttocks")
FESSES_F = ("round high buttocks", "heart-shaped buttocks", "square buttocks", "bubble-shaped buttocks", "soft low buttocks", "athletic muscular buttocks")
HANCHES = ("narrow hips", "wide hips", "hip dips", "smooth rounded hips", "straight hips")
# Ce qui parle du visage dans une fiche : retire des images de dos, sinon le modele la retourne pour le montrer.
VISAGE_MOTS = re.compile(r"\bface\b|faced\b|eyes?\b|eyed\b|eyebrow|brows?\b|lash|eyelid|nose|nostril|lips?\b|lipped|mouth|smile|teeth|tooth|jaw|chin\b|cheek|"
                         r"forehead|dimple|makeup|lipstick|gaze|look(s|ing)?\b|expression", re.I)
CORPS_TENUE = "she wears only a plain fitted grey sports bra and matching briefs, bare stomach, bare legs, barefoot"
CORPS_POSE = "in front of a plain light grey wall, soft even studio light, neutral face"
CORPS_POSE_DOS = "in front of a plain light grey wall, soft even studio light"
ANGLES = (("de profil", "profile view from her left side, she stands straight, arms slightly away from her body, looking ahead"),
          ("de trois quarts face", "three-quarter front view, she stands straight, arms slightly away from her body, looking at the camera"),
          ("de trois quarts dos", "three-quarter back view, she stands straight, arms slightly away from her body, head turned away"),
          ("de profil, autre côté", "profile view from her right side, she stands straight, arms slightly away from her body, looking ahead"))


def traits_corps(s, fiche, dos=False):
    """Traits du corps numero s (de face : buste et taille ; de dos : fesses et hanches), toujours les memes pour un numero donne."""
    r = random.Random(104729 * s + dos)
    if dos:
        return f"{r.choice(FESSES_F if re.search(r'butt|hips|bottom|glute', fiche, re.I) else FESSES)}, {r.choice(HANCHES)}"
    return f"{r.choice(BUSTES)}, {r.choice(TAILLES)}"


def _de_dos(chemin):
    """Image du corps ou la tete ne montre pas de visage : le dos, et l'angle de trois quarts dos."""
    m = re.fullmatch(r"([kda])_(\d+)\.png", Path(chemin).name)
    return bool(m) and (m[1] == "d" or (m[1] == "a" and (int(m[2]) - 1) % 4 == 2))


# Mots d'allure : la taille et la silhouette d'ensemble, a part du detail du corps.
ALLURE_MOTS = re.compile(r"\btall\b|\bshort\b(?! hair)|petite|\bcm\b|height|slim|slender|skinny|athletic|toned|muscular|sporty|curv|hourglass|voluptuous|"
                         r"thick\b|chubby|plump|bod(y|ied)|figure|silhouette|physique|build\b|frame\b|posture|arched|sexy|elegant|graceful", re.I)
DETAIL_CORPS = re.compile(r"breast|bust|chest|boob|tits|cleavage|nipple|areola|hips?\b|waist|butt|bottom\b|\bass\b|glute|legs?\b|thigh|stomach|belly|abs\b|"
                          r"shoulders|arms?\b|\bcup\b", re.I)


def ranger(texte, corps=""):
    """Une description d'un seul bloc repartie dans les quatre cases de la fiche, aux mots : une proposition que le proprietaire corrige.
    Un morceau « a latina woman with brown eyes and long black hair » est coupe : les yeux au visage, le reste a l'identite."""
    o = {"identite": [], "allure": [], "visage": [], "corps": [x.strip() for x in corps.split(",") if x.strip()]}
    for bout in (x.strip() for x in texte.split(",") if x.strip()):
        tete, *reste = re.split(r"\s+with\s+", bout, maxsplit=1)
        for i, x in enumerate([tete] + (re.split(r"\s+and\s+", reste[0]) if reste else [])):
            k = "visage" if VISAGE_MOTS.search(x) else "corps" if DETAIL_CORPS.search(x) else "allure" if ALLURE_MOTS.search(x) and not re.search(r"year|woman|hair", x) else "identite"
            if k == "identite" and i and o["identite"] and o["identite"][-1].startswith(tete):
                o["identite"][-1] += (" and " if " with " in o["identite"][-1] else " with ") + x  # reste attache a « a ... woman with »
            elif x not in o[k]:
                o[k].append(x)
    return {k: ", ".join(v) for k, v in o.items()}


def sans_visage(fiche):
    """La fiche sans ce qui decrit le visage (yeux, bouche, nez...) : restent l'age, l'origine, la peau, les cheveux et le corps.
    Un morceau du type « a latina woman with brown eyes and long black hair » ne perd que « brown eyes »."""
    out = []
    for x in (y.strip() for y in fiche.split(",")):
        if x and VISAGE_MOTS.search(x):
            m = [z for z in re.split(r"\s+(?:with|and)\s+", x) if not VISAGE_MOTS.search(z)]
            x = (m[0] + (" with " + " and ".join(m[1:]) if m[1:] else "")) if m else ""
        if x:
            out.append(x)
    return ", ".join(out)


# Angles dessines par Z-Image (LoRA du corps choisies) : la vue en tete du texte, comme pour le dos. Meme ordre que ANGLES.
ANGLES_Z = ("side view, full profile, she stands sideways to the camera, her body and her face turned toward the left edge of the picture, looking straight ahead",
            "side view, slightly turned toward the camera: she stands sideways, her body turned toward the left edge of the picture, we see her side, "
            "one hip and part of her chest and stomach, her face in three-quarter profile, looking toward the left edge of the picture",
            "rear three-quarter view, her whole body is rotated halfway between back and profile, we see her back and the side of one hip and one breast, "
            "her feet point toward the far left corner, one shoulder closer to the camera, her face is turned away and not visible",
            "side view, full profile, she stands sideways to the camera, her body and her face turned toward the right edge of the picture, looking straight ahead")


def texte_angle(k, fiche, corps, tenue):
    """Texte Z-Image de l'angle k : la vue d'abord, puis elle (sans son visage de trois quarts dos), puis son corps (celui de la face et du dos retenus)."""
    return (f"full-body photo of a woman, {ANGLES_Z[k]}. {fiche}, {corps}, vertical full-body shot from head to feet, eye-level, she stands straight, "
            f"arms slightly away from her body, feet slightly apart, {CORPS_POSE if k != 2 else CORPS_POSE_DOS}, {tenue}, only one woman in the picture{FIN}")


def _lora_force(x):
    """« nom:0.8 » devient {name, strength} pour le pilote ; « nom » seul garde la force du catalogue."""
    n, _, f = str(x).rpartition(":")
    try:
        return {"name": n, "strength": max(0.0, min(2.0, float(f)))} if n else str(x)
    except ValueError:
        return str(x)


def taille_corps(s):
    """La taille tiree pour le corps de face numero s (meme tirage que traits_corps)."""
    r = random.Random(104729 * s)
    r.choice(BUSTES)
    return r.choice(TAILLES)


ESSAIS = ("medium shot, eye-level, front view, she stands, soft smile, looking at the camera, in a bright living room, wearing a white t-shirt and jeans",
          "full-body shot, eye-level, three-quarter view, she stands, one hand on her hip, on a city street, wearing a black dress")
FORCES = (1.0, 1.3, 1.6)
# Galerie d'expressions : un visage par expression, tire du portrait de depart (ou de la LoRA). Tous publics.
# Elle montre ce que le visage sait faire, nourrit l'entrainement de la LoRA (un jeu sans expressions donne un visage fige)
# et donne au scenariste les mots anglais qui marchent. Celles de la fiche du personnage ("expressions") passent en tete.
EXPRESSIONS = (("Neutre", "neutral relaxed face, lips closed, looking at the camera"),
               ("Sourire doux", "soft closed-lip smile, looking at the camera"),
               ("Grand sourire", "big bright smile showing her teeth, looking at the camera"),
               ("Rire", "laughing out loud, eyes half closed, head slightly tilted back"),
               ("Clin d'œil", "playful wink with one eye closed, slight smile"),
               ("Sourire en coin", "smirk with one corner of her mouth raised, knowing look at the camera"),
               ("Surprise", "surprised, eyebrows raised, mouth slightly open"),
               ("Moue", "pouting, lips pushed forward, looking at the camera"),
               ("Pensive", "thoughtful, looking away to the side, lips closed"),
               ("Timide", "shy smile, looking down, chin slightly lowered"),
               ("Sérieuse", "serious determined look straight into the camera, lips closed"),
               ("Agacée", "annoyed, one eyebrow raised, lips pressed together"),
               ("Triste", "sad, eyes lowered, corners of her mouth down"),
               ("Yeux fermés", "eyes closed, peaceful face, slight smile"),
               # Suggestives (visage seul, habillee)
               ("Tire la langue", "playfully sticking her tongue out, eyes smiling, looking at the camera"),
               ("Se mord la lèvre", "biting her lower lip, sultry half-lidded eyes, looking at the camera"),
               ("Regard de braise", "seductive smoldering gaze, lips slightly parted, looking at the camera"),
               ("Regard par en dessous", "chin lowered, looking up through her lashes, teasing half smile"),
               ("Bisou", "blowing a kiss, lips puckered, eyes half closed"),
               ("Langue sur la lèvre", "tip of her tongue touching her upper lip, mischievous look at the camera"),
               ("Doigt sur la lèvre", "one fingertip resting on her lower lip, lips slightly parted, flirty look at the camera"))
VUES = ("front view", "three-quarter view", "front view, head slightly tilted")
# Cabine d'essayage : poses proposees (nom affiche, texte pour le modele).
POSES = (("Debout, de face", "full-body shot, eye-level, front view, she stands facing the camera, arms relaxed along her body"),
         ("Debout, de trois quarts", "full-body shot, eye-level, three-quarter view, she stands, one hand on her hip"),
         ("De dos, regard par-dessus l'épaule", "full-body shot, eye-level, back view, she stands, looking over her shoulder at the camera"),
         ("Assise", "full-body shot, eye-level, she sits on a stool, legs crossed, looking at the camera"),
         ("Buste", "medium shot, eye-level, front view, she stands, looking at the camera, soft smile"))
NEUTRE = ("vertical full-body shot, eye-level, front view, she stands facing the camera, arms relaxed along her body, "
          "in front of a plain light grey wall, wearing a white t-shirt and jeans, soft studio light")


def _s(x, n=300):
    return re.sub(r"\s+", " ", str(x or "")).strip()[:n]


def cle(x):
    """Cle d'une ligne de la fiche : sa partie anglaise, sans casse ni ponctuation de fin (la meme que dans l'atelier)."""
    return _s(str(x or "").rpartition("|")[2]).strip(" .,").lower()


def h8(x):
    return hashlib.sha1(re.sub(r"^wearing ", "", cle(x)).encode()).hexdigest()[:8]  # la fiche de continuite dit "wearing a ..."


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _sans_elle(en):
    """Un lieu decrit pour une scene (« in her kitchen », « rooftops behind her ») devient un lieu vide : toute mention
    d'elle appelle une personne dans l'image (essai du 15/11/2026 : 3 images sur 14 avec quelqu'un)."""
    t = re.sub(r"^(in|on|at|inside) ", "", en)
    t = re.sub(r"\b(in front of|front of) ", "", t)
    t = re.sub(r"\s*\b(behind|around|next to|beside|above|below|near) (her|him|them)\b", "", t)
    t = re.sub(r"\b(her|his|their)\b", "the", t)
    return re.sub(r"^the ", "a ", t).strip()


NOMS_CALCUL = {"lieux": "Images des lieux", "tenues": "Images des tenues", "import": "Import d'images", "essayage": "Essayage", "visage": "Portraits", "corps": "Corps de référence",
               "expressions": "Expressions", "planches": "Planches", "banc": "Banc d'essai", "entrainement": "Entraînement de la LoRA"}


class Biblio:
    def __init__(self, at):
        self.at, self.job = at, None  # job : {"slug", "quoi", "log", "n"}, dernier calcul lance d'ici

    def dir(self, slug):
        if not re.fullmatch(r"[a-z0-9_]{1,24}", str(slug)):
            raise ValueError("personnage inconnu")
        return self.at.dp / str(slug)

    def _b(self, slug):
        b = _load(self.dir(slug) / "biblio.json", {})
        for k in ("choix", "genres", "planches"):
            b.setdefault(k, {})
        b.setdefault("loras", [])
        b.setdefault("historique", [])
        return b

    def _ecrire(self, slug, b):
        d = self.dir(slug)
        d.mkdir(parents=True, exist_ok=True)
        (d / "biblio.json").write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")

    def fichier(self, slug, name):
        d = self.dir(slug)
        f = (d / name).resolve()
        if f.parent == d.resolve() and f.is_file() and f.suffix in (".png", ".mp4"):
            return f
        raise FileNotFoundError(name)

    def image(self, slug, quoi, ligne, defaut=False):
        """Image choisie d'un lieu ("l") ou d'une tenue ("t") de la fiche, ou None : c'est ce que lit la Production.
        `defaut` : sans image choisie, la premiere de la ligne (comparaison des methodes)."""
        try:
            nom = self._b(slug)["choix"].get(f"{quoi}_{h8(ligne)}")
            if not nom and defaut:
                nom = next(iter(sorted(f.name for f in self.dir(slug).glob(f"{quoi}_{h8(ligne)}_*.png"))), None)
            return self.fichier(slug, nom) if nom else None
        except (FileNotFoundError, ValueError):
            return None

    # --- Vue --------------------------------------------------------------------------------------
    def _etat(self, log, ici):
        try:
            t = Path(log).read_text(encoding="utf-8", errors="replace")
        except OSError:
            t = ""
        etat = "en cours" if ici else "arrete" if "ARRET" in t else "termine" if "rapport :" in t else "interrompu"
        m = re.search(r'"cost_usd": ([\d.]+)', t)
        lo = re.search(r'"lora": "([^"]*)"', t)
        return {"etat": etat, "faites": t.count(" : image (") + t.count(" : clip ("), "echecs": t.count("ECHEC"), "cout": float(m.group(1)) if m else None,
                "lora": lo.group(1) if lo else "", "log": "\n".join(l for l in t.strip().splitlines()[-3:] if "rapport :" not in l and "pod " not in l)[-400:]}

    def _ici(self, log):
        return bool(self.job and self.job["log"] == str(log) and self.at.studio.running())

    def vue(self, slug):
        p, b, d = self.at.perso(slug), self._b(slug), self.dir(slug)
        noms = sorted(f.name for f in d.glob("*.png")) if d.is_dir() else []
        change = False
        for lo in b["loras"]:  # un entrainement fini depuis la derniere visite : son resultat est note
            if lo["etat"] == "en cours" and not self._ici(lo["log"]):
                e = self._etat(lo["log"], False)
                lo.update(etat="prete" if e["lora"] else "echec", fichier=e["lora"], cout=e["cout"])
                change = True
        if change:
            self._ecrire(slug, b)

        def lignes(k, q):
            out = []
            for x in p.get(k) or []:
                h = h8(x)
                imgs = [n for n in noms if n.startswith(f"{q}_{h}_")]
                ch = b["choix"].get(f"{q}_{h}")
                out.append({"cle": h, "fr": _s(x.partition("|")[0]) if "|" in x else "", "en": _s(x.rpartition("|")[2]), "images": imgs,
                            "choix": ch if ch in imgs else "", "genre": b["genres"].get(h, "tenue"),
                            "portees": [n for n in noms if n.startswith(f"p_{h}_")]} if q == "t" else
                           {"cle": h, "fr": _s(x.partition("|")[0]) if "|" in x else "", "en": _s(x.rpartition("|")[2]), "images": imgs, "choix": ch if ch in imgs else ""})
            return out
        g = p.get("generation") or {}
        def num(pre):  # images numerotees d'une famille, les plus recentes d'abord
            return sorted((n for n in noms if n.startswith(pre) and n[2:-4].isdigit()), key=lambda n: -int(n[2:-4]))

        vis, tach = num("v_"), self._taches(slug)
        expr = [{"cle": h, "fr": fr, "en": en, "fiche": fi, "images": [{"nom": n, "garde": bool(b["planches"].get(n, {}).get("garde"))}
                                                                    for n in noms if n.startswith(f"x_{h}_")]} for h, fr, en, fi in self._expressions(p)]
        series = self._series(slug)
        j = self.job if self.job and self.job["slug"] == slug else None
        return {"slug": slug, "nom": p["nom"], "lora": bool(g.get("lora")), "lora_force": g.get("lora_strength"), "prefixe": bool(g.get("zimage_prefix")),
                "lieux": lignes("lieux", "l"), "tenues": lignes("tenues", "t"),
                "visage": {"images": vis, "choix": b["choix"].get("visage") if b["choix"].get("visage") in vis else ""},
                "corps": {"face": {"images": num("k_"), "choix": b["choix"].get("corps") if b["choix"].get("corps") in noms else ""},
                          "dos": {"images": num("d_"), "choix": b["choix"].get("dos") if b["choix"].get("dos") in noms else ""},
                          "angles": [{"nom": n, "vue": ANGLES[(int(n[2:-4]) - 1) % len(ANGLES)][0]} for n in num("a_")], "tenue": b.get("corps_tenue") or "", "loras": b.get("corps_loras") or [], "nsfw": bool(b.get("corps_nsfw")),
                          "avec_lora": [n for n in noms if n[:2] in ("k_", "d_", "a_") and (tach.get(n[:-4]) or {}).get("loras")], "variantes": "\n".join(b.get("corps_variantes") or [])},
                "expressions": expr, "gardees": sum(1 for x in b["planches"].values() if x.get("garde")),
                "banc": [{"cle": k, **x, "images": [n for n in noms if n.startswith(f"b_{k}_")], "clips": sorted(f.name for f in d.glob(f"bv_{k}_*.mp4"))}
                         for k, x in reversed(list((b.get("banc") or {}).items()))],
                "departs": [n for n in noms if n.startswith("bd_")],
                "planches": [{"nom": n, "garde": bool(b["planches"].get(n, {}).get("garde")), "legende": b["planches"].get(n, {}).get("legende", "")}
                             for n in noms if n.startswith("c_")],
                "series": {s: series[s] for s in {n.split("_")[1] for n in noms if n.startswith("c_")} if s in series},
                "loras": [{k: lo.get(k) for k in ("nom", "etat", "date", "passages", "images", "cout")} | {"en_place": bool(lo.get("fichier")) and lo.get("fichier") == g.get("lora"),
                           "essais": [n for n in noms if n.startswith(f"e_{lo['v']}_")]} for lo in b["loras"]],
                "job": ({"quoi": j["quoi"], "n": j["n"]} | self._etat(j["log"], self._ici(j["log"]))) if j else None,
                "occupe": self.at.studio.running(), "pod": bool(self.at.studio.pod()), "forces": FORCES, "poses": [x[0] for x in POSES]}

    def _series(self, slug):
        """Reglages de chaque serie de planches, relus dans les fiches de lancement (lots/planches-*.json) : date, tenue, adultes, LoRA en plus."""
        memo = self.__dict__.setdefault("_memo_series", {})
        out = {}
        for f in sorted((self.dir(slug) / "lots").glob("planches-*.json")):
            if str(f) not in memo:
                try:
                    lot = json.loads(f.read_text(encoding="utf-8"))
                    T = lot["taches"]
                    serie = int(T[0]["sortie"].split("_")[1])
                    rg = lot.get("reglages")
                    if not rg:  # fiche d'avant les reglages notes : la tenue se relit dans le texte de chaque planche
                        habits = []
                        for i, t in enumerate(T):
                            cadre, fond = CADRES[(i * 7 + serie) % len(CADRES)], FONDS[(i + serie) % len(FONDS)]
                            if "bed" in cadre:
                                fond = FONDS[1]
                            h = t["prompt"].partition(f"{cadre}, {fond}, ")[2]
                            for fin in (FIN, FIN_ANC, f". Natural smartphone photo, {PEAU}.", ". Natural smartphone photo.", ", nsfw"):
                                h = h[:-len(fin)] if h.endswith(fin) else h
                            habits.append(h)
                        rg = {"tenue": habits[0] if len(set(habits)) == 1 else "", "nsfw": ", nsfw" in T[0]["prompt"],
                              "loras": [x if isinstance(x, str) else x.get("name", "") for x in T[0].get("loras") or []]}
                    m = re.search(r"-(\d{4})(\d\d)(\d\d)-(\d\d)(\d\d)", f.name)
                    memo[str(f)] = (str(serie), {**rg, "n": len(T), "date": f"{m.group(3)}/{m.group(2)} {m.group(4)}:{m.group(5)}" if m else ""})
                except Exception:
                    memo[str(f)] = None
            if memo[str(f)]:
                out[memo[str(f)][0]] = memo[str(f)][1]
        return out

    # --- Lignes de la fiche -----------------------------------------------------------------------
    def ajouter(self, b):
        """Nouvelle ligne "français | anglais" dans les lieux ou les tenues de la fiche ; "genre" : tenue ou dessous."""
        slug, k = b["slug"], "lieux" if b.get("quoi") == "lieux" else "tenues"
        fr, en = _s(b.get("fr"), 120), _s(b.get("en"), 280).strip(" .")
        if not fr or not en:
            raise ValueError("il faut le nom en français et la description en anglais")
        if not re.match(r"(in|on|at|by|inside|under) " if k == "lieux" else r"(a|an|the|her|two|some) ", en.lower()):
            raise ValueError('la description anglaise d\'un lieu commence par "in" ou "on"' if k == "lieux" else 'la description anglaise d\'une tenue commence par "a" ou "an"')
        p = dict(self.at.perso(slug))
        if len(p.get(k) or []) >= 30:
            raise ValueError("30 lignes au plus : en retirer une d'abord")
        if any(cle(x) == cle(en) for x in p.get(k) or []):
            raise ValueError("cette ligne existe déjà")
        p[k] = [*(p.get(k) or []), f"{fr} | {en}"]
        self.at.save_perso(p)
        if k == "tenues" and b.get("genre") == "dessous":
            bb = self._b(slug)
            bb["genres"][h8(en)] = "dessous"
            self._ecrire(slug, bb)
        return self.vue(slug)

    def retirer(self, b):
        """Retire une ligne de la fiche (ses images sont mises de cote dans retire/), ou une seule image."""
        slug = b["slug"]
        d = self.dir(slug)
        (d / "retire").mkdir(parents=True, exist_ok=True)
        if b.get("image"):
            f = self.fichier(slug, str(b["image"]))
            shutil.move(str(f), str(d / "retire" / f.name))
            bb = self._b(slug)
            bb["planches"].pop(f.name, None)
            self._ecrire(slug, bb)
            return self.vue(slug)
        k, q = ("lieux", "l") if b.get("quoi") == "lieux" else ("tenues", "t")
        p = dict(self.at.perso(slug))
        p[k] = [x for x in p.get(k) or [] if h8(x) != b.get("cle")]
        self.at.save_perso(p)
        for qq in (q, "p") if q == "t" else (q,):
            for f in d.glob(f"{qq}_{re.sub(r'[^0-9a-f]', '', str(b.get('cle')))}_*.png"):
                shutil.move(str(f), str(d / "retire" / f.name))
        return self.vue(slug)

    def choix(self, b):
        slug, bb = b["slug"], self._b(b["slug"])
        nom = self.fichier(slug, str(b["image"])).name
        m = re.fullmatch(r"([lt])_([0-9a-f]{8})_\d+\.png", nom)
        if m:
            bb["choix"][f"{m.group(1)}_{m.group(2)}"] = nom
        elif nom[:2] in ("v_", "k_", "d_"):
            bb["choix"][{"v_": "visage", "k_": "corps", "d_": "dos"}[nom[:2]]] = nom
        else:
            raise ValueError("image sans choix possible")
        self._ecrire(slug, bb)
        return self.vue(slug)

    def _jetes(self, slug, pre):
        """Numeros des images supprimees (rangees dans corbeille/) : ils ne sont pas repris, sinon la meme image reviendrait."""
        return {int(f.stem.rsplit("_", 1)[1]) for f in (self.dir(slug) / "corbeille").glob(pre + "*.png") if f.stem.rsplit("_", 1)[1].isdigit()}

    def supprimer(self, b):
        """Image retiree de la bibliotheque (portrait, expression, planche, lieu, tenue, essayage) : rangee dans corbeille/, plus montree
        ni comptee ; un choix ou une case « garder » qui la visait tombe."""
        slug, bb = b["slug"], self._b(b["slug"])
        f = self.fichier(slug, str(b["image"]))
        if not re.fullmatch(r"[vxcltpkda]_[0-9a-f_]+\.png", f.name):
            raise ValueError("cette image ne se supprime pas d'ici")
        if self.job and self.job["slug"] == slug and self.at.studio.running():
            raise ValueError("un calcul de ce personnage est en cours : attendre sa fin")
        (f.parent / "corbeille").mkdir(exist_ok=True)
        f.replace(f.parent / "corbeille" / f.name)
        bb["planches"].pop(f.name, None)
        bb["choix"] = {k: n for k, n in bb["choix"].items() if n != f.name}
        self._ecrire(slug, bb)
        return self.vue(slug)

    def garde(self, b):
        """Planche gardee ou non pour l'entrainement ; "legende" : son texte, modifiable."""
        slug, bb = b["slug"], self._b(b["slug"])
        nom = self.fichier(slug, str(b["image"])).name
        e = bb["planches"].setdefault(nom, {})
        if "garde" in b:
            e["garde"] = bool(b["garde"])
        if "legende" in b:
            e["legende"] = _s(b["legende"], 600)
        self._ecrire(slug, bb)
        return {}

    # --- Calculs ----------------------------------------------------------------------------------
    def _libre(self):
        if self.at.chaine_active():
            raise ValueError("une chaîne de production est en cours : attendre sa fin")
        if self.at.studio.running():
            raise ValueError("un calcul est déjà en cours : attendre sa fin")
        if not self.at.studio.can_run():
            raise ValueError("clé RunPod absente : lancement impossible depuis l'interface")

    def _lancer(self, slug, quoi, lot, n, veille=True):
        d = self.dir(slug)
        (d / "lots").mkdir(parents=True, exist_ok=True)
        nom = f"{quoi}-{time.strftime('%Y%m%d-%H%M%S')}"
        lot |= {"nom": f"{slug}-{quoi}", "out": str(d), "character": self.at.char_override(self.at.perso(slug))} | ({"nom": lot["nom"]} if lot.get("nom") else {})
        (d / "lots" / f"{nom}.json").write_text(json.dumps(lot, ensure_ascii=False, indent=1), encoding="utf-8")
        tt = self._taches(slug) | {t["sortie"]: t for t in lot.get("taches") or [] if t.get("sortie") and t.get("prompt")}
        (d / "taches.json").write_text(json.dumps(tt, ensure_ascii=False), encoding="utf-8")  # le texte reel de chaque image, pour le relire et l'ajuster
        log = d / "lots" / f"{nom}.log"
        cmd = [sys.executable, "-m", "pilot", "perso" if veille else "entrainer", str(d / "lots" / f"{nom}.json")]
        if veille:  # pod de veille du studio, partage avec la Production et la page Essais
            cmd += ["--pod-id", os.environ.get("STUDIO_POD_ID") or self.at.studio.ensure_pod()]
        self.at.studio.proc = subprocess.Popen(cmd, cwd=str(self.at.repo / "server"), stdout=open(log, "w"), stderr=subprocess.STDOUT)
        self.job = {"slug": slug, "quoi": quoi, "log": str(log), "n": n}
        self.at.studio.poser(f"{NOMS_CALCUL.get(quoi, quoi.capitalize())} ({slug})")
        return log

    def _taches(self, slug):
        try:
            return json.loads((self.dir(slug) / "taches.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def texte(self, b):
        """Le texte reellement envoye pour une image (portrait, corps, expression) ; vide pour une image creee avant qu'il soit conserve."""
        t = self._taches(b["slug"]).get(str(b.get("image") or "")[:-4]) or {}
        return {"prompt": t.get("prompt") or "", "retouche": bool(t.get("ref")), "loras": [{"nom": x["name"], "force": x.get("strength")} if isinstance(x, dict) else {"nom": str(x), "force": None} for x in t.get("loras") or []]}

    def refaire(self, b):
        """Une image de plus d'apres une image existante, avec le texte ajuste par le proprietaire : meme reference, meme graine,
        memes LoRA ; seul le texte change, pour voir ce que l'ajustement donne. La nouvelle image prend le numero libre suivant."""
        slug, anc = b["slug"], str(b.get("image") or "")[:-4]
        self._libre()
        t0, texte = self._taches(slug).get(anc), _s(b.get("prompt"), 4000)
        if not t0 or not re.fullmatch(r"[vkda]_\d+|x_[0-9a-f]+_\d+", anc):
            raise ValueError("texte non conservé pour cette image : en créer une nouvelle d'abord")
        if not texte:
            raise ValueError("texte vide")
        pre, num = anc.rsplit("_", 1)
        pre += "_"
        pris = {int(f.stem.rsplit("_", 1)[1]) for f in self.dir(slug).glob(pre + "*.png") if f.stem.rsplit("_", 1)[1].isdigit()} | self._jetes(slug, pre)
        pas = len(ANGLES) if pre == "a_" else 1  # un angle refait garde sa vue : numero de meme rang
        s = next(x for x in range(int(num) + pas, 4000, pas) if x not in pris)
        if pre.startswith("x_"):
            bb = self._b(slug)
            bb["planches"][f"{pre}{s}.png"] = {"garde": False, "legende": texte[:600]}
            self._ecrire(slug, bb)
        self._lancer(slug, {"v": "visage", "x": "expressions"}.get(pre[0], "corps"), {"taches": [t0 | {"sortie": f"{pre}{s}", "prompt": texte}]}, 1)
        return {"lance": 1, "nom": f"{pre}{s}.png"}

    def _prefixe(self, p):
        g = p.get("generation") or {}
        return (g.get("zimage_prefix") or f"a {p.get('age', 25)} year old woman, ") + ((g["corps"].rstrip(", ") + ", ") if g.get("corps") else "")

    @staticmethod
    def _cases(p):
        """Fiche rangee en quatre cases (identite, allure, visage, corps) : les cases ; None pour une fiche d'un seul bloc."""
        g = p.get("generation") or {}
        return {k: (g.get(k) or "").strip(" ,") for k in ("identite", "allure", "visage", "corps")} if (g.get("identite") or "").strip(" ,") else None

    def _prefixe_corps(self, p):
        """Description pour une image du corps : identite, allure et corps. Le visage n'y est pas : tres decrit, il tire l'image vers lui."""
        c = self._cases(p)
        if c:
            return ", ".join(x for x in (c["identite"], c["allure"], c["corps"]) if x)
        return sans_visage(self._prefixe(p).rstrip(", "))  # fiche d'un seul bloc : le visage est devine aux mots et retire

    def _prefixe_visage(self, p):
        """Description pour un portrait : le debut de la fiche sans ce qui parle du corps (ni le champ « corps »), sinon le modele
        recule pour le montrer et le portrait devient un buste."""
        g, c = p.get("generation") or {}, self._cases(p)
        if c:  # fiche rangee : identite et visage, sans l'allure ni le corps
            return ", ".join(x for x in (c["identite"], c["visage"]) if x) + ", "
        txt = g.get("zimage_prefix") or f"a {p.get('age', 25)} year old woman, "
        garde = [x.strip() for x in txt.split(",") if x.strip() and not CORPS_MOTS.search(x)]
        return (", ".join(garde) or f"a {p.get('age', 25)} year old woman") + ", "

    def creer(self, b):
        """Images des lieux (piece vide) ou des tenues (a plat) : "cles" donnees, sinon toutes les lignes sans image. "n" images par ligne."""
        slug = b["slug"]
        self._libre()
        v = self.vue(slug)
        k, q = ("lieux", "l") if b.get("quoi") == "lieux" else ("tenues", "t")
        n = max(1, min(int(b.get("n") or 2), 4))
        dues = [x for x in v[k] if (x["cle"] in b["cles"] if b.get("cles") else not x["images"])]
        if not dues:
            raise ValueError("rien à créer : chaque ligne a déjà ses images")
        taches = []
        for x in dues:
            deja = {int(i.rsplit("_", 1)[1][:-4]) for i in x["images"]} | self._jetes(slug, f"{q}_{x['cle']}_")
            for s in [s for s in range(1, 60) if s not in deja][:n]:
                if q == "l":
                    pr = f"vertical wide shot, eye-level, photo of an empty deserted place, {_sans_elle(x['en'])}, natural light, smartphone photo"
                else:
                    pr = f"product photo, flat lay on a plain white background, {re.sub(r'^wearing ', '', x['en'])} laid flat, nothing else, no person, no mannequin"
                taches.append({"sortie": f"{q}_{x['cle']}_{s}", "prompt": pr, "seed": 7 * s + int(x["cle"][:4], 16), "taille": [720, 1280], "lora": False})
        self._lancer(slug, k, {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def importer(self, b):
        """Photo envoyee par le proprietaire ("png" : image PNG en base64, reduite par la page) pour une ligne de la fiche.
        Lieu : la photo devient l'image du lieu, retenue d'office. Tenue : deux images du vetement a plat sur fond blanc
        en sont tirees par retouche (la photo reste dans lots/, elle n'est pas montree)."""
        slug = b["slug"]
        v = self.vue(slug)
        k, q = ("lieux", "l") if b.get("quoi") == "lieux" else ("tenues", "t")
        x = next((x for x in v[k] if x["cle"] == b.get("cle")), None)
        if not x:
            raise ValueError("ligne inconnue")
        try:
            data = base64.b64decode(str(b.get("png") or "").rpartition(",")[2], validate=True)
        except ValueError:
            data = b""
        if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) > 12_000_000:
            raise ValueError("photo illisible ou trop lourde")
        d = self.dir(slug)
        (d / "lots").mkdir(parents=True, exist_ok=True)
        deja = {int(i.rsplit("_", 1)[1][:-4]) for i in x["images"]} | self._jetes(slug, f"{q}_{x['cle']}_")
        libres = [s for s in range(1, 60) if s not in deja]
        if q == "l":
            nom = f"l_{x['cle']}_{libres[0]}.png"
            (d / nom).write_bytes(data)
            bb = self._b(slug)
            bb["choix"][f"l_{x['cle']}"] = nom
            self._ecrire(slug, bb)
            return self.vue(slug)
        self._libre()
        src = d / "lots" / f"src_{x['cle']}.png"
        src.write_bytes(data)
        taches = [{"sortie": f"t_{x['cle']}_{s}", "ref": str(src), "seed": 300 + 13 * s, "taille": [720, 1280],
                   "prompt": "Product photo of the clothes from this picture only: the same garments, same colors, same fabric, same details, "
                             "laid flat on a plain white background. No person, no mannequin, no body, nothing else."} for s in libres[:2]]
        self._lancer(slug, "import", {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def essayer(self, b):
        """Cabine d'essayage : deux images d'elle portant une tenue de la garde-robe (son image retenue), sur fond neutre
        ou dans un lieu de la bibliotheque, dans une pose de la liste. Retouche a plusieurs images : elle (image neutre,
        faite une fois avec sa LoRA, ou son portrait retenu), la tenue a plat, le lieu vide."""
        slug = b["slug"]
        self._libre()
        p, v, d = self.at.perso(slug), self.vue(slug), self.dir(slug)
        x = next((x for x in v["tenues"] if x["cle"] == b.get("tenue") and x["choix"]), None)
        if not x:
            raise ValueError("choisir une tenue qui a une image retenue")
        lieu = next((y for y in v["lieux"] if y["cle"] == b.get("lieu") and y["choix"]), None) if b.get("lieu") else None
        pose = POSES[max(0, min(int(b.get("pose") or 0), len(POSES) - 1))][1]
        taches = []
        if v["lora"]:
            elle = d / "n_1.png"
            if not elle.is_file():
                taches.append({"sortie": "n_1", "lora": True, "seed": 4242, "taille": [720, 1280], "prompt": f"{self._prefixe(p)}{NEUTRE}{FIN}"})
        elif v["visage"]["choix"]:
            elle = self.fichier(slug, v["visage"]["choix"])
        else:
            raise ValueError("ce personnage n'a ni LoRA ni portrait retenu : passer d'abord par l'onglet Corps")
        refs = [str(self.fichier(slug, x["choix"]))] + ([str(self.fichier(slug, lieu["choix"]))] if lieu else [])
        ou = ("in the place shown in image 3. The place is exactly the one of image 3: same walls, same furniture, same floor, same light"
              if lieu else "in front of a plain light grey wall, soft studio light")
        deja = {int(i.rsplit("_", 1)[1][:-4]) for i in x["portees"]} | self._jetes(slug, f"p_{x['cle']}_")
        # des sous-vetements : sans le dire, le modele garde les habits de l'image 1 ou en invente (un survetement noir pour un ensemble noir)
        porte = (f"who has taken off all the clothes she wears in image 1 and now wears only the underwear set shown in image 2 ({x['en']}), "
                 "nothing over it: bare shoulders, bare arms, bare stomach, bare legs, no t-shirt, no trousers, no jacket"
                 if x["genre"] == "dessous" else "dressed only with the clothes shown in image 2")
        for s in [s for s in range(1, 200) if s not in deja][:2]:
            taches.append({"sortie": f"p_{x['cle']}_{s}", "ref": str(elle), "refs": refs, "seed": 600 + 17 * s, "taille": [720, 1280],
                           "prompt": f"The woman from image 1, same face, same hair, same body, {porte}, {ou}. "
                                     f"New photo of her: {pose}. Only one woman in the picture. Natural smartphone photo."})
        self._lancer(slug, "essayage", {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def visage(self, b):
        """Personnage sans LoRA : huit portraits d'apres sa description, aux traits tires au sort, le proprietaire en choisit un ; les planches en seront tirees."""
        slug = b["slug"]
        self._libre()
        p = self.at.perso(slug)
        pv = self._prefixe_visage(p)
        deja = {int(f.stem.split("_")[1]) for f in self.dir(slug).glob("v_*.png")} if self.dir(slug).is_dir() else set()
        deja |= self._jetes(slug, "v_")
        taches = [{"sortie": f"v_{s}", "seed": 1000 + 37 * s, "taille": [720, 1280], "lora": False,
                   "prompt": f"headshot of {traits(s, pv)}. {pv}vertical tight close-up headshot, her face fills the frame, cropped at the base of the neck, "
                             f"eye-level, front view, she looks at the camera, relaxed friendly expression, in front of a plain light grey wall, "
                             f"the collar of a white crew-neck t-shirt barely visible at the bottom edge, soft natural daylight{FIN}"}
                  for s in [s for s in range(1, 400) if s not in deja][:8]]
        self._lancer(slug, "visage", {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def corps(self, b):
        """Personnage sans LoRA : son corps de reference, tire du portrait retenu. "quoi" : face (huit essais, buste et taille tires au sort),
        dos (huit essais d'apres la face retenue, fesses et hanches tirees au sort), angles (profils et trois quarts d'apres face et dos).
        "tenue" : texte du proprietaire (anglais), tel quel ; vide : brassiere et culotte unies. Les planches sont ensuite tirees de ces images."""
        slug, quoi = b["slug"], b.get("quoi")
        self._libre()
        p, v, bb = self.at.perso(slug), self.vue(slug), self._b(slug)
        if v["lora"]:
            raise ValueError("sans objet : sa LoRA tient déjà son corps")
        if not v["visage"]["choix"]:
            raise ValueError("choisir d'abord un portrait : son corps en est tiré")
        if "tenue" in b:
            bb["corps_tenue"] = _s(b.get("tenue"), 400)
            self._ecrire(slug, bb)
        if "variantes" in b:  # details a faire varier, ecrits par le proprietaire : un par ligne, un tire au sort par image
            bb["corps_variantes"] = [_s(x, 200) for x in str(b.get("variantes") or "").splitlines() if x.strip()][:30]
            self._ecrire(slug, bb)
        if "loras" in b:  # LoRA choisies par le proprietaire : face et dos sont alors dessines par Z-Image avec elles, d'apres la description
            bb["corps_loras"] = [_s(x, 140) for x in b.get("loras") or [] if _s(x, 140)][:4]  # « nom » ou « nom:force »
            self._ecrire(slug, bb)
        if "nsfw" in b:  # images pour adultes : le mot nsfw suit la tenue dans chaque texte, comme pour les planches
            bb["corps_nsfw"] = bool(b.get("nsfw"))
            self._ecrire(slug, bb)
        tenue, var, lo = bb.get("corps_tenue") or CORPS_TENUE, bb.get("corps_variantes") or [], bb.get("corps_loras") or []
        if bb.get("corps_nsfw"):
            tenue += ", nsfw"
        # Sa description d'abord (les traits tires au sort ne font que la completer), sans ce qui decrit le visage : pour une image
        # du corps seuls comptent l'origine, la peau, les cheveux et le corps ; un visage tres decrit tire l'image vers lui.
        fiche = self._prefixe_corps(p)
        lo = [_lora_force(x) for x in lo]

        def plus(s):
            return (", " + random.Random(15485863 * s).choice(var)) if var else ""

        elle, c = str(self.fichier(slug, v["visage"]["choix"])), v["corps"]
        pre, base = {"face": ("k_", 7000), "dos": ("d_", 8000), "angles": ("a_", 9000)}[quoi]
        deja = {int(f.stem[2:]) for f in self.dir(slug).glob(pre + "*.png") if f.stem[2:].isdigit()} | self._jetes(slug, pre)
        libres = [s for s in range(1, 400) if s not in deja]
        if lo and quoi in ("face", "dos"):
            if quoi == "dos" and not c["face"]["choix"]:
                raise ValueError("retenir d'abord son corps de face")
            vue = "front view, she stands straight facing the camera"
            if quoi == "dos":
                # De dos, Z-Image suit le debut du texte : la vue passe en tete, et tout ce qui decrit le visage est retire
                # (traits du portrait, yeux, bouche...) ; sinon elle se retourne. La taille est celle de la face retenue.
                nf = c["face"]["choix"][2:-4]
                taille = (", " + taille_corps(int(nf))) if nf.isdigit() and not re.search(r"waist|stomach|torso", fiche, re.I) else ""
                taches = [{"sortie": f"{pre}{s}", "seed": base + 53 * s, "taille": [720, 1280], "lora": False, "loras": lo,
                           "prompt": f"full-body photo of a woman seen from behind, rear view, she stands with her back to the camera, facing the wall, "
                                     f"her face is not visible, only the back of her head and her hair. {fiche}{taille}, {traits_corps(s, fiche, True)}, "
                                     f"vertical full-body shot from head to feet, eye-level, arms slightly away from her body, feet slightly apart, "
                                     f"{CORPS_POSE_DOS}, {tenue}, only one woman in the picture{FIN}"}
                          for s in libres[:8]]
            else:
                taches = [{"sortie": f"{pre}{s}", "seed": base + 53 * s, "taille": [720, 1280], "lora": False, "loras": lo,
                           "prompt": f"full-body photo of a woman, {vue}. {fiche}, {traits_corps(s, fiche)}{plus(s)}, vertical full-body shot from head to feet, "
                                     f"eye-level, arms slightly away from her body, feet slightly apart, {CORPS_POSE}, {tenue}, only one woman in the picture{FIN}"}
                          for s in libres[:8]]
        elif quoi == "face":
            taches = [{"sortie": f"k_{s}", "ref": elle, "seed": base + 53 * s, "taille": [720, 1280],
                       "prompt": f"The woman from image 1, same face, same hair. New photo of her whole body, from head to feet: vertical full-body shot, eye-level, "
                                 f"front view, she stands straight facing the camera, arms slightly away from her body, feet slightly apart, {CORPS_POSE}. "
                                 f"She is {fiche}. Her body also has: {traits_corps(s, fiche)}{plus(s)}. {tenue}. Only one woman in the picture. Natural smartphone photo."}
                      for s in libres[:8]]
        elif not c["face"]["choix"]:
            raise ValueError("retenir d'abord son corps de face")
        elif quoi == "dos":
            face = str(self.fichier(slug, c["face"]["choix"]))
            taches = [{"sortie": f"d_{s}", "ref": face, "refs": [elle], "seed": base + 59 * s, "taille": [720, 1280],
                       "prompt": f"The woman from image 1 (her face is shown in image 2): same body, same skin, same hair, same height. New photo of her seen from behind, "
                                 f"from head to feet: vertical full-body shot, eye-level, back view, she stands straight with her back to the camera, head facing away, "
                                 f"arms slightly away from her body, feet slightly apart, {CORPS_POSE}. She is {fiche}. Her body from behind also has: {traits_corps(s, fiche, True)}. {tenue}. "
                                 "Only one woman in the picture. Natural smartphone photo."}
                      for s in libres[:8]]
        elif not c["dos"]["choix"]:
            raise ValueError("retenir d'abord son corps de dos")
        else:
            face, dos = str(self.fichier(slug, c["face"]["choix"])), str(self.fichier(slug, c["dos"]["choix"]))
            libres = [s for s in libres if (s - 1) % len(ANGLES) == 0][:1]  # un tour complet des angles a la fois
            nf, nd = c["face"]["choix"][2:-4], c["dos"]["choix"][2:-4]
            if lo and nf.isdigit() and nd.isdigit():  # LoRA choisies : les angles aussi sont dessines par Z-Image avec elles, la vue en tete du texte
                corps = f"{traits_corps(int(nf), fiche)}{plus(int(nf))}, {traits_corps(int(nd), fiche, True)}"
                taches = [{"sortie": f"a_{s}", "seed": base + 61 * s, "taille": [720, 1280], "lora": False, "loras": lo,
                           "prompt": texte_angle((s - 1) % len(ANGLES), fiche, corps, tenue)}
                          for s in range(libres[0], libres[0] + len(ANGLES))]
                self._lancer(slug, "corps", {"taches": taches}, len(taches))
                return {"lance": len(taches)}
            taches = [{"sortie": f"a_{s}", "ref": face, "refs": [dos, elle], "seed": base + 61 * s, "taille": [720, 1280],
                       "prompt": f"The woman from image 1 (front), image 2 (her back) and image 3 (her face): exactly the same body, same breasts, same waist, same hips, "
                                 f"same buttocks, same skin, same hair. New photo of her from another angle, from head to feet: vertical full-body shot, eye-level, "
                                 f"{ANGLES[(s - 1) % len(ANGLES)][1]}, {CORPS_POSE}. {tenue}. Only one woman in the picture. Natural smartphone photo."}
                      for s in range(libres[0], libres[0] + len(ANGLES))]
        self._lancer(slug, "corps", {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def _refs_corps(self, slug, v, cadre):
        """Images du corps de reference a joindre a une planche, d'apres son cadrage (deux au plus : la retouche lit trois images, portrait compris)."""
        c = v["corps"]
        if cadre.startswith("close-up") or not c["face"]["choix"]:
            return []
        vue = lambda k: next((x["nom"] for x in c["angles"] if (int(x["nom"][2:-4]) - 1) % len(ANGLES) == k), None)
        face, dos = c["face"]["choix"], c["dos"]["choix"]
        if "back view" in cadre:  # de face et de dos : la seule vue qui correspond (une vue opposee en plus brouille le corps)
            r = [dos]
        elif "profile" in cadre:
            r = [vue(0) or vue(3), face]
        elif "three-quarter" in cadre:
            r = [vue(1), face]
        else:
            r = [face]
        r = [x for x in r if x] or [face]
        return [str(self.fichier(slug, x)) for x in dict.fromkeys(r)]

    def _expressions(self, p):
        """Expressions de la galerie : celles de la fiche du personnage ("français | anglais"), puis la liste commune."""
        out, vus = [], set()
        for fr, en, fi in [(_s(x.partition("|")[0], 60), _s(x.rpartition("|")[2], 200).strip(" ."), True) for x in p.get("expressions") or [] if "|" in x] \
                + [(fr, en, False) for fr, en in EXPRESSIONS]:
            h = h8(en)
            if en and h not in vus:
                vus.add(h)
                out.append((h, fr, en, fi))
        return out

    def expressions(self, b):
        """Galerie d'expressions : une image par expression qui n'en a pas ("cles" : une image de plus pour celles-la).
        Avec la LoRA du personnage si elle existe ; sinon par retouche du portrait choisi. Cadrage serre, fonds et vues varies,
        tenue habillee de la fiche : ces images entrent dans le jeu d'entrainement comme les planches (case « garder »)."""
        slug = b["slug"]
        self._libre()
        p, v, bb = self.at.perso(slug), self.vue(slug), self._b(slug)
        ref = None
        if not v["lora"]:
            if not v["visage"]["choix"]:
                raise ValueError("choisir d'abord un portrait : les expressions en sont tirées")
            ref = str(self.fichier(slug, v["visage"]["choix"]))
        cles = {str(x) for x in b.get("cles") or []}
        pre, taches = self._prefixe_visage(p), []
        for i, x in enumerate(v["expressions"]):
            if (x["cle"] not in cles) if cles else x["images"]:
                continue
            k = max([int(y["nom"][:-4].split("_")[2]) for y in x["images"]] + list(self._jetes(slug, f"x_{x['cle']}_")) or [0]) + 1
            # la tenue n'est plus nommee : la citer fait reculer le cadre jusqu'au buste
            desc = (f"extreme close-up of her face only, from the chin to the top of her hair, her face fills the whole frame, shoulders out of frame, "
                    f"eye-level, {VUES[(i + k) % len(VUES)]}, {x['en']}, {FONDS[(i + k) % len(FONDS)]} blurred behind her")
            nom = f"x_{x['cle']}_{k}"
            bb["planches"][nom + ".png"] = {"garde": False, "legende": f"{pre}{desc}"}
            t = {"sortie": nom, "seed": 7000 + 53 * i + k, "taille": [720, 1280]}
            t |= {"ref": ref, "prompt": (f"Change the facial expression of the woman in image 1. Her new expression: {x['en']}. The expression is strong and obvious, "
                                        f"clearly different from image 1: her mouth, eyes and eyebrows move accordingly. She stays the same woman: same "
                                        f"facial features, same hair. New photo of her: {desc}. Natural smartphone photo.")} if ref \
                else {"lora": True, "prompt": f"{pre}vertical {desc}{FIN}"}
            taches.append(t)
        if not taches:
            raise ValueError("chaque expression a déjà son image : toucher « une autre » sur celle à refaire")
        self._ecrire(slug, bb)
        self._lancer(slug, "expressions", {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def planches(self, b):
        """Serie de planches : photos d'elle, cadrages, fonds et expressions varies. "tenue" vide : les tenues de sa fiche a tour de role ;
        sinon le texte du proprietaire (anglais), tel quel, pour toute la serie. "loras" : LoRA en plus, choisies par lui.
        Avec la LoRA du personnage si elle existe ; sinon par retouche du portrait choisi."""
        slug = b["slug"]
        self._libre()
        p, v, bb = self.at.perso(slug), self.vue(slug), self._b(slug)
        n = max(4, min(int(b.get("n") or 24), 40))
        tenue = _s(b.get("tenue"), 400)
        # « wearing » devant un etat sans vetement donne des dessous couleur chair : il est retire (page ancienne restee ouverte, ou saisie)
        tenue = re.sub(r"^wearing\s+(?=(?:fully |completely |totally )?(?:nude|naked|topless|bottomless|undressed|unclothed)\b)", "", tenue, flags=re.I)
        ref = None
        if not v["lora"]:
            if not v["visage"]["choix"]:
                raise ValueError("choisir d'abord un portrait : les planches en sont tirées")
            ref = str(self.fichier(slug, v["visage"]["choix"]))
        # « voie » lora (personnage sans LoRA) : le corps est dessine par Z-Image d'apres la fiche, avec les LoRA du proprietaire, puis
        # le visage du portrait retenu y est pose par retouche. Les images du corps de reference ne servent pas.
        pose = bool(ref) and b.get("voie") == "lora"
        lo = [_lora_force(x) for x in b.get("loras") or []][:4] if pose else []
        tenues = [x["en"] for x in v["tenues"] if x["genre"] != "dessous"] or ["a white t-shirt and jeans"]
        serie = bb["series"] = int(bb.get("series") or 0) + 1
        pre, taches = self._prefixe(p), []
        # Expressions de la galerie (celles de la fiche en tete), a tour de role, sur un cadrage sur deux qui n'en dit aucune :
        # le jeu d'entrainement garde une majorite de visages calmes, et la LoRA apprend que le visage bouge.
        exprs = [", ".join(y for y in en.split(", ") if not y.startswith("looking")) for _, fr, en, _ in self._expressions(p) if fr != "Neutre"]
        libres = 0
        for i in range(n):
            cadre, fond = CADRES[(i * 7 + serie) % len(CADRES)], FONDS[(i + serie) % len(FONDS)]
            if "bed" in cadre:
                fond = FONDS[1]
            if exprs and not re.search(r"neutral|smile|laugh", cadre):
                if libres % 2 == 0:
                    cadre += ", " + exprs[(libres // 2 + serie) % len(exprs)]
                libres += 1
            habit = tenue or "wearing " + re.sub(r"^wearing ", "", tenues[(i + serie) % len(tenues)])
            desc = f"{cadre}, {fond}, {habit}" + (", nsfw" if b.get("nsfw") else "")
            nom = f"c_{serie}_{i + 1:02d}"
            bb["planches"][nom + ".png"] = {"garde": False, "legende": f"{pre}{desc}"}
            t = {"sortie": nom, "seed": 5000 + 101 * serie + i, "taille": [720, 1280]}
            if pose:
                dessin = {"seed": t["seed"], "taille": t["taille"], "lora": False, "loras": lo}
                if "back view" in cadre:  # de dos, pas de visage a poser : l'image dessinee est la planche (la vue en tete, le visage non decrit)
                    t |= dessin | {"prompt": f"photo of a woman seen from behind, {self._prefixe_corps(p)}, vertical {desc}{FIN}"}
                else:
                    taches.append(dessin | {"sortie": f"y_{serie}_{i + 1:02d}", "prompt": f"{pre}vertical {desc}{FIN}"})
                    t |= {"ref": str(self.dir(slug) / f"y_{serie}_{i + 1:02d}.png"), "refs": [ref], "depuis": f"y_{serie}_{i + 1:02d}",
                          "prompt": "Replace the head of the woman in image 1 with the head of the woman from image 2: her face, her facial features and her hair, "
                                    "keeping the expression, the gaze and the head position of image 1. Keep everything else of image 1 exactly unchanged: her body, "
                                    f"her skin tone, her pose, her clothing, the background, the light and the framing. Only one woman in the picture. Natural smartphone photo, {PEAU}."}
            elif ref:
                # Par retouche : ses cases Identite, Allure et Corps sont redites, pour que la peau (bronzage) et les formes ecrites par le
                # proprietaire ne tiennent pas qu'aux images de reference, que le nouveau fond et la nouvelle pose font deriver.
                cs = self._cases(p) or {}
                qui = ", ".join(x for x in (cs.get("identite"), cs.get("allure")) if x)
                qui = (f" She is {qui}." if qui else "") + (f" Her body: {cs['corps']}." if cs.get("corps") else "")
                rc = self._refs_corps(slug, v, cadre)
                t |= {"ref": ref, "prompt": f"Same woman, same face, same hair.{qui} New photo of her: {desc}. Natural smartphone photo, {PEAU}."}
                if rc:  # son corps de reference : meme corps, mais ni sa tenue ni son fond ; sa tete y est coupee (sauf de dos), un seul visage en jeu
                    t |= {"sans_tete": [x for x in rc if not _de_dos(x)]}
                    t |= {"refs": rc, "prompt": f"The woman from image 1: same face, same hair. Her body is the one shown in image {' and image '.join(str(k) for k in range(2, 2 + len(rc)))}: "
                                                f"same breasts, same waist, same hips, same buttocks, same legs, same skin; ignore the clothes and the background of "
                                                f"{'those images' if len(rc) > 1 else 'that image'}.{qui} New photo of her: {desc}. Only one woman in the picture. Natural smartphone photo, {PEAU}."}
            else:
                t |= {"lora": True, "loras": [str(x) for x in b.get("loras") or []][:4], "prompt": f"{pre}vertical {desc}{FIN}"}
            taches.append(t)
        self._ecrire(slug, bb)
        self._lancer(slug, "planches", {"taches": taches, "reglages": {"tenue": tenue, "nsfw": bool(b.get("nsfw")), "loras": [str(x) for x in b.get("loras") or []][:4], "voie": "lora" if pose else ""}}, n)
        return {"lance": n}

    def banc(self, b):
        """Banc d'essai d'une LoRA. LoRA de clip : voir _banc_clip. LoRA d'image : une position, a trois cadrages et trois forces, avec le visage du personnage et les LoRA de style
        par defaut du temps 4. Le proprietaire coche ce qui tient ; la fiche de capacite de la LoRA en est tiree (banc_noter)."""
        from atelier import BANC_CADRES, BANC_DEUX, BANC_FORCES, BANC_PARTENAIRE, BANC_SEUL, CATS_STYLE as STYLES, _cle, _loras_plan
        from categories import temps_min
        slug = b["slug"]
        self._libre()
        p, v, bb = self.at.perso(slug), self.vue(slug), self._b(slug)
        cat, nom = self.at._catalogue(), str(b.get("lora") or "")
        if nom not in cat:
            raise ValueError("choisir une LoRA du catalogue")
        if cat[nom].get("famille") == "wan22":
            return self._banc_clip(b, p, bb, cat, nom)
        if not v["lora"]:
            raise ValueError("ce personnage n'a pas encore sa LoRA de visage : le banc en a besoin")
        acte, phrase = _s(b.get("acte"), 80), _s(b.get("phrase"), 500)
        if not acte:
            raise ValueError("écrire la position à essayer")
        k = hashlib.sha1(f"{nom}|{_cle(acte)}".encode()).hexdigest()[:8]
        fi = self.at._lib()["fiche"]
        styles = [x for x in _loras_plan(self.at._defauts().get(4) or "") if fi.get(x["name"] if isinstance(x, dict) else x, ("autre", "zimage")) [0] in STYLES
                  and fi.get(x["name"] if isinstance(x, dict) else x, ("", "zimage"))[1] != "wan22"]
        avec = []  # LoRA empilees a celle qu'on essaie, au choix du proprietaire, chacune a sa force du catalogue
        for n in b.get("avec") or []:
            if n in cat and n != nom and n not in avec and cat[n].get("famille") != "wan22" and not any((x["name"] if isinstance(x, dict) else x) == n for x in styles):
                avec.append(n)
        if len(avec) > 4:
            raise ValueError("4 LoRA ajoutées au plus")
        adulte = max(temps_min(cat[n].get("cat")) for n in (nom, *avec)) >= 2
        forces = self._forces(b)
        serie = int((bb.setdefault("banc", {}).get(k) or {}).get("serie") or 0) + 1
        pre, taches = self._prefixe(p), []
        deux = str(b.get("personnes")) == "2"
        part = (_s(b.get("partenaire"), 200) or BANC_PARTENAIRE) if deux else ""
        if deux:  # a deux : cadrages qui laissent voir les deux corps, et le partenaire dit dans la phrase
            phrase = f"{phrase or acte}, {part}"
        for ci, (ck, _, cadre) in enumerate([c for c in BANC_CADRES if c[0] in (BANC_DEUX if deux else BANC_SEUL)]):
            for f in forces:
                taches.append({"sortie": f"b_{k}_{serie}_{ck}_{int(round(f * 100)):03d}", "seed": 9000 + 13 * serie + ci, "taille": [720, 1280], "lora": True,
                               "loras": [*styles, *avec, {"name": nom, "strength": f}], "prompt": f"{pre}vertical {cadre}, {phrase or acte}{', nsfw' if adulte else ''}{FIN}"})
        bb["banc"].pop(k, None)  # la derniere serie lancee passe en tete
        bb["banc"][k] = {"lora": nom, "acte": acte, "phrase": _s(b.get("phrase"), 500), "partenaire": part, "personnes": 2 if deux else 1, "avec": avec, "forces": forces, "serie": serie, "date": time.strftime("%d/%m/%Y")}
        self._ecrire(slug, bb)
        self._lancer(slug, "banc", {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def _forces(self, b):
        """Trois poids, au choix du proprietaire (par defaut BANC_FORCES)."""
        from atelier import BANC_FORCES
        try:
            forces = sorted({round(float(str(f).replace(",", ".")), 2) for f in b.get("forces") or BANC_FORCES})
        except (TypeError, ValueError):
            forces = []
        if len(forces) != 3 or not all(0.1 <= f <= 2 for f in forces):
            raise ValueError("trois poids différents, entre 0,1 et 2")
        return forces

    def _banc_clip(self, b, p, bb, cat, nom):
        """Banc d'une LoRA de clip : une image de depart choisie par le proprietaire, un mouvement, et trois clips de 5 s qui ne different que
        par le poids de la LoRA. Les LoRA de mouvement et de vitesse par defaut du temps 4 sont chargees comme en Production."""
        from atelier import _cle, _loras_plan
        slug = b["slug"]
        acte, phrase = _s(b.get("acte"), 80), _s(b.get("phrase"), 500)
        if not acte or not phrase:
            raise ValueError("écrire la position et le mouvement")
        try:
            depart = self.fichier(slug, str(b.get("image") or ""))
        except FileNotFoundError:
            depart = None
        if not depart or depart.suffix != ".png":
            raise ValueError("choisir l'image de départ")
        fi = self.at._lib()["fiche"]
        nm = lambda x: x["name"] if isinstance(x, dict) else x
        base = [x for x in _loras_plan(self.at._defauts().get(4) or "") if nm(x) != nom and fi.get(nm(x), ("autre", "zimage"))[1] == "wan22"
                and fi.get(nm(x), ("autre",))[0] in ("mouvement", "vitesse")]
        avec = []  # LoRA de clip empilees a celle qu'on essaie
        for n in b.get("avec") or []:
            if n in cat and n != nom and n not in avec and cat[n].get("famille") == "wan22" and not any(nm(x) == n for x in base):
                avec.append(n)
        if len(avec) > 2:
            raise ValueError("2 LoRA de clip ajoutées au plus")
        forces = self._forces(b)
        k = hashlib.sha1(f"{nom}|{_cle(acte)}".encode()).hexdigest()[:8]
        serie = int((bb.setdefault("banc", {}).get(k) or {}).get("serie") or 0) + 1
        taches = [{"sortie": f"bv_{k}_{serie}_{int(round(f * 100)):03d}", "clip": str(depart), "prompt": phrase, "seed": 9100 + 13 * serie, "taille": [480, 832],
                   "loras": [*base, *avec, {"name": nom, "strength": f}]} for f in forces]
        bb["banc"].pop(k, None)
        bb["banc"][k] = {"lora": nom, "acte": acte, "phrase": phrase, "personnes": 1, "avec": avec, "forces": forces, "serie": serie, "clip": True,
                         "image": depart.name, "date": time.strftime("%d/%m/%Y")}
        self._ecrire(slug, bb)
        self._lancer(slug, "banc", {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def banc_depart(self, b):
        """Image de depart envoyee par le proprietaire pour le banc des clips ("png" : PNG en base64, reduit par la page)."""
        slug = b["slug"]
        try:
            data = base64.b64decode(str(b.get("png") or "").rpartition(",")[2], validate=True)
        except ValueError:
            data = b""
        if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) > 12_000_000:
            raise ValueError("image illisible ou trop lourde")
        d = self.dir(slug)
        d.mkdir(parents=True, exist_ok=True)
        deja = sorted(d.glob("bd_*.png"))
        if len(deja) >= 24:
            raise ValueError("24 images de départ au plus : en retirer une")
        nom = f"bd_{hashlib.sha1(data).hexdigest()[:8]}.png"
        (d / nom).write_bytes(data)
        return {**self.vue(slug), "depart": nom}

    def banc_depart_retirer(self, b):
        f = self.fichier(b["slug"], str(b.get("image") or ""))
        if not f.name.startswith("bd_"):
            raise ValueError("image de départ inconnue")
        f.unlink()
        return self.vue(b["slug"])

    def banc_retirer(self, b):
        """Retire une serie du banc de la page (ses images restent sur le disque, la fiche de capacite n'est pas touchee)."""
        slug, bb = b["slug"], self._b(b["slug"])
        if (bb.get("banc") or {}).pop(str(b.get("cle")), None) is None:
            raise ValueError("série du banc inconnue")
        self._ecrire(slug, bb)
        return self.vue(slug)

    def banc_noter(self, b):
        """Le proprietaire a coche les images du banc qui tiennent ("bonnes") : la ligne de la fiche de capacite est ecrite. Cadrages : ceux
        des images cochees ; force : celle qui revient le plus (la plus basse a egalite). Rien de coche : la position est notee non validee."""
        from atelier import _cle
        slug, bb = b["slug"], self._b(b["slug"])
        x = (bb.get("banc") or {}).get(str(b.get("cle")))
        if not x:
            raise ValueError("série du banc inconnue")
        pre = f"b{'v' if x.get('clip') else ''}_{b['cle']}_{x['serie']}_"
        bonnes = [n[len(pre):-4].split("_") for n in b.get("bonnes") or [] if str(n).startswith(pre) and (self.dir(slug) / str(n)).is_file()]
        if x.get("clip"):  # un clip par poids : le plus bas des poids coches est garde
            bonnes = [("", f) for f, in bonnes]
        forces = [int(f) / 100 for _, f in bonnes]
        ligne = {"acte": x["acte"], "phrase": x["phrase"], "personnes": x["personnes"], "avec": x.get("avec") or [], "cadrages": sorted({c for c, _ in bonnes if c}),
                 "force": min(set(forces), key=lambda f: (-forces.count(f), f)) if forces else 0, "ok": bool(bonnes)}
        avant = [l for l in (self.at._catalogue().get(x["lora"]) or {}).get("capacite") or [] if isinstance(l, dict) and _cle(l.get("acte")) != _cle(x["acte"])]
        bib = self.at.save_capacite({"name": x["lora"], "capacite": [*avant, ligne]}, verrou=False)
        x["note"] = {"bonnes": len(bonnes), "date": time.strftime("%d/%m/%Y")}
        self._ecrire(slug, bb)
        return {**self.vue(slug), "bibliotheque": bib}

    def devis(self, slug, passages):
        """Duree et cout estimes d'un entrainement : 1 350 pas en 40 min sur la carte rapide (constate par le proprietaire), plus la mise en route."""
        n = sum(1 for x in self._b(slug)["planches"].values() if x.get("garde"))
        minutes = round(n * passages * 40 / 1350 + 10)
        return {"images": n, "minutes": minutes, "usd": round(minutes / 60 * 0.95 + 0.02, 2)}

    def entrainer(self, b):
        """Entraine une nouvelle version de la LoRA du personnage sur les planches gardees (pod a lui, supprime a la fin)."""
        slug = b["slug"]
        self._libre()
        p, bb = self.at.perso(slug), self._b(slug)
        passages = max(4, min(int(b.get("passages") or 30), 60))
        dv = self.devis(slug, passages)
        if dv["images"] < 10:
            raise ValueError(f"il faut au moins 10 planches gardées ({dv['images']} pour l'instant) ; 20 à 40 donnent un meilleur résultat")
        if dv["minutes"] > 70:
            raise ValueError(f"entraînement trop long ({dv['minutes']} min estimées, 70 au plus) : garder moins d'images ou baisser les passages")
        dep = self.at.depense()
        if dep and dep["jour"] + dv["usd"] > dep["plafond"]:
            raise ValueError(f"plafond du jour : {dv['usd']:.2f} $ estimés, il reste {dep['plafond'] - dep['jour']:.2f} $")
        ver = max([int(x["v"]) for x in bb["loras"]] or [0]) + 1
        nom = f"girls-ai-{slug}-v{ver}"
        jeu = self.at.data / "work" / f"girls-ai-train-{slug}"
        shutil.rmtree(jeu, ignore_errors=True)
        jeu.mkdir(parents=True)
        for k, x in bb["planches"].items():
            if x.get("garde"):
                shutil.copy(self.fichier(slug, k), jeu / k)
                (jeu / k).with_suffix(".txt").write_text(x.get("legende") or self._prefixe(p), encoding="utf-8")
        pre = self._prefixe(p)
        essais = [{"sortie": f"e_{ver}_{int(f * 10)}_{i + 1}", "prompt": f"{pre}vertical {e}{FIN}", "seed": 900 + i, "force": f} for i, e in enumerate(ESSAIS) for f in FORCES]
        log = self._lancer(slug, "entrainement", {"nom": nom, "images": str(jeu), "passages": passages, "delai_min": 80, "essais": essais}, len(essais), veille=False)
        bb["loras"].append({"v": ver, "nom": nom, "etat": "en cours", "date": time.strftime("%d/%m/%Y %H:%M"), "passages": passages, "images": dv["images"],
                            "log": str(log), "fichier": "", "cout": None})
        self._ecrire(slug, bb)
        return {"lance": nom, **dv}

    def adopter(self, b):
        """La LoRA entrainee devient celle du personnage, a la force choisie ; l'ancienne est notee dans l'historique."""
        slug, bb = b["slug"], self._b(b["slug"])
        self.vue(slug)
        bb = self._b(slug)
        lo = next((x for x in bb["loras"] if x["nom"] == b.get("lora") and x.get("fichier")), None)
        if not lo:
            raise ValueError("LoRA pas prête")
        p = dict(self.at.perso(slug))
        g = dict(p.get("generation") or {})
        bb["historique"].append({"lora": g.get("lora") or "", "force": g.get("lora_strength"), "date": time.strftime("%d/%m/%Y %H:%M")})
        g["lora"], g["lora_strength"] = lo["fichier"], max(0.5, min(float(b.get("force") or 1.3), 2.0))
        p["generation"] = g
        self.at.save_perso(p)
        self._ecrire(slug, bb)
        (self.dir(slug) / "n_1.png").unlink(missing_ok=True)  # l'image de depart de la cabine sera refaite avec la LoRA en place
        return self.vue(slug)

    def revenir(self, b):
        """Remet la LoRA d'avant (derniere ligne de l'historique)."""
        slug, bb = b["slug"], self._b(b["slug"])
        if not bb["historique"]:
            raise ValueError("pas de LoRA précédente")
        h = bb["historique"].pop()
        p = dict(self.at.perso(slug))
        p["generation"] = dict(p.get("generation") or {}) | {"lora": h["lora"], "lora_strength": h["force"] or 1.0}
        self.at.save_perso(p)
        self._ecrire(slug, bb)
        (self.dir(slug) / "n_1.png").unlink(missing_ok=True)  # l'image de depart de la cabine sera refaite avec la LoRA en place
        return self.vue(slug)

    # --- Routes -----------------------------------------------------------------------------------
    def get(self, path, q):
        if path == "/api/a/b":
            return self.vue(q.get("slug", [""])[0])
        if path == "/api/a/b/devis":
            return self.devis(q.get("slug", [""])[0], max(4, min(int(q.get("passages", ["30"])[0] or 30), 60)))
        return None

    def post(self, path, b):
        f = {"/api/a/b/creer": self.creer, "/api/a/b/ajouter": self.ajouter, "/api/a/b/retirer": self.retirer, "/api/a/b/choix": self.choix,
             "/api/a/b/visage": self.visage, "/api/a/b/corps": self.corps, "/api/a/b/texte": self.texte, "/api/a/b/refaire": self.refaire, "/api/a/b/expressions": self.expressions, "/api/a/b/planches": self.planches, "/api/a/b/garde": self.garde, "/api/a/b/supprimer": self.supprimer, "/api/a/b/entrainer": self.entrainer,
             "/api/a/b/adopter": self.adopter, "/api/a/b/revenir": self.revenir, "/api/a/b/importer": self.importer, "/api/a/b/essayer": self.essayer,
             "/api/a/b/banc": self.banc, "/api/a/b/banc/noter": self.banc_noter, "/api/a/b/banc/retirer": self.banc_retirer,
             "/api/a/b/banc/depart": self.banc_depart, "/api/a/b/banc/depart/retirer": self.banc_depart_retirer}.get(path)
        if not f:
            return None
        with self.at.lock:
            return f(b)
