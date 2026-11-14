"""Atelier : du personnage a la video montee.

Socle : les personnages (fiche, ton, reglages de generation). Au-dessus : les projets, un par video.
Un projet suit cinq etapes : idee, scenario (scenes, textes a l'ecran, voix), images, clips, montage.
L'ecriture est confiee au redacteur IA (server/writer, file d'attente dans data/ecriture) ; s'il ne
repond pas, un redacteur de secours (moteur_local.py) tire un scenario d'une structure toute faite.
Les images et les clips passent par le pilote, donc par le plafond GPU du jour.

Un projet couvre quatre temps : 1 accroche tous publics, 2 montee suggestive, 3 devoile (nudite, sans
acte), 4 final prive. Chaque scene porte son temps. Le redacteur ecrit les temps 1 et 2 ; les temps 3 et 4
sont a la main du proprietaire, ou alimentes par un plan depose par son agent dans server/jobs/atelier/.
Bibliotheque de LoRA : catalogue du pilote (production.yaml et data/lora_catalog.yaml), LoRA par defaut de
chaque temps (data/lora_defauts.json), inventaire du volume releve par le pilote (data/lora_volume.json).

Donnees : data/personnages/<slug>.json, data/projets/<id>/ (projet.json, runs/, media/, final_vN.mp4),
data/ecriture/ (demandes et reponses du redacteur), data/audio/ (musiques deposees par le proprietaire).
"""
import base64
import datetime
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from pathlib import Path

import moteur_local
from controle import CIBLE, controle

AGE_MIN = 21
ETAPES = ("idee", "ecrit", "images", "clips", "monte", "valide")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TEMPS = {1: "accroche", 2: "montee", 3: "devoile", 4: "final"}
V = 4            # version des donnees : 4 = quatre temps (l'ancien temps 3, le final, est devenu le temps 4)
MODELE_4T = "2026-11-14f"  # premier modele de plans a quatre temps : avant lui, "temps: 3" designait le final
FORMATS = {"vertical": (1080, 1920), "carre": (1080, 1080), "paysage": (1920, 1080)}

SYSTEME = """Tu es scénariste, dialoguiste et monteur de teasers vidéo courts pour un personnage fictif, adulte, généré par IA et présenté comme tel. Tu écris pour vendre : la vidéo doit arrêter le pouce dans la première seconde, faire monter l'envie, couper juste avant la suite et envoyer vers la page payante du personnage.

REGISTRE
Classe, sensuel, aguicheur. Suggestif, jamais explicite : pas de nudité, pas d'acte sexuel, pas de mot cru. Tout passe par le regard, la tenue, le décolleté, le geste lent, le cadrage, le sous-entendu et l'ellipse. Ce qui n'est pas montré vend mieux que ce qui l'est. Le personnage a de l'humour et une vraie personnalité : sers-toi de ses tics, de ses défauts, de son univers.

CE QUI FAIT CLIQUER
- Première scène : une accroche lisible en une seconde (adresse directe, POV, défi, question, promesse, interruption).
- L'accroche est vraie dès la première image : ce qu'elle annonce se voit déjà dans la première scène (si elle dit qu'elle a fait le café, la tasse est à l'image ; si elle dit « attends la fin », quelque chose est déjà amorcé). Une accroche que l'image contredit ou n'illustre pas fait partir le spectateur.
- Une boucle ouverte : quelque chose commence et ne se termine pas dans la vidéo.
- Une progression nette : chaque scène va un cran plus loin que la précédente (distance à la caméra, regard, tenue, geste).
- Dernière scène : la coupe arrive au moment où l'on veut voir la suite, avec un appel à l'action court et concret.
- Lisible sans le son : le texte à l'écran porte l'histoire.

CONTRAINTES TECHNIQUES (modèles d'image et de vidéo)
- Chaque scène = une image de départ, puis un clip de 5 secondes animé à partir de cette image.
- "continuite" : la fiche de continuité du projet, en anglais, écrite une seule fois et ajoutée automatiquement à la fin de chaque "still". "lieu" (commence par "in"/"on" : pièce, mobilier, couleurs), "tenue" (commence par "wearing"), "cheveux" (coiffure du jour, ou ""), "lumiere", "pdv" (point de vue de la caméra, par exemple "shot at eye level on a phone"). Un champ ne contient que ce qui reste identique pendant toute la vidéo ; si un élément change en cours de route (elle change de pièce, elle retire une veste), laisse ce champ vide et écris l'élément dans chaque "still".
- "still" : en anglais, une seule phrase dense : cadrage, pose, expression, et rien de ce qui est déjà dans la fiche de continuité. Format vertical. Une seule personne à l'image. Ne décris ni le visage, ni les cheveux, ni les tatouages, ni les bijoux : ils sont ajoutés automatiquement. Aucun texte dans l'image.
- "motion" : en anglais, UN geste simple et lent, en une phrase commençant par "She". Gestes fiables : regarder l'objectif, sourire lentement, pencher la tête, se mordre la lèvre, se pencher vers la caméra, marcher vers la caméra, faire glisser une bretelle, ajuster un décolleté, s'étirer doucement, boire, respirer. Gestes interdits (ils ratent) : tourner le dos, attacher ses cheveux, passer la main devant le visage, renverser la tête, éclater de rire, cheveux au vent, manipuler un objet compliqué, changer de vêtement.
- "end_edit" : presque toujours "". À remplir seulement si la pose doit changer nettement entre le début et la fin du clip (assise puis debout) : une phrase en anglais qui décrit la pose finale, même cadrage.
- "raccord" : "coupe" (la scène a sa propre image, le montage coupe : changement de cadrage ou d'angle) ou "continu" (la scène prolonge la précédente sans coupe visible : son clip démarre sur la dernière image du clip précédent, même cadrage, le geste s'enchaîne). Utilise "continu" quand deux gestes se suivent dans le même cadre ; pas plus de deux scènes continues de suite, et jamais sur la première scène. Le "still" d'une scène continue décrit quand même l'image attendue à cet instant.
- "texte" : texte incrusté pendant la scène, dans la langue du personnage, 7 mots au plus. Aucun emoji, ni là ni dans l'accroche (la police de montage ne les affiche pas). "voix" : phrase de voix off dans sa voix, 12 mots au plus, ou "".
- "cran" : niveau de la scène dans la progression, entier de 1 (anodin) à 5 (le plus osé du temps, toujours suggestif). Il ne redescend jamais d'une scène à la suivante et la dernière scène porte le plus haut.
- "tattoos" : false si la tenue couvre les épaules et la poitrine (pull, peignoir fermé), sinon true.
- "role" : "accroche", "montee" ou "chute".
- Le personnage ne prétend jamais être une personne réelle. Aucune personne réelle, aucune marque, aucun mineur, rien qui évoque la jeunesse.

SORTIE
Un seul objet JSON valide, sans texte autour, sans bloc de code. Les champs "titre" et "pitch" sont en français ; les textes publiés (accroche, texte, voix, legende, cta, hashtags) sont dans la langue du personnage."""

SCHEMA = ('{"titre": "...", "pitch": "une phrase", "accroche": "texte à l\'écran de la première seconde", '
          '"continuite": {"lieu": "...", "tenue": "...", "cheveux": "", "lumiere": "...", "pdv": "..."}, '
          '"scenes": [{"titre": "...", "role": "accroche|montee|chute", "raccord": "coupe|continu", "still": "...", "motion": "...", "end_edit": "", '
          '"texte": "...", "voix": "", "cran": 1, "tattoos": true}], "legende": "légende de la publication, 1 à 2 phrases, avec l\'appel à l\'action", '
          '"cta": "carton de fin, 6 mots au plus", "hashtags": "3 à 5 mots-dièse"}')


RELECTEUR = """Tu es chef monteur et tu relis les images fixes d'une vidéo verticale courte avant qu'on paie le calcul des clips. Le personnage est fictif, adulte, généré par IA et présenté comme tel. Chaque image est le point de départ d'un clip de 5 secondes animé par un modèle vidéo.

Tu reçois les images dans l'ordre des scènes, puis la fiche de continuité et la description de chaque scène. Pour chaque image, cherche ce qui gâcherait la vidéo :
- le personnage n'est pas la même personne que sur les autres images (visage, cheveux, corpulence) ;
- le lieu, la tenue, la coiffure ou la lumière ne sont pas ceux de la fiche de continuité, ou changent d'une image à l'autre sans que la scène le demande ;
- un défaut d'anatomie ou de rendu : mains, doigts, membres, dents, regard, objet déformé, texte ou logo parasite, peau plastique ;
- l'image ne montre pas ce que la scène décrit (cadrage, pose, objet), ou le geste demandé pour le clip ne peut pas partir de cette pose ;
- la première image ne montre pas ce que l'accroche annonce, ou la contredit (l'accroche est donnée avec les scènes quand il y en a une) ;
- le point de vue est incohérent avec celui de la fiche (par exemple un téléphone en main alors que c'est lui qui filme) ;
- le cadrage vertical est mauvais : visage coupé, sujet trop petit, place manquante en haut pour le texte à l'écran.
Ne signale que ce qui se voit vraiment. Une image correcte est "ok" : ne cherche pas la petite bête. Tu ne juges ni l'idée ni le registre de la vidéo, seulement la fabrication.

SORTIE
Un seul objet JSON valide, sans texte autour, sans bloc de code, en français :
{"scenes": [{"id": "identifiant de la scène", "verdict": "ok" ou "a_refaire", "constat": "ce qui ne va pas, une phrase ; vide si ok", "consigne": "ce qu'il faut faire : autre prise telle quelle, ou ce qu'il faut changer dans la description de l'image ; vide si ok"}], "ensemble": "une ou deux phrases sur la cohérence de la série"}"""


ANALYSTE = """Tu es chef monteur et tu critiques une vidéo verticale courte déjà montée, avant sa publication. Le personnage est fictif, adulte, généré par IA et présenté comme tel. La vidéo est faite de clips de 5 secondes animés par un modèle vidéo, parfois raccourcis au montage.

Tu ne vois pas la vidéo : tu reçois des images qui en sont extraites, chacune avec son instant et son rôle (première image, milieu d'une scène, dernière image avant une jointure, première image après), puis la fiche technique du montage et le scénario. Tu ne peux donc juger ni le mouvement, ni le rythme réel, ni le son : n'en dis rien.

Ce que tu cherches, du plus grave au moins grave :
- la première seconde : y a-t-il une raison de rester (regard, geste amorcé, texte d'accroche lisible et intrigant), ou une image d'attente ; l'accroche est-elle vraie dès la première image (ce qu'elle annonce se voit, rien ne la contredit) ;
- les jointures annoncées « sans coupe » : compare l'image d'avant et celle d'après ; elles doivent être presque identiques (pose, cadrage, couleurs) ; tout saut se verra ;
- les jointures « coupe » : le changement de cadrage est-il franc (un cadrage trop proche du précédent donne un saut maladroit) ; le lieu, la tenue, la coiffure et la lumière restent-ils les mêmes quand le scénario ne demande pas de changement ;
- le personnage est-il la même personne partout ; défauts de rendu visibles (mains, doigts, visage, objet déformé) ;
- les textes à l'écran : lisibles, pas sur le visage, pas deux à la fois, pas trop longs pour leur durée, sans faute ;
- la progression : la vidéo monte-t-elle, la dernière scène est-elle la plus forte, la fin laisse-t-elle une envie de suite ;
- le carton de fin et la mention « AI character » : présents et lisibles.
Ne signale que ce qui se voit sur les images ou se déduit de la fiche. Pas de compliment de politesse. Chaque point propose une correction faisable dans l'atelier : refaire une prise, changer la description d'une scène, changer un raccord, raccourcir ou retirer une scène, changer un texte, remonter avec une autre durée visée.

SORTIE
Un seul objet JSON valide, sans texte autour, sans bloc de code, en français :
{"verdict": "publiable" ou "a_reprendre", "points": [{"moment": "instant ou scène concernés, par exemple 0-2 s, scène 2, jointure 1", "grave": true ou false, "constat": "ce qui ne va pas, une phrase", "proposition": "quoi faire, une phrase"}], "forces": "ce qui marche et qu'il faut garder, une phrase", "ensemble": "le jugement d'ensemble en deux phrases au plus"}
Six points au plus, les plus graves d'abord. "a_reprendre" seulement s'il y a au moins un point grave."""


RACCORDS = ("coupe", "continu", "arrivee")
# Fiche de continuite d'un projet : ce qui ne doit pas changer d'une image a l'autre. Texte anglais, ajoute a chaque "still".
CONT = ("lieu", "tenue", "cheveux", "lumiere", "pdv")
CIBLES = (0, 15, 20, 30)  # duree visee d'un montage, en secondes (0 : tout garder)
PLANCHER = 2.0  # un plan raccourci pour tenir la duree visee garde au moins cette duree
NOIR = 0.4  # fondu au noir de la fin
FIXE = 2.0  # duree d'une image fixe (scene sans clip), en zoom lent
FONDU_JOINT = 4  # images de fondu a un raccord sans coupe
STYLES = {"doux": ("Poppins-SemiBold.ttf", 1.0, False), "contour": ("Poppins-SemiBold.ttf", 1.0, True),
          "serif": ("DMSerifDisplay-Italic.ttf", 1.2, False)}  # texte a l'ecran : (police, echelle, contour)
JOINT = 1 / 32  # a un raccord continu, la premiere image du clip suivant repete la derniere du precedent : elle est retiree


def _cont(d):
    d = d if isinstance(d, dict) else {}
    return {k: _s(d.get(k), 300) for k in CONT}


def _prec(p):
    """Scene precedente de chaque scene dans son temps (None pour la premiere)."""
    out, der = {}, {}
    for s in p["scenes"]:
        out[s["id"]] = der.get(s["temps"])
        der[s["temps"]] = s
    return out


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return default


def _dump(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _s(x, n=2000):
    return " ".join(str(x or "").split())[:n]


JOURS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre")
# Reperes a date fixe (mois, jour) ; le redacteur complete de lui-meme les fetes mobiles.
REPERES = (((1, 1), "jour de l'an"), ((1, 6), "galette des rois"), ((2, 2), "Chandeleur"), ((2, 14), "Saint-Valentin"), ((3, 20), "début du printemps"),
           ((4, 1), "1er avril"), ((5, 1), "1er mai"), ((6, 21), "début de l'été, fête de la musique"), ((7, 14), "14 juillet"), ((8, 15), "15 août"),
           ((9, 1), "rentrée"), ((9, 22), "début de l'automne"), ((10, 31), "Halloween"), ((11, 1), "Toussaint"), ((11, 11), "11 novembre"),
           ((12, 21), "début de l'hiver"), ((12, 25), "Noël"), ((12, 31), "réveillon du nouvel an"))


def _date(x):
    """Date du personnage : "AAAA-MM-JJ" valide, sinon ""."""
    try:
        return datetime.date.fromisoformat(str(x or "").strip()).isoformat()
    except ValueError:
        return ""


def _moment(d, contexte=""):
    """Decrit au redacteur la date du personnage (fictive) : jour, saison (hemisphere nord), reperes a dix jours pres."""
    if not _date(d):
        return ""
    j = datetime.date.fromisoformat(d)
    saison = "hiver" if (j.month, j.day) < (3, 20) or (j.month, j.day) >= (12, 21) else "printemps" if (j.month, j.day) < (6, 21) \
        else "été" if (j.month, j.day) < (9, 22) else "automne"
    pres = []
    for (m, q), nom in REPERES:
        for an in (j.year - 1, j.year, j.year + 1):
            e = (datetime.date(an, m, q) - j).days
            if abs(e) <= 10:
                pres.append(f"{nom} ({'le jour même' if e == 0 else f'dans {e} j' if e > 0 else f'il y a {-e} j'})")
    return (f"MOMENT\nDate du personnage (fictive : le jour où elle vit la scène, pas la date réelle d'aujourd'hui) : {JOURS[j.weekday()]} {j.day} "
            f"{MOIS[j.month - 1]} {j.year}, {saison}.\n{'Repères proches : ' + ' ; '.join(pres) + chr(10) if pres else ''}"
            f"{'Contexte du moment donné par le propriétaire : ' + contexte + chr(10) if contexte else ''}"
            "Ancre la vidéo dans ce moment : activité, tenue, lumière et météo de saison dans \"still\" (heure du jour cohérente avec la durée du jour), "
            "allusions naturelles dans les textes. N'écris pas la date elle-même. N'invente aucune actualité réelle et ne cite aucune personne réelle : "
            "seuls les repères ci-dessus et le contexte donné comptent.\n\n")


def _json_de(texte):
    """Extrait l'objet JSON d'une reponse du redacteur (tolere un bloc de code ou une phrase autour)."""
    a, b = texte.find("{"), texte.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("réponse du rédacteur illisible")
    return json.loads(texte[a:b + 1])


def _loras(x):
    """LoRA supplementaires d'une scene, en texte : "nom:0.6, autre"."""
    if isinstance(x, list):
        x = ", ".join(f"{i['name']}:{i['strength']}" if isinstance(i, dict) and i.get("strength") is not None
                      else str(i.get("name", "")) if isinstance(i, dict) else str(i) for i in x)
    return ", ".join(p for p in (re.sub(r"[^A-Za-z0-9_.:-]", "", p) for p in str(x or "").split(",")) if p)[:300]


def _loras_plan(txt):
    out = []
    for p in txt.split(", ") if txt else []:
        nom, _, force = p.partition(":")
        try:
            out.append({"name": nom, "strength": float(force)} if force else nom)
        except ValueError:
            out.append(nom)
    return out


class Atelier:
    def __init__(self, data: Path, repo: Path, studio):
        self.data, self.repo, self.studio = data, repo, studio
        self.dp, self.dj, self.de, self.da = data / "personnages", data / "projets", data / "ecriture", data / "audio"
        self.dd = repo / "server" / "jobs" / "atelier"  # plans deposes par l'agent du proprietaire (lecture seule ici)
        for d in (self.dp, self.dj, self.de, self.da):
            d.mkdir(parents=True, exist_ok=True)
        os.chmod(self.de, 0o777)  # le redacteur tourne sur le serveur sous un autre compte que le conteneur
        self.lock = threading.Lock()
        self.montages = {}  # id du projet -> fil de montage en cours
        self.job = None     # {"projet", "quoi", "log"} : dernier lancement du pilote par l'atelier
        self.ch = None      # chaine de production en cours ou derniere chaine (voir chaine())
        self._migrer()
        c = _load(data / "chaine.json")  # une chaine en pause survit au redemarrage de l'interface
        if c and c.get("etat") == "pause":
            self.ch = c
        elif c and c.get("etat") == "en cours":
            self.ch = {**c, "etat": "erreur", "erreur": "interface redémarrée pendant la chaîne : la relancer, elle ne recalcule que ce qui manque"}
        self._dep = (0, None)

    def _migrer(self):
        """Passage de trois a quatre temps (14/11/2026) : dans les donnees d'avant, le temps 3 etait le final. Il devient
        le temps 4 (scenes, videos montees, planches, fiches de montage, chaine en pause). Fait une fois par projet."""
        for d in sorted(self.dj.glob("p[0-9][0-9][0-9][0-9]")):
            p = _load(d / "projet.json")
            if not p or p.get("v") == V:
                continue
            for s in p.get("scenes") or []:
                if s.get("temps") == 3:
                    s["temps"] = 4
            for f in sorted(d.glob("final_t3_v*.mp4")) + sorted(d.glob("planche_t3_v*.jpg")):
                f.rename(d / f.name.replace("_t3_", "_t4_", 1))
            for nom in ("finals.json", "analyse.json"):
                j = _load(d / nom)
                if j:
                    _dump(d / nom, {k.replace("final_t3_", "final_t4_"): v for k, v in j.items()})
            m = _load(d / "montage.json")
            if m and str(m.get("fichier") or "").startswith("final_t3_"):
                _dump(d / "montage.json", m | {"fichier": m["fichier"].replace("final_t3_", "final_t4_")})
            _dump(d / "projet.json", p | {"v": V})
        c = _load(self.data / "chaine.json")
        if c and c.get("v") != V:
            _dump(self.data / "chaine.json", c | {"v": V, "temps": [4 if t == 3 else t for t in c.get("temps") or []]})

    # --- Bibliotheque de LoRA ---------------------------------------------------------------------
    def _catalogue(self):
        """Catalogue du pilote : production.yaml, puis data/lora_catalog.yaml qui prime (ecrit par "pilot lora add" et par la page)."""
        import yaml
        cat = {}
        for f, src in ((self.repo / "persona" / "production.yaml", "depot"), (self.data / "lora_catalog.yaml", "donnees")):
            if f.is_file():
                j = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                for k, v in ((j.get("lora_catalog") or {}) if src == "depot" else j).items():
                    if isinstance(v, dict):
                        cat[str(k)] = {**cat.get(str(k), {}), **v, "ou": src}
        return cat

    def _defauts(self):
        d = _load(self.data / "lora_defauts.json", {})
        return {t: _loras(d.get(str(t))) for t in TEMPS if t > 1}

    def _lib(self):
        """Ce que le controle des plans doit savoir des LoRA : fichier de chaque nom du catalogue, fichiers du volume (None si inconnu)."""
        try:
            cat = {k: str(v.get("file") or k) for k, v in self._catalogue().items()}
        except Exception:
            cat = {}
        vol = _load(self.data / "lora_volume.json", {})
        return {"cat": cat, "volume": set(vol["fichiers"]) if isinstance(vol.get("fichiers"), list) else None, "date": vol.get("date", "")}

    def _ctl(self, p, t):
        return controle(p, t, self._lib())

    def bibliotheque(self):
        """LoRA supplementaires connues : catalogue, presence sur le volume d'apres le dernier inventaire, defauts par temps."""
        try:
            cat = self._catalogue()
        except Exception:
            cat = {}
        vol = _load(self.data / "lora_volume.json", {})
        fichiers = vol["fichiers"] if isinstance(vol.get("fichiers"), list) else None
        visages = {(x.get("generation") or {}).get("lora") for x in self.persos().values()}
        try:
            import yaml
            visages |= {v for v in (yaml.safe_load((self.repo / "persona" / "production.yaml").read_text(encoding="utf-8")).get("character") or {}).values()
                        if isinstance(v, str) and v.endswith(".safetensors")}
        except Exception:
            pass
        connus = {str(v.get("file") or k) for k, v in cat.items()}
        return {"loras": [{"name": k, "label": str(v.get("label") or k), "file": str(v.get("file") or ""), "strength": float(v.get("strength", 1.0)),
                           "trigger": str(v.get("trigger") or ""), "note": str(v.get("note") or ""), "base": str(v.get("base") or ""),
                           "source": str(v.get("source") or ""), "ou": v["ou"],
                           "volume": None if fichiers is None else str(v.get("file") or k) in fichiers} for k, v in cat.items()],
                "inventaire": vol.get("date", ""),
                "hors": sorted(f for f in fichiers or [] if f not in connus and f not in visages),
                "defauts": self._defauts()}

    def save_lora(self, b):
        """Inscrit ou corrige une LoRA du catalogue (force conseillee, mots declencheurs, note), ou la retire. Ecrit dans
        data/lora_catalog.yaml, le fichier que lit le pilote. Le fichier .safetensors, lui, se depose par "pilot lora add"."""
        import yaml
        nom = str(b.get("name") or "")
        if not re.fullmatch(r"[a-z0-9_]{1,40}", nom):
            raise ValueError("nom court : lettres minuscules, chiffres, tirets bas")
        f = self.data / "lora_catalog.yaml"
        with self.lock:
            cat = (yaml.safe_load(f.read_text(encoding="utf-8")) or {}) if f.is_file() else {}
            if b.get("supprimer"):
                if nom not in cat:
                    raise ValueError("cette LoRA est inscrite dans persona/production.yaml : elle se retire dans ce fichier")
                del cat[nom]
            else:
                fichier = str(b.get("file") or "").strip()
                if not re.fullmatch(r"[A-Za-z0-9_.\-/ ]{1,200}\.safetensors", fichier):
                    raise ValueError("fichier : nom du .safetensors tel qu'il est sur le volume")
                try:
                    force = float(b.get("strength") or 0)
                except (TypeError, ValueError):
                    force = 0
                if not 0 < force <= 2:
                    raise ValueError("force conseillée : entre 0,1 et 2")
                cat[nom] = {**self._catalogue().get(nom, {}), **cat.get(nom, {}), "label": _s(b.get("label"), 80) or nom, "file": fichier,
                            "strength": round(force, 2), "trigger": _s(b.get("trigger"), 200), "note": _s(b.get("note"), 300)}
                cat[nom].pop("ou", None)
            f.write_text(yaml.safe_dump(cat, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return self.bibliotheque()

    def save_defauts(self, b):
        """LoRA par defaut de chaque temps (2 a 4) : posees sur les scenes ajoutees a la main ou importees sans "loras"."""
        lib, out = self._lib(), {}
        for t in TEMPS:
            txt = _loras((b.get("defauts") or {}).get(str(t)))
            if t == 1 or not txt:
                continue
            for x in _loras_plan(txt):
                n = x["name"] if isinstance(x, dict) else x
                if n not in lib["cat"] and not n.endswith(".safetensors"):
                    raise ValueError(f"temps {t} : « {n} » n'est pas dans le catalogue")
            out[str(t)] = txt
        _dump(self.data / "lora_defauts.json", out)
        return self.bibliotheque()

    # --- Personnages ------------------------------------------------------------------------------
    def persos(self):
        out = {}
        for d in (self.repo / "persona" / "personnages", self.dp):  # le dossier de donnees prime
            for f in sorted(d.glob("*.json")) if d.is_dir() else []:
                p = _load(f)
                if p and p.get("slug"):
                    out[p["slug"]] = p
        return out

    def perso(self, slug):
        p = self.persos().get(str(slug))
        if not p:
            raise ValueError("personnage inconnu")
        return p

    def save_perso(self, b):
        slug = re.sub(r"[^a-z0-9_]+", "_", str(b.get("slug") or b.get("nom") or "").lower()).strip("_")[:24]
        if not slug or not _s(b.get("nom")):
            raise ValueError("nom du personnage obligatoire")
        try:
            age = int(b.get("age") or 0)
        except ValueError:
            age = 0
        if age < AGE_MIN:
            raise ValueError(f"âge obligatoire, {AGE_MIN} ans au moins : les personnages sont des adultes")
        fiche, ecr, gen = b.get("fiche") or {}, b.get("ecriture") or {}, b.get("generation") or {}
        prefix = _s(gen.get("zimage_prefix"), 400)
        if prefix and not prefix.endswith(","):
            prefix += ","
        p = {"slug": slug, "nom": _s(b["nom"], 60), "statut": b.get("statut") if b.get("statut") in ("actif", "archive") else "actif",
             "age": age, "langue": _s(b.get("langue") or "en", 5), "accroche": _s(b.get("accroche"), 200),
             "fiche": {k: _s(fiche.get(k), 1500) for k in ("identite", "apparence", "voix", "personnalite", "seduction", "univers", "limites")},
             "lieux": [_s(x, 300) for x in b.get("lieux") or [] if _s(x)][:30],
             "tenues": [_s(x, 300) for x in b.get("tenues") or [] if _s(x)][:30],
             "ecriture": {k: _s(ecr.get(k), 400) for k in ("ton", "cta", "plateforme", "hashtags", "interdits")},
             "generation": {"zimage_prefix": (prefix + " ") if prefix else "", "lora": _s(gen.get("lora"), 120),
                            "lora_strength": float(gen.get("lora_strength") or 1.0), "corps": _s(gen.get("corps"), 600),
                            "suffixe": _s(gen.get("suffixe"), 400), "note": _s(gen.get("note"), 400)}}
        _dump(self.dp / f"{slug}.json", p)
        return p

    def char_override(self, p):
        """Reglages du personnage a poser sur ceux de production.yaml dans un fichier de plans."""
        g = p.get("generation") or {}
        o = {"name": p["nom"], "zimage_prefix": g.get("zimage_prefix") or f"a {p.get('age', 25)} year old woman, ",
             "lora_still_zimage": g.get("lora") or "", "lora_still_zimage_strength": float(g.get("lora_strength") or 1.0),
             "zimage_tattoos": "", "zimage_body": (g["corps"].rstrip(", ") + ", ") if g.get("corps") else ""}
        if g.get("suffixe"):
            o["zimage_suffix"] = g["suffixe"]
        return o

    # --- Projets ----------------------------------------------------------------------------------
    def _pdir(self, pid):
        if not re.fullmatch(r"p\d{4}", str(pid)):
            raise ValueError("identifiant de projet invalide")
        d = self.dj / str(pid)
        if not d.is_dir():
            raise FileNotFoundError(pid)
        return d

    def _raw(self, pid):
        p = _load(self._pdir(pid) / "projet.json")
        if not p:
            raise FileNotFoundError(pid)
        for s in p.get("scenes") or []:  # projets d'avant le decoupage en temps
            s.setdefault("temps", 1), s.setdefault("loras", ""), s.setdefault("origine", "")
            s.setdefault("raccord", "coupe"), s.setdefault("libre", False), s.setdefault("cran", 0)
        p["continuite"] = _cont(p.get("continuite"))
        p.setdefault("reference", "")
        p.setdefault("brief2", ""), p.setdefault("nb2", 3), p.setdefault("depots", {})
        p.setdefault("date_perso", ""), p.setdefault("contexte", "")
        return p

    def _scene(self, d, proj):
        sid = d.get("id") if re.fullmatch(r"s\d+", str(d.get("id") or "")) else None
        if not sid:
            sid = f"s{proj['next']}"
            proj["next"] += 1
        return {"id": sid, "titre": _s(d.get("titre"), 80), "role": d.get("role") if d.get("role") in ("accroche", "montee", "chute") else "montee",
                "temps": int(d.get("temps") or 1) if str(d.get("temps") or 1) in ("1", "2", "3", "4") else 1,
                "loras": _loras(d.get("loras")), "origine": _s(d.get("origine"), 120),
                "raccord": d.get("raccord") if d.get("raccord") in RACCORDS else "coupe", "libre": bool(d.get("libre")),
                "cran": min(5, max(0, int(d.get("cran") or 0))) if str(d.get("cran") or 0).isdigit() else 0,
                "still": _s(d.get("still"), 1200), "motion": _s(d.get("motion"), 600), "end_edit": _s(d.get("end_edit"), 600),
                "texte": _s(d.get("texte"), 120), "voix": _s(d.get("voix"), 240), "tattoos": bool(d.get("tattoos", True)),
                "seed": int(d.get("seed") or random.randint(1, 999999)), "image": _s(d.get("image"), 80), "clip": _s(d.get("clip"), 80),
                "debut": max(0.0, float(d.get("debut") or 0)), "duree": max(0.0, float(d.get("duree") or 0))}

    def save_projet(self, b):
        with self.lock:
            pid = b.get("id")
            if pid:
                old = self._raw(pid)
            else:
                self.perso(b.get("personnage"))
                nums = [int(d.name[1:]) for d in self.dj.iterdir() if re.fullmatch(r"p\d{4}", d.name)]
                pid = f"p{max(nums, default=0) + 1:04d}"
                (self.dj / pid / "media").mkdir(parents=True)
                old = {"id": pid, "personnage": b["personnage"], "cree": time.strftime("%Y-%m-%d %H:%M"), "next": 1,
                       "date_perso": time.strftime("%Y-%m-%d")}
            m = b.get("montage") or old.get("montage") or {}
            p = {"id": pid, "v": V, "personnage": old["personnage"], "cree": old.get("cree"), "modifie": time.strftime("%Y-%m-%d %H:%M"),
                 "next": int(old.get("next") or 1), "titre": _s(b.get("titre", old.get("titre")), 100) or "Sans titre",
                 "statut": b.get("statut", old.get("statut")) if b.get("statut", old.get("statut")) in ("", "valide", "publie", "archive") else "",
                 "brief": _s(b.get("brief", old.get("brief")), 1500), "suite": _s(b.get("suite", old.get("suite")), 600),
                 "nb_scenes": max(2, min(int(b.get("nb_scenes", old.get("nb_scenes")) or 3), 8)),
                 "brief2": _s(b.get("brief2", old.get("brief2")), 1500), "nb2": max(2, min(int(b.get("nb2", old.get("nb2")) or 3), 6)),
                 "depots": old.get("depots") or {}, "continuite": _cont(b.get("continuite", old.get("continuite"))),
                 # date_perso : date fictive, celle du jour ou le personnage vit la scene ; cree et modifie : dates reelles
                 "date_perso": _date(b.get("date_perso", old.get("date_perso"))), "contexte": _s(b.get("contexte", old.get("contexte")), 400),
                 "pitch": _s(b.get("pitch", old.get("pitch")), 400), "accroche": _s(b.get("accroche", old.get("accroche")), 120),
                 "legende": _s(b.get("legende", old.get("legende")), 600), "cta": _s(b.get("cta", old.get("cta")), 120),
                 "hashtags": _s(b.get("hashtags", old.get("hashtags")), 200), "attente": old.get("attente") or "",
                 "montage": {"transition": m.get("transition") if m.get("transition") in ("coupe", "fondu") else "coupe",
                             "format": m.get("format") if m.get("format") in FORMATS else "vertical",
                             "textes": bool(m.get("textes", True)), "carton": bool(m.get("carton", True)),
                             "label": bool(m.get("label", False)), "musique": _s(m.get("musique"), 120),
                             "cible": int(m.get("cible") or 0) if int(m.get("cible") or 0) in CIBLES else 0,
                             "noir": bool(m.get("noir", True)),
                             "style": m.get("style") if m.get("style") in STYLES else "doux"}}
            p["scenes"] = [self._scene(s, p) for s in (b["scenes"] if "scenes" in b else old.get("scenes") or [])][:30]
            ref = b.get("reference", old.get("reference"))
            p["reference"] = ref if ref in [s["id"] for s in p["scenes"] if s["temps"] == 1] else ""
            if p["statut"] in ("valide", "publie") and old.get("statut") not in ("valide", "publie"):
                bloc = [x["msg"] for x in self.publication(p) if x["grave"]]
                if bloc:
                    raise ValueError("Validation refusée. " + " ".join(bloc))
            _dump(self.dj / pid / "projet.json", p)
            return p

    def prises(self, pid):
        """Prises de chaque scene, de la plus ancienne a la plus recente. "source" : image dont un clip est tire ;
        "depuis" : clip dont une image est la derniere image (scene continue) ; "fin" : image sur laquelle un clip arrive."""
        d, out, runs = self._pdir(pid), {}, {}
        for f in sorted((d / "media").iterdir(), key=lambda f: f.stat().st_mtime):
            m = re.fullmatch(rf"{pid}(r\d+)_(s\d+)\.(png|mp4)", f.name)
            if not m:
                continue
            if m.group(1) not in runs:
                runs[m.group(1)] = {x["name"]: x for x in (_load(d / "runs" / f"{m.group(1)}.json") or {}).get("shots", [])}
            sh = runs[m.group(1)].get(m.group(2)) or {}
            t = out.setdefault(m.group(2), {"images": [], "clips": [], "source": {}, "depuis": {}, "fin": {}})
            if m.group(3) == "png":
                t["images"].append(f.name)
                if sh.get("depuis"):
                    t["depuis"][f.name] = sh["depuis"]
                continue
            t["clips"].append(f.name)
            t["source"][f.name] = f"{pid}{m.group(1)}_{m.group(2)}.png" if sh.get("suite_de") else Path(sh.get("image") or "").name
            if sh.get("end_image"):
                t["fin"][f.name] = Path(sh["end_image"]).name
        return out

    def _choix(self, p, pr=None):
        """Prise retenue pour chaque scene : celle choisie si elle existe encore, sinon la derniere.
        Un clip ne compte que s'il a ete tire de l'image retenue. Raccords : l'image d'une scene continue ne compte que si
        elle sort du clip retenu de la scene precedente ; le clip qui precede une scene "arrivee" ne compte que s'il finit
        sur l'image retenue de cette scene. Changer une prise en amont rend donc la suite a refaire."""
        pr = pr if pr is not None else self.prises(p["id"])
        vide = {"images": [], "clips": [], "source": {}, "depuis": {}, "fin": {}}
        prec, out = _prec(p), {}
        cont = {s["id"]: bool(prec[s["id"]]) and s["raccord"] == "continu" for s in p["scenes"]}
        for s in p["scenes"]:  # images des scenes qui ont la leur
            if not cont[s["id"]]:
                t = pr.get(s["id"], vide)
                out[s["id"]] = {"image": s["image"] if s["image"] in t["images"] else (t["images"][-1] if t["images"] else ""), "clip": ""}
        suiv = {prec[s["id"]]["id"]: s for s in p["scenes"] if prec[s["id"]]}
        for s in p["scenes"]:  # dans l'ordre : le clip d'une scene decide de l'image de la scene continue qui la suit
            t = {**vide, **pr.get(s["id"], vide)}
            if cont[s["id"]]:
                amont = out[prec[s["id"]]["id"]]["clip"]
                imgs = [i for i in t["images"] if amont and t["depuis"].get(i) == amont]
                out[s["id"]] = {"image": s["image"] if s["image"] in imgs else (imgs[-1] if imgs else ""), "clip": ""}
            img = out[s["id"]]["image"]
            clips = [c for c in t["clips"] if img and t["source"].get(c) == img]
            nx = suiv.get(s["id"])
            if nx and nx["raccord"] == "arrivee" and out[nx["id"]]["image"]:
                clips = [c for c in clips if t["fin"].get(c) == out[nx["id"]]["image"]]
            out[s["id"]]["clip"] = s["clip"] if s["clip"] in clips else (clips[-1] if clips else "")
        return out

    def _eff(self, p, pr=None):
        """Copie du projet ou chaque scene porte la prise retenue (dans le fichier, "" veut dire : la derniere)."""
        ch = self._choix(p, pr)
        return {**p, "scenes": [{**s, **ch[s["id"]]} for s in p["scenes"]]}

    def _etape(self, p, finals):
        """Avancement du temps 1 (le teaser), celui qui se publie."""
        if p.get("statut") in ("valide", "publie"):
            return "valide"
        sc = [s for s in p["scenes"] if s["temps"] == 1]
        if not sc:
            return "idee"
        if finals:
            return "monte"
        if all(s["clip"] for s in sc):
            return "clips"
        prec = _prec(p)
        if all(s["image"] or (prec[s["id"]] and s["raccord"] == "continu") for s in sc):
            return "images"
        return "ecrit"

    def publication(self, p):
        """Ce qui s'oppose a la validation du teaser (temps 1) : remarques {"grave", "msg"}. Les graves la bloquent."""
        out = []
        r = lambda msg, grave=False: out.append({"grave": grave, "msg": msg})
        finals = self._finals(p["id"], 1)
        if not finals:
            r("Aucune vidéo montée.", True)
            return out
        info = _load(self._pdir(p["id"]) / "finals.json", {}).get(finals[-1])
        if not info or not info.get("label"):
            r(f"{finals[-1]} ne porte pas la mention « AI character » (montée avant qu'elle soit imposée) : la remonter.", True)
        if info:
            e = self._eff(p)
            if info.get("prises") != [[s["id"], s["clip"] or s["image"]] for s in e["scenes"] if s["temps"] == 1 and (s["clip"] or s["image"])]:
                r(f"{finals[-1]} ne correspond plus aux scènes ou aux prises retenues : la remonter.")
            if info.get("duree", 0) > CIBLE[1] + 1:
                r(f"{finals[-1]} dure {info['duree']:.0f} s : long pour une accroche (viser {CIBLE[1]} s ou moins).")
            if info.get("images"):
                r(f"{info['images']} scène(s) montée(s) en image fixe, sans clip.")
        if not p.get("legende"):
            r("Légende vide.")
        if not p.get("cta"):
            r("Pas d'appel à l'action : la vidéo finit sans carton.")
        return out

    def _finals(self, pid, temps=1):
        pre = "final_v" if temps == 1 else f"final_t{temps}_v"
        return sorted((f.name for f in self._pdir(pid).glob(pre + "*.mp4")), key=lambda n: int(n[len(pre):-4]))

    def projet(self, pid):
        p = self._raw(pid)
        pr = self.prises(pid)
        e = self._eff(p, pr)
        finals = {t: self._finals(pid, t) for t in TEMPS}
        mt = _load(self._pdir(pid) / "montage.json", {})
        if mt.get("etat") == "en cours" and pid not in self.montages:
            mt = {"etat": "erreur", "erreur": "montage interrompu (interface redémarrée)"}
        return {"projet": p, "choix": {s["id"]: {"image": s["image"], "clip": s["clip"]} for s in e["scenes"]}, "prises": pr,
                "finals": finals, "etape": self._etape(e, finals[1]), "montage": mt, "prod": self.prod(pid),
                "devis": {t: self.devis(e, t) for t in TEMPS}, "depots": [x for x in self.depots() if x.get("projet") == pid],
                "chaine": self.chaine_vue(pid), "controle": {t: self._ctl(p, t) for t in TEMPS}, "relecture": self.relecture(pid),
                "publication": self.publication(p), "analyses": self.analyses(pid), "infos": _load(self._pdir(pid) / "finals.json", {}),
                "planches": {n: _nom_planche(n) for n in sum(finals.values(), []) if (self._pdir(pid) / _nom_planche(n)).is_file()}}

    def liste(self):
        out = []
        for d in sorted(self.dj.glob("p*/projet.json"), reverse=True):
            p = self._raw(d.parent.name)
            if p.get("statut") == "archive":
                continue
            p = self._eff(p)
            finals = self._finals(p["id"])
            out.append({"id": p["id"], "personnage": p["personnage"], "titre": p["titre"], "pitch": p.get("pitch", ""),
                        "modifie": p.get("modifie"), "cree": p.get("cree"), "date_perso": p.get("date_perso", ""), "etape": self._etape(p, finals), "scenes": len(p["scenes"]),
                        "temps": sorted({s["temps"] for s in p["scenes"]}),
                        "vignette": next((s["image"] for s in p["scenes"] if s["image"]), ""), "final": finals[-1] if finals else ""})
        return sorted(out, key=lambda x: (x["date_perso"] or "0", x["id"]), reverse=True)  # chronologie du personnage, la plus recente d'abord

    def fichier(self, pid, name):
        d = self._pdir(pid)
        for base in (d / "media", d):
            f = (base / name).resolve()
            if f.parent == base.resolve() and f.is_file():
                return f
        raise FileNotFoundError(name)

    def depense(self):
        if time.time() - self._dep[0] > 60:
            try:
                import yaml
                rp = self.studio._rp()
                infra = yaml.safe_load((self.repo / "persona" / "production.yaml").read_text(encoding="utf-8"))["infra"]
                self._dep = (time.time(), {"jour": rp.spent_today(), "plafond": rp.daily_cap(infra)})
            except Exception:
                self._dep = (time.time(), None)
        return self._dep[1]

    def etat(self):
        return {"personnages": [{k: p.get(k) for k in ("slug", "nom", "statut", "age", "langue", "accroche")} | {"lora": bool((p.get("generation") or {}).get("lora"))}
                                for p in self.persos().values()],
                "projets": self.liste(), "depots": [x for x in self.depots() if not self._existe(x.get("projet"))], "redacteur": self.redacteur_actif(), "depense": self.depense(),
                "occupe": self.studio.running(), "can_run": self.studio.can_run(),
                "bibliotheque": self.bibliotheque(),
                "musiques": sorted(f.name for f in self.da.iterdir() if f.suffix.lower() in (".mp3", ".m4a", ".wav", ".ogg"))}

    # --- Ecriture ---------------------------------------------------------------------------------
    def redacteur_actif(self):
        try:
            return time.time() - (self.de / "redacteur.vivant").stat().st_mtime < 45
        except FileNotFoundError:
            return False

    def _fiche(self, p):
        return json.dumps({"nom": p["nom"], "age": p["age"], "langue_des_publications": p.get("langue"), "phrase": p.get("accroche"),
                           **(p.get("fiche") or {}), "lieux (français | anglais)": p.get("lieux"), "tenues (français | anglais)": p.get("tenues"),
                           "ecriture": p.get("ecriture"), "note_generation": (p.get("generation") or {}).get("note")}, ensure_ascii=False, indent=1)

    def _texte_projet(self, p, temps=1):
        """Texte d'un temps du projet pour le redacteur. Les temps 3 et 4 ne lui sont jamais envoyes, ni une scene a LoRA supplementaires."""
        if temps not in (1, 2):
            raise ValueError("les temps 3 et 4 sont à votre main : le rédacteur IA ne les lit pas")
        keep = ("id", "titre", "role", "raccord", "cran", "still", "motion", "end_edit", "texte", "voix", "tattoos")
        tete = {k: p.get(k) for k in ("titre", "pitch", "accroche", "legende", "cta", "hashtags")} if temps == 1 else {}
        return json.dumps(tete | {"continuite": p["continuite"], "scenes": [{k: s[k] for k in keep} for s in p["scenes"] if s["temps"] == temps and not s["loras"]]}, ensure_ascii=False, indent=1)

    def _voisins(self, slug, dp, proj=None):
        """Projets du meme personnage les plus proches dans sa chronologie, pour la continuite."""
        if not dp:
            return ""
        j = datetime.date.fromisoformat(dp)
        v = [x for x in self.liste() if x["personnage"] == slug and x["date_perso"] and not (proj and x["id"] == proj["id"])]
        v = sorted(v, key=lambda x: abs((datetime.date.fromisoformat(x["date_perso"]) - j).days))[:5]
        if not v:
            return ""
        return ("AUTRES VIDÉOS DU PERSONNAGE AUTOUR DE CETTE DATE (dates du personnage)\n"
                + "\n".join(f"- {x['date_perso']} : {x['titre']}. {x['pitch']}" for x in sorted(v, key=lambda x: x["date_perso"]))
                + "\nReste cohérent avec elles (ce qu'elle a déjà fait ou annoncé) sans les répéter.\n\n")

    def ecrire(self, b):
        kind = b.get("kind")
        consigne = _s(b.get("consigne"), 1500)
        proj = self._raw(b["projet"]) if b.get("projet") else None
        perso = self.perso(proj["personnage"] if proj else b.get("personnage")) if kind != "personnage" else None
        n = max(1, min(int(b.get("n") or 8), 12))
        dp = proj["date_perso"] if proj else _date(b.get("date_perso")) or (time.strftime("%Y-%m-%d") if kind == "idees" else "")
        moment = _moment(dp, proj["contexte"] if proj else _s(b.get("contexte"), 400)) + (self._voisins(perso["slug"], dp, proj) if perso else "")
        if kind == "scenario":
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\n{moment}COMMANDE\nÉcris le scénario complet d'un teaser en {proj['nb_scenes']} scènes.\n"
                      f"Idée de départ : {proj.get('brief') or 'libre, choisis l angle le plus vendeur pour ce personnage'}\n"
                      f"Suite payante annoncée : {proj.get('suite') or 'non précisée, reste vague sur son contenu'}\n"
                      f"{'Consigne : ' + consigne if consigne else ''}\n\nFORMAT\n{SCHEMA}")
        elif kind == "retouche":
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\n{moment}SCÉNARIO ACTUEL\n{self._texte_projet(proj)}\n\nCOMMANDE\nRéécris ce scénario selon la consigne : "
                      f"{consigne or 'rends-le plus accrocheur et plus vendeur'}\nGarde le champ \"id\" des scènes que tu conserves, et laisse leur \"still\" "
                      f"identique au mot près si l'image ne doit pas changer. Une scène nouvelle n'a pas d'\"id\".\n\nFORMAT\n{SCHEMA}")
        elif kind == "scene":
            sc = next((s for s in proj["scenes"] if s["id"] == b.get("scene")), None)
            if not sc:
                raise ValueError("scène inconnue")
            if sc["temps"] not in (1, 2):
                raise ValueError("les temps 3 et 4 sont à votre main : le rédacteur IA ne les écrit pas")
            if sc["loras"]:
                raise ValueError("scène à LoRA supplémentaires : elle reste à votre main")
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\n{moment}SCÉNARIO\n{self._texte_projet(proj, sc['temps'])}\n\nCOMMANDE\nRéécris uniquement la scène \"{sc['id']}\" "
                      f"selon la consigne : {consigne or 'plus forte, plus sensuelle, toujours suggestive'}\n\nFORMAT\n"
                      '{"titre": "...", "role": "...", "raccord": "coupe|continu", "still": "...", "motion": "...", "end_edit": "", "texte": "...", "voix": "", "cran": 1, "tattoos": true}')
        elif kind == "temps2":
            if not [s for s in proj["scenes"] if s["temps"] == 1]:
                raise ValueError("écrire d'abord le teaser (temps 1) : la montée en est la suite")
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\n{moment}TEASER PUBLIC (temps 1, déjà écrit)\n{self._texte_projet(proj)}\n\nCOMMANDE\n"
                      f"Écris le temps 2 : la suite du teaser, en {proj['nb2']} scènes, offerte ou réservée aux abonnés. Ce n'est plus une publicité, c'est ce que "
                      "le teaser promettait : elle reprend à l'instant où le teaser a coupé et va un cran plus loin à chaque scène (plus près, plus lente, plus "
                      "intime, regard plus appuyé, tenue plus défaite). Même lieu et même tenue que le teaser : la fiche de continuité du projet est "
                      "ajoutée automatiquement à chaque \"still\", ne la répète pas et ne la renvoie pas. Registre : suggestif poussé, jamais explicite. La tenue peut se défaire jusqu'à la lingerie, la nudité peut être suggérée "
                      "(dos nu, épaule, drap, serviette, cadrage coupé, contre-jour) mais rien d'intime n'est visible et il n'y a aucun acte. Pas d'appel à l'action ; "
                      f"la dernière scène laisse seulement entendre qu'une suite plus dévoilée existe, sans la décrire.\n{'Consigne : ' + (consigne or proj.get('brief2')) if (consigne or proj.get('brief2')) else ''}\n\nFORMAT\n"
                      '{"scenes": [{"titre": "...", "role": "accroche|montee|chute", "raccord": "coupe|continu", "still": "...", "motion": "...", "end_edit": "", "texte": "...", "voix": "", "cran": 1, "tattoos": true}]}')
        elif kind == "legendes":
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\n{moment}SCÉNARIO\n{self._texte_projet(proj)}\n\nCOMMANDE\nPropose {min(n, 5)} variantes d'accroche, de légende "
                      f"et de carton de fin pour cette vidéo, d'angles différents (défi, confidence, humour, promesse, urgence). {consigne}\n\nFORMAT\n"
                      '{"variantes": [{"angle": "...", "accroche": "...", "legende": "...", "cta": "..."}]}')
        elif kind == "idees":
            deja = [x["titre"] for x in self.liste() if x["personnage"] == perso["slug"]]
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\n{moment}COMMANDE\nPropose {n} idées de teasers différentes, classées de la plus vendeuse à la moins vendeuse. "
                      f"Varie les lieux, les tenues et les mécaniques d'accroche. {('Thème : ' + consigne) if consigne else ''}\n"
                      f"Déjà faites, à ne pas répéter : {', '.join(deja) or 'aucune'}\n\nFORMAT\n"
                      '{"idees": [{"titre": "...", "pitch": "ce qui se passe, en deux phrases", "accroche": "texte de la première seconde"}]}')
        elif kind == "personnage":
            if not consigne:
                raise ValueError("décrire le personnage en une ou deux phrases")
            prompt = (f"COMMANDE\nCrée la fiche complète d'un nouveau personnage fictif pour des vidéos de séduction. Concept donné par le propriétaire : {consigne}\n"
                      f"Le personnage est une femme adulte de {AGE_MIN} ans au moins, d'apparence clairement adulte, sans ressemblance avec une personne réelle ou célèbre, "
                      "avec un prénom et un nom inventés. Donne-lui un métier, des défauts, des tics de langage, un univers visuel et une manière précise de séduire. "
                      "\"lieux\" et \"tenues\" : 6 éléments chacun, au format \"français | anglais\" (l'anglais commence par \"in\"/\"on\" pour un lieu, par \"a\"/\"an\" pour une tenue). "
                      "\"zimage_prefix\" : en anglais, \"a woman with ...\" (âge apparent, cheveux, yeux, teint, silhouette), une ligne.\n\nFORMAT\n"
                      '{"nom": "...", "age": 27, "langue": "en", "accroche": "phrase qui la résume", "fiche": {"identite": "...", "apparence": "...", "voix": "...", '
                      '"personnalite": "...", "seduction": "...", "univers": "...", "limites": "..."}, "lieux": ["..."], "tenues": ["..."], '
                      '"ecriture": {"ton": "...", "cta": "...", "plateforme": "Fanvue", "hashtags": "...", "interdits": "..."}, "generation": {"zimage_prefix": "..."}}')
        else:
            raise ValueError("commande inconnue")
        if not self.redacteur_actif():
            rng = random.Random()
            if kind == "idees":
                return {"etat": "pret", "moteur": "secours", "resultat": {"idees": moteur_local.idees(perso, rng, n)}}
            if kind == "scenario":
                res = moteur_local.scenario(perso, rng, moteur_local.par_titre(proj.get("titre")), proj["nb_scenes"])
                return {"etat": "pret", "moteur": "secours", "resultat": self._appliquer("scenario", proj["id"], None, res)}
            raise ValueError("le rédacteur IA ne répond pas (service girls-ai-writer) : seuls les idées et les scénarios types sont disponibles")
        rid = f"{time.strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
        req = {"systeme": SYSTEME, "demande": prompt, "kind": kind, "projet": proj["id"] if proj else "", "scene": b.get("scene") or ""}
        _dump(self.de / f"{rid}.req.json", req)
        os.chmod(self.de / f"{rid}.req.json", 0o666)
        if proj and kind in ("scenario", "retouche", "scene", "temps2"):
            proj["attente"] = rid
            _dump(self.dj / proj["id"] / "projet.json", proj)
        return {"etat": "attente", "rid": rid}

    def _appliquer(self, kind, pid, sid, res):
        with self.lock:
            p = self._raw(pid)
            p["attente"] = ""
            if kind == "scene":
                for i, s in enumerate(p["scenes"]):
                    if s["id"] == sid:
                        p["scenes"][i] = self._scene({**s, **{k: res[k] for k in ("titre", "role", "raccord", "cran", "still", "motion", "end_edit", "texte", "voix", "tattoos") if k in res}}, p)
            else:
                t = 2 if kind == "temps2" else 1  # les scenes des autres temps ne bougent pas
                old = {s["id"]: s for s in p["scenes"] if s["temps"] == t}
                for k in ("pitch", "accroche", "legende", "cta", "hashtags") if t == 1 else ():
                    p[k] = _s(res.get(k), 600)
                if t == 1 and isinstance(res.get("continuite"), dict) and any(_cont(res["continuite"]).values()):
                    p["continuite"] = _cont(res["continuite"])
                if t == 1 and res.get("titre") and (kind == "retouche" or p.get("titre") in ("", "Sans titre")):
                    p["titre"] = _s(res["titre"], 100)
                scenes = []
                for d in res.get("scenes") or []:
                    o = old.get(d.get("id")) or {}
                    scenes.append(self._scene({**{k: o[k] for k in ("id", "seed", "image", "clip", "debut", "duree", "raccord", "libre") if k in o}, **d,
                                               **({"id": o["id"]} if o else {"id": None}), "temps": t, "loras": o.get("loras", ""), "origine": ""}, p))
                if not scenes:
                    raise ValueError("le rédacteur n'a renvoyé aucune scène")
                # les plans deposes par l'agent (origine) ne sont jamais ecrases par le redacteur
                garde = [s for s in p["scenes"] if s["temps"] != t or (kind == "temps2" and s["origine"])]
                p["scenes"] = sorted(scenes[:10] + garde, key=lambda s: s["temps"])
                if p["reference"] not in [s["id"] for s in p["scenes"]]:
                    p["reference"] = ""
            p["modifie"] = time.strftime("%Y-%m-%d %H:%M")
            _dump(self.dj / pid / "projet.json", p)
            return p

    def resultat(self, rid):
        if not re.fullmatch(r"\d{17}", str(rid)):
            raise ValueError("identifiant invalide")
        req = _load(self.de / f"{rid}.req.json")
        res, err = self.de / f"{rid}.res.txt", self.de / f"{rid}.err.txt"
        if not req:
            return {"etat": "pret", "resultat": None}  # deja appliquee
        if not res.exists() and not err.exists():
            if not self.redacteur_actif() and time.time() - (self.de / f"{rid}.req.json").stat().st_mtime > 60:
                self._fin(rid, req)
                raise ValueError("le rédacteur IA s'est arrêté avant de répondre")
            return {"etat": "attente"}
        try:
            if err.exists():
                raise ValueError("rédacteur : " + err.read_text(encoding="utf-8", errors="replace")[:300])
            out = _json_de(res.read_text(encoding="utf-8"))
            if req["kind"] in ("scenario", "retouche", "scene", "temps2"):
                out = self._appliquer(req["kind"], req["projet"], req.get("scene"), out)
            return {"etat": "pret", "moteur": "ia", "resultat": out}
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(str(e)[:300])
        finally:
            self._fin(rid, req)

    def _fin(self, rid, req):
        for f in self.de.glob(f"{rid}.*"):
            f.unlink(missing_ok=True)
        if req.get("projet"):
            with self.lock:
                p = _load(self.dj / req["projet"] / "projet.json")
                if p and p.get("attente") == rid:
                    p["attente"] = ""
                    _dump(self.dj / req["projet"] / "projet.json", p)

    # --- Relecture des images ---------------------------------------------------------------------
    def relire(self, b):
        """Fait relire par le redacteur IA les images retenues d'un temps, avant les clips. Jamais les temps 3 et 4, ni les
        scenes qui portent des LoRA supplementaires : ces images sont a la main du proprietaire."""
        pid, t = b["id"], int(b.get("temps") or 1)
        if t not in (1, 2):
            raise ValueError("les temps 3 et 4 sont à votre main : ils ne sont pas relus")
        if not self.redacteur_actif():
            raise ValueError("le rédacteur IA ne répond pas (service girls-ai-writer)")
        p = self._raw(pid)
        d = self._pdir(pid)
        sc = [s for s in self._eff(p)["scenes"] if s["temps"] == t]
        vus = [(i, s) for i, s in enumerate(sc, 1) if s["image"] and not s["loras"]][:8]
        if not vus:
            raise ValueError("aucune image à relire dans ce temps")
        images = []
        with tempfile.TemporaryDirectory() as tmp:
            for _, s in vus:
                _ff("-i", d / "media" / s["image"], "-vf", "scale=-2:768", "-q:v", "5", Path(tmp) / "i.jpg")
                images.append({"scene": s["id"], "jpeg": base64.b64encode((Path(tmp) / "i.jpg").read_bytes()).decode()})
        c = p["continuite"]
        demande = ((f"ACCROCHE (texte à l'écran de la première seconde)\n{p['accroche']}\n\n" if t == 1 and p.get("accroche") else "")
                   + "FICHE DE CONTINUITÉ (anglais)\n" + "\n".join(f"- {k} : {c[k] or 'non précisé'}" for k in CONT) + "\n\nSCÈNES RELUES\n"
                   + "\n".join(f"- {s['id']} (scène {i}{', scène libre : hors fiche de continuité' if s['libre'] else ''}"
                               f"{', suite sans coupe de la scène précédente : image tirée de la fin de son clip' if i > 1 and s['raccord'] == 'continu' else ''})\n"
                               f"  image : {s['still'] or 'non décrite'}\n  geste du clip : {s['motion'] or 'aucun (image fixe)'}\n  texte à l'écran : {s['texte'] or 'aucun'}"
                               for i, s in vus)
                   + "\n\nRelis ces images et réponds au format demandé, avec une entrée par scène, dans l'ordre.")
        rid = f"{time.strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
        _dump(self.de / f"{rid}.req.json", {"systeme": RELECTEUR, "demande": demande, "images": images, "kind": "relecture", "projet": pid, "temps": t})
        os.chmod(self.de / f"{rid}.req.json", 0o666)
        with self.lock:
            r = _load(d / "relecture.json", {})
            r[str(t)] = {"etat": "attente", "rid": rid, "date": time.strftime("%Y-%m-%d %H:%M"), "vues": {s["id"]: s["image"] for _, s in vus}}
            _dump(d / "relecture.json", r)
        return {"etat": "attente"}

    def _releve(self, rid, lire):
        """Reponse du redacteur a la demande `rid` : None tant qu'elle n'est pas arrivee, sinon {"etat": "pret", ...lire(json)}
        ou {"etat": "erreur", "erreur"}. Les fichiers de la demande sont alors supprimes."""
        req, res, err = self.de / f"{rid}.req.json", self.de / f"{rid}.res.txt", self.de / f"{rid}.err.txt"
        if not res.exists() and not err.exists():
            age = time.time() - req.stat().st_mtime if req.exists() else 1e9
            if age < 60 or (self.redacteur_actif() and age < 400):
                return None
            maj = {"etat": "erreur", "erreur": "le rédacteur IA n'a pas répondu"}
        else:
            try:
                if err.exists():
                    raise ValueError(err.read_text(encoding="utf-8", errors="replace")[:300])
                maj = {"etat": "pret", **lire(_json_de(res.read_text(encoding="utf-8")))}
            except (ValueError, KeyError, TypeError, AttributeError) as e:
                maj = {"etat": "erreur", "erreur": str(e)[:300]}
        for f in self.de.glob(f"{rid}.*"):
            f.unlink(missing_ok=True)
        return maj

    def relecture(self, pid):
        """Relectures du projet, par temps. Releve au passage la reponse du redacteur quand elle est arrivee."""
        d = self._pdir(pid)
        r = _load(d / "relecture.json", {})
        for t, x in r.items():
            if x.get("etat") != "attente":
                continue
            rid = x["rid"]

            def lire(out, x=x):
                sc = {}
                for y in out.get("scenes") or []:
                    if isinstance(y, dict) and y.get("id") in x["vues"]:
                        sc[y["id"]] = {"image": x["vues"][y["id"]], "ok": y.get("verdict") != "a_refaire",
                                       "constat": _s(y.get("constat"), 400), "consigne": _s(y.get("consigne"), 700)}
                if not sc:
                    raise ValueError("réponse sans scène")
                return {"ensemble": _s(out.get("ensemble"), 600), "scenes": sc}

            maj = self._releve(rid, lire)
            if not maj:
                continue
            with self.lock:
                r2 = _load(d / "relecture.json", {})
                if (r2.get(t) or {}).get("rid") == rid:
                    r2[t] = {"date": x["date"], **maj}
                    _dump(d / "relecture.json", r2)
                r[t] = r2.get(t) or {}
        return {t: {k: v for k, v in x.items() if k not in ("rid", "vues")} for t, x in r.items()}

    def analyser(self, b):
        """Fait critiquer par le redacteur IA une video montee, d'apres des images qui en sont extraites (debut, milieu de
        chaque scene, de part et d'autre de chaque jointure, fin). Jamais les temps 3 et 4 ni une video qui contient une scene a
        LoRA supplementaires : celles-la sont a la main du proprietaire."""
        pid, nom = b["id"], str(b.get("fichier"))
        m = re.fullmatch(r"final_(t2_)?v\d+\.mp4", nom)
        if not m:
            raise ValueError("les temps 3 et 4 sont à votre main : ils ne sont pas analysés" if re.match(r"final_t[34]_", nom) else "fichier invalide")
        if not self.redacteur_actif():
            raise ValueError("le rédacteur IA ne répond pas (service girls-ai-writer)")
        t = 2 if m.group(1) else 1
        p, d = self._raw(pid), self._pdir(pid)
        sc = {s["id"]: s for s in p["scenes"] if s["temps"] == t}
        if any(s["loras"] for s in sc.values()):
            raise ValueError("ce temps contient une scène à LoRA supplémentaires : son analyse reste à votre main")
        src = d / nom
        if not src.is_file():
            raise ValueError("vidéo introuvable")
        info = _load(d / "finals.json", {}).get(nom) or {}
        duree = info.get("duree") or _duree(src)
        vues, ids, deb, fins = _vues(info, duree)
        images = []
        with tempfile.TemporaryDirectory() as tmp:
            for a, role, _ in vues:
                _ff("-ss", f"{a:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=-2:640", "-q:v", "6", Path(tmp) / "i.jpg")
                images.append({"titre": f"Image à {a:.1f} s, {role} :", "jpeg": base64.b64encode((Path(tmp) / "i.jpg").read_bytes()).decode()})
        c, mt = p["continuite"], p["montage"]
        fiche = [f"durée {duree:.1f} s, format {mt['format']}, {len(ids) or '?'} scène(s), transition « {mt['transition']} » entre les scènes coupées",
                 f"musique : {'oui' if mt['musique'] else 'non'} ; mention « AI character » incrustée : {'oui' if info.get('label') else 'non garantie'}"]
        if info.get("cible"):
            fiche.append(f"durée visée {info['cible']} s : les scènes ont été raccourcies au montage")
        if t == 1:
            fiche.append(f"accroche affichée au début de la première scène : {p['accroche'] or 'aucune'} ; carton de fin : {p['cta'] if info.get('carton') else 'aucun'}")
        lignes = []
        for i, sid in enumerate(ids):
            s = sc.get(sid)
            if s:
                lignes.append(f"- scène {i + 1}, de {deb[i]:.1f} s à {fins[i]:.1f} s" + (", collée à la précédente sans coupe" if info["colle"][i] else "") + (", montée en image fixe" if not str(info["prises"][i][1]).endswith(".mp4") else "")
                              + f", cran {s['cran'] or 'non renseigné'}\n  image : {s['still'] or 'non décrite'}\n  geste : {s['motion'] or 'aucun'}\n  texte à l'écran : {s['texte'] or 'aucun'}")
        demande = ("FICHE TECHNIQUE DU MONTAGE\n" + "\n".join("- " + x for x in fiche)
                   + "\n\nFICHE DE CONTINUITÉ (anglais)\n" + "\n".join(f"- {k} : {c[k] or 'non précisé'}" for k in CONT)
                   + ("\n\nSCÉNARIO\n" + "\n".join(lignes) if lignes else "")
                   + "\n\nCritique cette vidéo d'après ces images et réponds au format demandé.")
        rid = f"{time.strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
        _dump(self.de / f"{rid}.req.json", {"systeme": ANALYSTE, "demande": demande, "images": images, "kind": "analyse", "projet": pid, "fichier": nom})
        os.chmod(self.de / f"{rid}.req.json", 0o666)
        with self.lock:
            r = _load(d / "analyse.json", {})
            r[nom] = {"etat": "attente", "rid": rid, "date": time.strftime("%Y-%m-%d %H:%M")}
            _dump(d / "analyse.json", r)
        return {"etat": "attente"}

    def analyses(self, pid):
        """Analyses des videos montees du projet, par fichier. Releve au passage les reponses arrivees."""
        d = self._pdir(pid)
        r = _load(d / "analyse.json", {})

        def lire(out):
            pts = [{"moment": _s(y.get("moment"), 60), "grave": bool(y.get("grave")), "constat": _s(y.get("constat"), 400),
                    "proposition": _s(y.get("proposition"), 500)} for y in out.get("points") or [] if isinstance(y, dict) and y.get("constat")][:8]
            if not pts and not out.get("ensemble"):
                raise ValueError("réponse vide")
            return {"publiable": out.get("verdict") != "a_reprendre", "points": pts, "forces": _s(out.get("forces"), 400), "ensemble": _s(out.get("ensemble"), 600)}

        for nom, x in r.items():
            if x.get("etat") != "attente":
                continue
            maj = self._releve(x["rid"], lire)
            if not maj:
                continue
            with self.lock:
                r2 = _load(d / "analyse.json", {})
                if (r2.get(nom) or {}).get("rid") == x["rid"]:
                    r2[nom] = {"date": x["date"], **maj}
                    _dump(d / "analyse.json", r2)
                r[nom] = r2.get(nom) or {}
        return {nom: {k: v for k, v in x.items() if k != "rid"} for nom, x in r.items() if (d / nom).is_file()}

    # --- Plans deposes par l'agent ----------------------------------------------------------------
    def _existe(self, pid):
        return bool(re.fullmatch(r"p\d{4}", str(pid or ""))) and (self.dj / str(pid) / "projet.json").is_file()

    def _plan(self, f):
        """Lit un plan depose (format de server/jobs/modele.yaml, plus un bloc "atelier") et le rend en scenes."""
        import yaml
        if f.stat().st_size > 200_000:
            raise ValueError("fichier trop gros")
        j = yaml.safe_load(f.read_text(encoding="utf-8"))
        if not isinstance(j, dict) or not isinstance(j.get("atelier"), dict):
            raise ValueError('bloc "atelier" absent')
        a, d, shots = j["atelier"], j.get("defaults") or {}, j.get("shots")
        if a.get("temps") not in (1, 2, 3, 4) or isinstance(a.get("temps"), bool):
            raise ValueError('"atelier.temps" doit valoir 1, 2, 3 ou 4')
        if a["temps"] == 3 and str(j.get("modele") or "") < MODELE_4T:  # plan ecrit avant les quatre temps : son temps 3 etait le final
            a = a | {"temps": 4}
        if not isinstance(shots, list) or not 1 <= len(shots) <= 10:
            raise ValueError("de 1 à 10 plans par fichier")
        scenes, noms = [], set()
        for i, sh in enumerate(shots):
            nom = str(sh.get("name") or "") if isinstance(sh, dict) else ""
            if not re.fullmatch(r"[A-Za-z0-9_]{1,40}", nom) or nom in noms:
                raise ValueError(f"plan {i + 1} : nom absent, invalide ou en double")
            noms.add(nom)
            if not _s(sh.get("still")):
                raise ValueError(f"plan {nom} : \"still\" obligatoire")
            if [k for k in ("steps", "image", "edit", "suite_de", "end_image") if sh.get(k)]:
                raise ValueError(f"plan {nom} : \"steps\", \"image\", \"edit\", \"suite_de\" et \"end_image\" ne sont pas repris par l'atelier "
                                 "(raccords : champ \"raccord\" ; image de référence : \"atelier.reference\")")
            if sh.get("raccord", "coupe") not in RACCORDS:
                raise ValueError(f"plan {nom} : \"raccord\" vaut coupe, continu ou arrivee")
            if sh.get("cran") not in (None, 1, 2, 3, 4, 5):
                raise ValueError(f"plan {nom} : \"cran\" est un entier de 1 à 5")
            seed = sh.get("seed") or (int(d["seed"]) + (0 if d.get("same_seed") else i) if d.get("seed") else 0)
            scenes.append({"titre": sh.get("titre") or nom, "role": sh.get("role"), "temps": a["temps"], "still": sh["still"], "motion": sh.get("motion"),
                           "end_edit": sh.get("end_edit"), "texte": sh.get("texte"), "voix": sh.get("voix"), "tattoos": sh.get("tattoos", True),
                           "loras": sh.get("loras", d.get("loras")), "seed": seed, "origine": f"{f.name}:{nom}",
                           "raccord": sh.get("raccord"), "libre": bool(sh.get("libre")), "cran": sh.get("cran")})
        # textes de publication : seulement avec le temps 1, et seulement ceux qui sont remplis
        lim = {"pitch": 400, "accroche": 120, "legende": 600, "cta": 120, "hashtags": 200}
        textes = {k: _s(a.get(k), n) for k, n in lim.items() if a["temps"] == 1 and _s(a.get(k), n)}
        if a.get("date_perso"):  # date du personnage (fictive) ; YAML peut la lire comme une date
            if not _date(a["date_perso"]):
                raise ValueError('"atelier.date_perso" : date au format AAAA-MM-JJ')
            if a["temps"] == 1:
                textes["date_perso"] = _date(a["date_perso"])
        if a["temps"] == 1 and _s(a.get("contexte"), 400):
            textes["contexte"] = _s(a.get("contexte"), 400)
        # fiche de continuite et image de reference : au projet entier, donc portees par le depot du temps 1
        if a.get("continuite") is not None and not isinstance(a["continuite"], dict):
            raise ValueError(f'"atelier.continuite" : un bloc de champs ({", ".join(CONT)})')
        if a["temps"] == 1 and any(_cont(a.get("continuite")).values()):
            textes["continuite"] = _cont(a["continuite"])
        ref = str(a.get("reference") or "")
        if ref and ref not in [str(sh["name"]) for i, sh in enumerate(shots) if not (i and sh.get("raccord") == "continu")]:
            raise ValueError('"atelier.reference" : nom d\'un plan de ce fichier qui a sa propre image (pas un plan continu)')
        return {"projet": str(a.get("projet") or ""), "temps": a["temps"], "personnage": str(a.get("personnage") or ""),
                "titre": _s(a.get("titre"), 100), "note": _s(a.get("note"), 300), "modele": str(j.get("modele") or ""), "scenes": scenes,
                "textes": textes, "reference": ref if a["temps"] == 1 else ""}

    def depots(self):
        import yaml
        if not self.dd.is_dir():
            return []
        try:
            modele = str(yaml.safe_load((self.dd.parent / "modele.yaml").read_text(encoding="utf-8"))["modele"])
        except Exception:
            modele = ""
        vus, out, lib = {}, [], self._lib()
        for f in sorted(self.dd.glob("*.yaml"), key=lambda f: f.stat().st_mtime, reverse=True)[:60]:
            x = {"fichier": f.name, "mtime": int(f.stat().st_mtime), "date": time.strftime("%d/%m %H:%M", time.localtime(f.stat().st_mtime))}
            try:
                if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}\.yaml", f.name):
                    raise ValueError("nom de fichier invalide (lettres, chiffres, _ . -)")
                pl = self._plan(f)
                x |= {k: pl[k] for k in ("projet", "temps", "personnage", "titre", "note")} | {"n": len(pl["scenes"]), "perime": bool(modele) and pl["modele"] != modele}
                if not x["projet"]:  # depot sans projet deja importe : il appartient au projet qu'il a ouvert
                    x["projet"] = self._rattache(f.name)
                fiche = pl["textes"].get("continuite") or (self._raw(x["projet"])["continuite"] if x["projet"] and self._existe(x["projet"]) else {})
                x["remarques"] = len(controle({"continuite": fiche, "accroche": pl["textes"].get("accroche"), "scenes": [
                    {**s, "id": str(i), "loras": _loras(s["loras"])} for i, s in enumerate(pl["scenes"])]}, pl["temps"], lib))
                if x["projet"] and not self._existe(x["projet"]):
                    x["erreur"] = f"projet {x['projet']} inconnu"
                elif x["projet"]:
                    if x["projet"] not in vus:
                        vus[x["projet"]] = self._raw(x["projet"]).get("depots") or {}
                    x["importe"] = vus[x["projet"]].get(f.name) == x["mtime"]
                    x["change"] = f.name in vus[x["projet"]] and not x["importe"]
            except Exception as e:
                x["erreur"] = str(e)[:200]
            out.append(x)
        return out

    def _rattache(self, nom):
        """Projet ouvert par l'import d'un depot qui ne nommait pas de projet ("" si aucun)."""
        for d in sorted(self.dj.glob("p*/projet.json"), reverse=True):
            if nom in (_load(d, {}).get("depots") or {}):
                return d.parent.name
        return ""

    def importer(self, b):
        """Verse les plans d'un fichier depose dans les scenes d'un temps du projet. Un nouvel import du meme
        fichier met a jour ses scenes (reperees par leur origine) en gardant leurs images tant que "still" est inchange."""
        f = self.dd / str(b.get("fichier"))
        if f.parent != self.dd or not f.is_file() or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}\.yaml", f.name):
            raise ValueError("fichier inconnu")
        pl = self._plan(f)
        pid = pl["projet"] or self._rattache(f.name)
        if not pid:  # depot sans projet : en ouvrir un
            pid = self.save_projet({"personnage": pl["personnage"] or b.get("personnage"), "titre": pl["titre"] or f.stem})["id"]
        with self.lock:
            p = self._raw(pid)
            old = {s["origine"]: s for s in p["scenes"] if s["origine"].startswith(f.name + ":")}
            neuves, defaut = [], self._defauts().get(pl["temps"], "")
            for d in pl["scenes"]:
                o = old.get(d["origine"]) or {}
                if d["loras"] is None:  # le plan ne dit rien des LoRA : celles deja posees sur la scene, sinon celles du temps
                    d = d | {"loras": o["loras"] if o else defaut}
                garde = ("id", "seed", "image", "clip", "debut", "duree") if o and o["still"] == _s(d["still"], 1200) else ("id",) if o else ()
                neuves.append(self._scene({**d, **{k: o[k] for k in garde}, "seed": (o.get("seed") if "seed" in garde else 0) or d["seed"],
                                           "id": o.get("id")}, p))
            reste = [s for s in p["scenes"] if s["origine"] not in old]
            if len(reste) + len(neuves) > 30:
                raise ValueError("trop de scènes dans ce projet")
            p["scenes"] = sorted(reste + neuves, key=lambda s: s["temps"])
            p.update(pl["textes"])
            if pl["reference"]:
                p["reference"] = next(s["id"] for s in neuves if s["origine"] == f"{f.name}:{pl['reference']}")
            elif p["reference"] not in [s["id"] for s in p["scenes"]]:
                p["reference"] = ""
            if pl["temps"] == 1 and not p["brief"]:  # l'idee de depart d'un projet depose est son pitch
                p["brief"] = p["pitch"]
            p.setdefault("depots", {})[f.name] = int(f.stat().st_mtime)
            p["modifie"] = time.strftime("%Y-%m-%d %H:%M")
            _dump(self.dj / pid / "projet.json", p)
        return {"id": pid, "temps": pl["temps"], "scenes": len(neuves)}

    # --- Production (pilote) ----------------------------------------------------------------------
    def _still(self, p, s):
        """Description envoyee au modele d'image : celle de la scene, suivie de la fiche de continuite du projet."""
        c = [v.strip(" .,") for v in (p.get("continuite") or {}).values() if v]
        return s["still"] if s["libre"] or not c else s["still"].rstrip(" .,") + ", " + ", ".join(c)

    def _a_imager(self, p, ch, temps, refaire=False):
        """Scenes d'un ou plusieurs temps dont l'image est a calculer (une scene continue n'a pas d'image a elle)."""
        prec = _prec(p)
        return [s["id"] for s in p["scenes"] if s["temps"] in temps and s["still"] and not (prec[s["id"]] and s["raccord"] == "continu")
                and (refaire or not ch[s["id"]]["image"])]

    def _a_cliper(self, p, ch, temps, want=None, neuves=()):
        """Scenes dont le clip est a calculer, dans l'ordre. Une scene continue suit le sort de la precedente : si le clip
        de celle-ci est refait, le sien l'est aussi. `neuves` : scenes dont l'image va etre refaite avant."""
        prec, out = _prec(p), []
        for s in p["scenes"]:
            pv = prec[s["id"]]
            cont = bool(pv) and s["raccord"] == "continu"
            if not s["motion"]:
                continue
            choisi = s["id"] in want if want else s["temps"] == temps and (s["id"] in neuves or not ch[s["id"]]["clip"])
            if not choisi and not (cont and pv["id"] in out):
                continue
            if (pv["id"] in out or ch[pv["id"]]["clip"]) if cont else (ch[s["id"]]["image"] or s["id"] in neuves):
                out.append(s["id"])
        return out

    def devis(self, p, temps=1):
        """Cout estime des deux lancements d'un temps, d'apres les couts constates (docs/journal-projet.md)."""
        ch = {s["id"]: s for s in p["scenes"]}
        img = self._a_imager(p, ch, (temps,))
        clp = [ch[i] for i in self._a_cliper(p, ch, temps)]
        return {"images": {"n": len(img), "usd": round(0.003 * len(img) + (0 if self.studio.pod() else 0.05), 2)},
                "clips": {"n": len(clp), "usd": round(sum(0.07 if s["end_edit"] else 0.035 for s in clp) + 0.12, 2),
                          "usd_hd": round(sum(0.26 if s["end_edit"] else 0.13 for s in clp) + 0.12, 2)}}

    def _fin_clip(self, clip, dest):
        """Derniere image d'un clip deja produit : celle gardee par le pilote, sinon tiree du fichier mp4."""
        run = clip.split("_")[0]
        src = self.data / "work" / run / f"{clip[:-4]}_fin.png"
        if src.is_file():
            shutil.copy(src, dest)
        else:
            _ff("-sseof", "-0.5", "-i", dest.parent / clip, "-update", "1", dest)

    def produire(self, b, chaine=False):
        pid, quoi = b["id"], b.get("quoi")
        if quoi not in ("images", "clips"):
            raise ValueError("lancement inconnu")
        if not chaine and self.chaine_active():
            raise ValueError(f"une chaîne de production est en cours (projet {self.ch['projet']}) : attendre sa fin ou l'arrêter")
        if self.studio.running():
            raise ValueError("un calcul est déjà en cours : attendre sa fin")
        if not self.studio.can_run():
            raise ValueError("clé RunPod absente : lancement impossible depuis l'interface")
        with self.lock:
            p = self._raw(pid)
            pr = self.prises(pid)
            ch = self._choix(p, pr)
            perso = self.perso(p["personnage"])
            want = set(b.get("scenes") or [])
            d = self._pdir(pid)
            n = len(list((d / "runs").glob("r*.json"))) + 1 if (d / "runs").is_dir() else 1
            shots, media, prec, ch_s = [], d / "media", _prec(p), {s["id"]: s for s in p["scenes"]}
            if quoi == "images":
                ids = [i for i in self._a_imager(p, ch, {s["temps"] for s in p["scenes"]} if want else (int(b.get("temps") or 1),), bool(want))
                       if not want or i in want]
                # image de reference : les autres images en sont tirees par retouche (meme personne, meme lieu, meme tenue)
                ref = p.get("reference") if not (prec.get(p.get("reference")) and ch_s[p["reference"]]["raccord"] == "continu") else ""
                base = f"{pid}r{n}_{ref}.png" if ref in ids else ch.get(ref, {}).get("image") if ref else ""
                for s in sorted((s for s in p["scenes"] if s["id"] in ids), key=lambda s: s["id"] != ref):
                    if ch[s["id"]]["image"]:  # nouvelle prise demandee : autre tirage
                        s["seed"] = random.randint(1, 999999)
                    s["image"], s["clip"] = "", ""  # la prise retenue sera la nouvelle
                    if base and s["id"] != ref and not s["libre"] and not s["loras"]:
                        shots.append({"name": s["id"], "image": str(media / base), "edit": self._still(p, s), "seed": s["seed"]})
                    else:
                        shots.append({"name": s["id"], "still": self._still(p, s), "seed": s["seed"], "tattoos": s["tattoos"],
                                      "body": bool((perso.get("generation") or {}).get("corps"))}
                                     | ({"loras": _loras_plan(s["loras"])} if s["loras"] else {}))
            else:
                ids = self._a_cliper(p, ch, int(b.get("temps") or 1), want)
                suiv = {prec[s["id"]]["id"]: s for s in p["scenes"] if prec[s["id"]]}
                for s in p["scenes"]:
                    if s["id"] not in ids:
                        continue
                    sh = {"name": s["id"], "still": s["still"], "motion": s["motion"], "seed": s["seed"] + len(pr.get(s["id"], {}).get("clips", []))}
                    pv, nx = prec[s["id"]], suiv.get(s["id"])
                    if pv and s["raccord"] == "continu":  # depart : derniere image du clip de la scene precedente
                        if pv["id"] in ids:
                            sh |= {"suite_de": pv["id"], "depuis": f"{pid}r{n}_{pv['id']}.mp4"}
                        else:
                            self._fin_clip(ch[pv["id"]]["clip"], media / f"{pid}r{n}_{s['id']}.png")
                            sh |= {"image": str(media / f"{pid}r{n}_{s['id']}.png"), "depuis": ch[pv["id"]]["clip"]}
                        s["image"] = ""
                    else:
                        sh["image"] = str(media / ch[s["id"]]["image"])
                    if nx and nx["raccord"] == "arrivee" and ch[nx["id"]]["image"]:  # le clip arrive sur l'image de la scene suivante
                        sh["end_image"] = str(media / ch[nx["id"]]["image"])
                    elif s["end_edit"]:
                        sh["end_edit"] = s["end_edit"]
                    s["clip"] = ""
                    shots.append(sh)
            if not shots:
                raise ValueError("rien à lancer : " + ("toutes les scènes ont déjà une image" if quoi == "images" else "il faut une image et un mouvement par scène"))
            job = {"name": f"{pid}r{n}", "character": self.char_override(perso),
                   "defaults": {"still_size": [720, 1280], "clip_size": [720, 1280] if b.get("hd") else [480, 832], "mode": "natural",
                                "smooth": True, "grain": True, "same_seed": True, "loras": []},
                   "shots": shots}
            _dump(d / "runs" / f"r{n}.json", job)
            _dump(d / "projet.json", p)
            cmd = [sys.executable, "-m", "pilot", "run", str(d / "runs" / f"r{n}.json"), "--data", str(self.data), "--out", str(d / "media")]
            if quoi == "images":  # pod de veille du studio, partage avec la page Test
                cmd += ["--stills-only", "--pod-id", os.environ.get("STUDIO_POD_ID") or self.studio.ensure_pod()]
            log = d / "runs" / f"r{n}.log"
            self.studio.proc = subprocess.Popen(cmd, cwd=str(self.repo / "server"), stdout=open(log, "w"), stderr=subprocess.STDOUT)
            self.job = {"projet": pid, "quoi": quoi, "log": str(log), "n": len(shots)}
            return {"lance": len(shots), "quoi": quoi}

    def prod(self, pid):
        d = self._pdir(pid) / "runs"
        logs = sorted(d.glob("r*.log"), key=lambda f: int(f.stem[1:])) if d.is_dir() else []
        if not logs:
            return {"etat": ""}
        log = logs[-1].read_text(encoding="utf-8", errors="replace")
        ici = bool(self.job and self.job["log"] == str(logs[-1]) and self.studio.running())
        etat = "en cours" if ici else "arrete" if "ARRET" in log else "termine" if "rapport :" in log else "interrompu"
        m = re.search(r'"cost_usd": ([\d.]+)', log)
        return {"etat": etat, "quoi": self.job["quoi"] if ici else "", "log": "\n".join(log.strip().splitlines()[-4:])[-600:],
                "echecs": log.count("ECHEC"), "cout": float(m.group(1)) if m else None}

    # --- Chaine : images, pause, puis clips et montage de chaque temps ------------------------------
    def chaine_active(self):
        return bool(self.ch and self.ch["etat"] == "en cours")

    def chaine_vue(self, pid):
        c = self.ch
        if not c or c["projet"] != pid:
            return {"etat": "", "ailleurs": c["projet"] if self.chaine_active() else ""}
        return {k: c[k] for k in ("projet", "temps", "mode", "refaire", "hd", "etat", "etape", "erreur", "journal", "stop")}

    def devis_chaine(self, pid, temps, refaire, hd):
        """Ce que la chaine va calculer et son cout estime (memes couts unitaires que devis())."""
        p = self._raw(pid)
        ch = self._choix(p)
        img = self._a_imager(p, ch, temps, refaire)
        usd, clips, montages = (0.003 * len(img) + (0 if self.studio.pod() else 0.05)) if img else 0, 0, 0
        for t in temps:
            sc = [s for s in p["scenes"] if s["temps"] == t]
            ok = self._a_cliper(p, ch, t, neuves=img)
            c = [s for s in sc if s["id"] in ok]
            if c:  # un lancement de clips par temps : chacun demarre son pod
                usd += sum(((0.26 if s["end_edit"] else 0.13) if hd else (0.07 if s["end_edit"] else 0.035)) for s in c) + 0.12
            clips += len(c)
            montages += bool([s for s in sc if s["still"]])
        dep = self.depense() or {}
        return {"images": len(img), "clips": clips, "montages": montages, "usd": round(usd, 2),
                "reste": round(dep["plafond"] - dep["jour"], 2) if dep else None}

    def chaine(self, b):
        """Lance la chaine d'un projet pour les temps choisis : images de tous ces temps en un lancement, pause pour choisir
        les prises (mode "pause") ou non (mode "complet"), puis clips et montage, un temps apres l'autre."""
        pid = b["id"]
        temps = sorted({int(t) for t in b.get("temps") or []} & set(TEMPS))
        if not temps:
            raise ValueError("choisir au moins un temps")
        refaire, hd = bool(b.get("refaire")), bool(b.get("hd"))
        dv = self.devis_chaine(pid, temps, refaire, hd)
        if not dv["montages"]:
            raise ValueError("aucune scène à produire dans les temps choisis")
        if dv["reste"] is not None and dv["usd"] > dv["reste"]:
            raise ValueError(f"devis de {dv['usd']:.2f} $ pour {dv['reste']:.2f} $ restants aujourd'hui : choisir moins de temps")
        if b.get("essai"):
            return {"devis": dv}
        if self.chaine_active():
            raise ValueError(f"une chaîne est déjà en cours (projet {self.ch['projet']})")
        if self.studio.running():
            raise ValueError("un calcul est déjà en cours : attendre sa fin")
        if not self.studio.can_run():
            raise ValueError("clé RunPod absente : lancement impossible depuis l'interface")
        self.ch = {"projet": pid, "temps": temps, "mode": "complet" if b.get("mode") == "complet" else "pause", "refaire": refaire, "hd": hd,
                   "etat": "en cours", "etape": "démarrage", "erreur": "", "journal": [], "stop": False}
        threading.Thread(target=self._chaine, args=(self.ch, False), daemon=True).start()
        return {"devis": dv, "etat": "en cours"}

    def chaine_suite(self, b):
        c = self.ch
        if not c or c["projet"] != b["id"] or c["etat"] != "pause":
            raise ValueError("aucune chaîne en pause pour ce projet")
        c.update(etat="en cours", etape="reprise", stop=False)
        threading.Thread(target=self._chaine, args=(c, True), daemon=True).start()
        return {"etat": "en cours"}

    def chaine_stop(self, b):
        c = self.ch
        if not c or c["projet"] != b["id"] or c["etat"] not in ("en cours", "pause"):
            raise ValueError("aucune chaîne à arrêter pour ce projet")
        if c["etat"] == "pause":
            c.update(etat="arretee", etape="arrêtée à la pause")
            _dump(self.data / "chaine.json", c)
        else:
            c["stop"] = True  # prise en compte a la fin de l'etape en cours
        return {"etat": c["etat"]}

    def _pas(self, c, texte):
        c["etape"] = texte
        c["journal"] = (c["journal"] + [f"{time.strftime('%H:%M')} {texte}"])[-12:]

    def _lancer_chaine(self, c, quoi, **kw):
        while self.studio.running():  # un test ou un autre calcul finit d'abord
            time.sleep(5)
        self.produire({"id": c["projet"], "quoi": quoi, "hd": c["hd"], **kw}, chaine=True)
        while self.studio.running():
            time.sleep(4)
        r = self.prod(c["projet"])
        if r["etat"] != "termine" or r["echecs"]:
            raise RuntimeError(f"{quoi} : " + (f"{r['echecs']} échec(s)" if r["etat"] == "termine" else "calcul " + r["etat"]) + ". " + r["log"][-300:])

    def _chaine(self, c, suite):
        _dump(self.data / "chaine.json", c)
        try:
            self._chaine_pas(c, suite)
        finally:
            _dump(self.data / "chaine.json", c)

    def _chaine_pas(self, c, suite):
        pid = c["projet"]
        try:
            if not suite:
                p = self._raw(pid)
                ids = self._a_imager(p, self._choix(p), c["temps"], c["refaire"])
                if ids:
                    self._pas(c, f"images ({len(ids)})")
                    self._lancer_chaine(c, "images", scenes=ids)
                    if c["stop"]:
                        return c.update(etat="arretee", etape="arrêtée après les images")
                    if c["mode"] == "pause":
                        for t in c["temps"]:  # relecture des images pendant la pause ; elle ne bloque jamais la chaine
                            try:
                                if t in (1, 2):
                                    self.relire({"id": pid, "temps": t})
                            except Exception:
                                pass
                        self._pas(c, "pause : choisir les prises, puis Continuer")
                        return c.update(etat="pause")
            for t in c["temps"]:
                e = self._eff(self._raw(pid))
                if self.devis(e, t)["clips"]["n"]:
                    self._pas(c, f"temps {t} : clips ({self.devis(e, t)['clips']['n']})")
                    self._lancer_chaine(c, "clips", temps=t)
                    if c["stop"]:
                        return c.update(etat="arretee", etape=f"arrêtée après les clips du temps {t}")
                e = self._eff(self._raw(pid))
                if [s for s in e["scenes"] if s["temps"] == t and (s["clip"] or s["image"])]:
                    self._pas(c, f"temps {t} : montage")
                    while pid in self.montages:
                        time.sleep(2)
                    self.monter({"id": pid, "temps": t})
                    while pid in self.montages:
                        time.sleep(2)
                    m = _load(self._pdir(pid) / "montage.json", {})
                    if m.get("etat") != "pret":
                        raise RuntimeError("montage : " + str(m.get("erreur") or "interrompu"))
                if c["stop"] and t != c["temps"][-1]:
                    return c.update(etat="arretee", etape=f"arrêtée après le temps {t}")
            self._pas(c, "terminée")
            c.update(etat="termine")
        except Exception as e:
            self._pas(c, "erreur : " + str(e)[-300:])
            c.update(etat="erreur", erreur=str(e)[-500:])

    # --- Montage ----------------------------------------------------------------------------------
    def monter(self, b):
        pid, t = b["id"], int(b.get("temps") or 1)
        if t not in TEMPS:
            raise ValueError("temps inconnu")
        p = self._eff(self._raw(pid))
        p["scenes"] = [s for s in p["scenes"] if s["temps"] == t]
        if t != 1:  # l'accroche et le carton de fin sont ceux du teaser
            p |= {"accroche": "", "cta": ""}
        else:  # le teaser se publie : la mention IA n'est pas une option
            p["montage"] = {**p["montage"], "label": True}
        if pid in self.montages:
            raise ValueError("un montage est déjà en cours pour ce projet")
        if not [s for s in p["scenes"] if s["clip"] or s["image"]]:
            raise ValueError("aucune image ni clip à monter")
        d = self._pdir(pid)
        _dump(d / "montage.json", {"etat": "en cours"})
        th = threading.Thread(target=self._monter, args=(p, d, t), daemon=True)
        self.montages[pid] = th
        th.start()
        return {"etat": "en cours"}

    def _monter(self, p, d, temps=1):
        pid = p["id"]
        tmp = d / "tmp"
        try:
            shutil.rmtree(tmp, ignore_errors=True)
            tmp.mkdir()
            perso = self.persos().get(p["personnage"]) or {}
            vus = self._finals(pid, temps)
            out = d / f"final_{'' if temps == 1 else f't{temps}_'}v{(int(re.search(r'v(\d+)', vus[-1]).group(1)) if vus else 0) + 1}.mp4"
            info = monter(p, d / "media", tmp, out, self.da, (perso.get("ecriture") or {}).get("plateforme", ""))
            with self.lock:
                infos = {k: v for k, v in _load(d / "finals.json", {}).items() if (d / k).is_file()}
                _dump(d / "finals.json", infos | {out.name: info | {"date": time.strftime("%Y-%m-%d %H:%M")}})
            try:
                planche(out, info, d / _nom_planche(out.name))
            except Exception:
                pass  # la planche est un confort : le montage reste bon sans elle
            _dump(d / "montage.json", {"etat": "pret", "fichier": out.name})
        except Exception as e:
            _dump(d / "montage.json", {"etat": "erreur", "erreur": str(e)[-400:]})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            self.montages.pop(pid, None)

    def supprimer_final(self, pid, name):
        if not re.fullmatch(r"final_(t[234]_)?v\d+\.mp4", str(name)):
            raise ValueError("fichier invalide")
        (self._pdir(pid) / name).unlink(missing_ok=True)
        (self._pdir(pid) / _nom_planche(name)).unlink(missing_ok=True)

    def planche(self, pid, name):
        """Cree la planche de controle d'une video montee avant que la planche soit faite d'office."""
        if not re.fullmatch(r"final_(t[234]_)?v\d+\.mp4", str(name)):
            raise ValueError("fichier invalide")
        d = self._pdir(pid)
        if not (d / name).is_file():
            raise ValueError("vidéo introuvable")
        planche(d / name, _load(d / "finals.json", {}).get(name) or {}, d / _nom_planche(name))
        return _nom_planche(name)

    def vers_tri(self, pid, name):
        """Copie une video montee dans la boite du Tri (validation humaine avant publication)."""
        if not re.fullmatch(r"final_(t[234]_)?v\d+\.mp4", str(name)):
            raise ValueError("fichier invalide")
        p = self._raw(pid)
        dest = self.data / "inbox" / f"{pid}_{re.sub(r'[^a-z0-9]+', '_', p['titre'].lower()).strip('_')[:30]}_{name[6:]}"
        shutil.copy(self._pdir(pid) / name, dest)
        return dest.name

    # --- HTTP -------------------------------------------------------------------------------------
    def get(self, path, q):
        g = lambda k: q.get(k, [""])[0]
        if path == "/api/a/etat":
            return self.etat()
        if path == "/api/a/personnage":
            return self.perso(g("slug"))
        if path == "/api/a/projet":
            return self.projet(g("id"))
        if path == "/api/a/ecrire":
            return self.resultat(g("rid"))
        return None

    def post(self, path, b):
        if path == "/api/a/personnage":
            return {"personnage": self.save_perso(b)}
        if path == "/api/a/projet":
            p = self.save_projet(b)
            return {"projet": p, "controle": {t: self._ctl(p, t) for t in TEMPS}}
        if path == "/api/a/ecrire":
            return self.ecrire(b)
        if path == "/api/a/produire":
            return self.produire(b)
        if path == "/api/a/relire":
            return self.relire(b)
        if path == "/api/a/analyser":
            return self.analyser(b)
        if path == "/api/a/monter":
            return self.monter(b)
        if path == "/api/a/chaine":
            return self.chaine(b)
        if path == "/api/a/chaine/continuer":
            return self.chaine_suite(b)
        if path == "/api/a/chaine/arreter":
            return self.chaine_stop(b)
        if path == "/api/a/depot/importer":
            return self.importer(b)
        if path == "/api/a/lora":
            return {"bibliotheque": self.save_lora(b)}
        if path == "/api/a/lora/defauts":
            return {"bibliotheque": self.save_defauts(b)}
        if path == "/api/a/final/supprimer":
            self.supprimer_final(b["id"], b["fichier"])
            return {}
        if path == "/api/a/final/planche":
            return {"fichier": self.planche(b["id"], b["fichier"])}
        if path == "/api/a/final/tri":
            return {"fichier": self.vers_tri(b["id"], b["fichier"])}
        return None


# --- Montage : ffmpeg -----------------------------------------------------------------------------
def _ff(*args):
    ff = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    if not ff:
        raise RuntimeError("ffmpeg introuvable")
    r = subprocess.run([ff, "-y", "-loglevel", "error", *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("ffmpeg : " + r.stderr.strip()[-350:])


def _nom_planche(final):
    return "planche_" + final[6:-4] + ".jpg"


def _duree(path):
    r = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise RuntimeError(f"durée illisible : {Path(path).name}")


def _vues(info, duree, maxi=16):
    """Instants d'une video montee a regarder pour la juger : debut, milieu de chaque scene, de part et d'autre de chaque
    jointure, fin. Rend ([(instant, role, etiquette courte)], ids des scenes, debuts, fins) d'apres la fiche du montage."""
    vues, deb, ids = [], info.get("debuts") or [], [x[0] for x in info.get("prises") or []]
    fins = []
    if deb and len(deb) == len(ids):
        fins = deb[1:] + [info.get("carton") or duree]
        vues.append((0.05, "première image de la vidéo", "début"))
        for i, (a, z) in enumerate(zip(deb, fins)):
            if i:
                genre = "sans coupe" if info["colle"][i] else "coupe"
                vues += [(a - 0.07, f"dernière image avant la jointure {i} ({genre})", f"avant jointure {i} ({genre})"),
                         (a + 0.07, f"première image après la jointure {i} ({genre})", f"après jointure {i}")]
            vues.append(((a + z) / 2, f"milieu de la scène {i + 1}", f"scène {i + 1}, milieu"))
        if info.get("carton"):
            vues.append((info["carton"] + 1.0, "carton de fin", "carton"))
        else:
            vues.append((duree - NOIR - 0.15, "dernière image avant le fondu au noir", "fin"))
        if len(vues) > maxi:  # trop de scenes : les milieux sautent d'abord
            vues = [v for v in vues if not v[1].startswith("milieu")][:maxi]
    else:  # video montee avant la fiche technique : images regulierement espacees
        ids = []
        vues = [(0.05, "première image de la vidéo", "début")] + [(duree * k / 9, "image", "") for k in range(1, 9)] + [(duree - 0.6, "fin de la vidéo", "fin")]
    return sorted((min(max(a, 0), max(0, duree - 0.05)), r, c) for a, r, c in vues), ids, deb, fins


def planche(src, info, out):
    """Planche de controle d'une video montee : les images que regarde l'analyste, cote a cote, avec l'instant et le role de
    chacune. Sans IA ni GPU."""
    duree = info.get("duree") or _duree(src)
    vues = _vues(info, duree, 24)[0]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for k, (a, _, court) in enumerate(vues):
            (tmp / "t.txt").write_text(f"{a:.1f} s  {court}".strip(), encoding="utf-8")
            _ff("-ss", f"{a:.2f}", "-i", src, "-frames:v", "1", "-vf", f"scale=-2:480:out_range=pc,format=yuvj420p,drawtext=fontfile={FONT}:textfile={tmp / 't.txt'}:fontsize=15"
                ":fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=5:x=6:y=6", "-q:v", "4", tmp / f"{k:02d}.jpg")
        # toutes les vues au meme format : un changement en cours de route viderait la mosaique
        cols = min(len(vues), 4)
        _ff("-i", tmp / "%02d.jpg", "-vf", f"tile={cols}x{-(-len(vues) // cols)}:padding=6:margin=6:color=0x15191d", "-frames:v", "1", "-q:v", "4", out)


def _texte(tmp, cle, texte, taille, centre, w, h, style="doux", quand="", haut=False, alpha=1.0):
    """Calque d'un texte centre sur la hauteur `centre` (fraction de h) : [(image PNG transparente, condition)].
    Pas de fond en aplat : le texte est blanc sur une ombre floue (et un contour fin pour le style "contour").
    `quand` : condition ffmpeg d'affichage (sur t, en secondes depuis le debut du segment), vide pour toujours.
    `haut` : texte du haut de l'image (accroche). `centre` est alors le bas du bloc, qui ne descend jamais plus bas
    (le visage est dessous) ; la police retrecit jusqu'a tenir en deux lignes, et le bloc reste sous la mention IA.
    `alpha` : opacite du texte (mention IA discrete)."""
    texte = "".join(c for c in str(texte or "") if ord(c) < 0x2190).strip()  # les polices n'ont pas les emojis
    if not texte:
        return []
    nom, echelle, contour = STYLES.get(style, STYLES["doux"])
    police = Path(__file__).parent / "polices" / nom
    if not police.is_file():
        police = FONT
    for k in (1, 0.9, 0.8, 0.7) if haut else (1,):
        fs = round(h * taille * k * echelle)
        lignes = textwrap.wrap(texte, max(8, int(w * 0.86 / (fs * (0.5 if style == "serif" else 0.6))))) or [texte]
        if len(lignes) <= 2:
            break
    f = tmp / f"{cle}.txt"
    f.write_text("\n".join(lignes), encoding="utf-8")
    y = f"max({round(h * 0.075)}\\,{round(h * centre)}-text_h)" if haut else f"{round(h * centre)}-text_h/2"
    trait = lambda couleur, plus="": (f"drawtext=fontfile={police}:textfile={f}:fontsize={fs}:fontcolor={couleur}{plus}:text_align=C"
                                      f":line_spacing={round(fs * 0.12)}:x=(w-text_w)/2:y={y}")
    bord = max(1, round(fs * 0.045))
    vf = [trait(f"black@{0.95 * alpha:.2f}", f":borderw={bord}:bordercolor=black@{0.95 * alpha:.2f}"), f"gblur=sigma={fs * 0.2:.1f}",
          trait(f"black@{0.75 * alpha:.2f}", f":borderw={bord}:bordercolor=black@{0.6 * alpha:.2f}"), f"gblur=sigma={max(1.0, fs * 0.05):.1f}",
          trait(f"white@{alpha:.2f}", f":borderw={max(2, round(fs * 0.05))}:bordercolor=black@0.85" if contour else "")]
    png = tmp / f"{cle}.png"
    _ff("-f", "lavfi", "-i", f"color=c=black@0.0:s={w}x{h},format=rgba", "-vf", ",".join(vf), "-frames:v", "1", png)
    return [(png, quand)]


def _poser(avant, calques, apres=()):
    """Arguments ffmpeg qui posent des calques de texte sur la video (entree 0) : (entrees en plus, graphe et sortie)."""
    args, g, prev = [], [f"[0:v]{avant}[c0]"], "c0"
    for k, (png, quand) in enumerate(calques, 1):
        args += ["-i", png]
        g.append(f"[{prev}][{k}:v]overlay" + (f"=enable='{quand}'" if quand else "") + f"[c{k}]")
        prev = f"c{k}"
    g.append(f"[{prev}]{','.join(apres) or 'null'}[v]")
    return args, ["-filter_complex", ";".join(g), "-map", "[v]"]


def _teinte(src, t=None):
    """Moyenne rouge, vert, bleu d'une image d'un clip : a l'instant t, ou la derniere si t est None."""
    r = subprocess.run([os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg"), "-loglevel", "error",
                        *(("-sseof", "-0.25") if t is None else ("-ss", f"{t:.3f}")), "-i", str(src), *(() if t is None else ("-frames:v", "1")),
                        "-vf", "scale=32:32:flags=area,format=rgb24", "-f", "rawvideo", "-"], capture_output=True)
    b = r.stdout[-3072:]
    return [sum(b[i::3]) / 1024 for i in range(3)] if len(b) == 3072 else None


def _plans(p, media):
    """Decoupe du montage : pour chaque scene qui a un clip ou une image, {"s", "deb", "dur", "colle"}.
    `colle` : le plan suit le precedent sans coupe (raccord continu ou arrivee, les deux clips entiers a la jointure) ;
    l'image en double de la jointure est alors retiree. Si une duree est visee (montage.cible), les plans libres
    sont raccourcis en proportion, jamais sous PLANCHER et jamais du cote d'une jointure collee."""
    m, prec, plans, derniere = p["montage"], _prec(p), [], None
    for s in [s for s in p["scenes"] if s["clip"] or s["image"]]:
        if s["clip"]:
            total = _duree(media / s["clip"])
            deb = min(s["debut"], max(0, total - 1))
            dur = min(s["duree"] or total, total - deb)
            colle = bool(derniere and s["raccord"] != "coupe" and prec[s["id"]] is derniere and derniere["clip"]
                         and not s["debut"] and not derniere["duree"])
            if colle:
                deb, dur = JOINT, dur - JOINT
        else:
            deb, dur, colle = 0, s["duree"] or FIXE, False
        plans.append({"s": s, "deb": deb, "dur": dur, "colle": colle})
        derniere = s
    carton = 2.6 if m["carton"] and p.get("cta") else 0
    trop = sum(x["dur"] for x in plans) + carton - (m.get("cible") or 0)
    if m.get("cible") and trop > 0:
        marges = []
        for i, x in enumerate(plans):  # (plan, marge, debut libre, fin libre) ; les reglages faits a la main ne sont pas touches
            av, ap = not x["colle"], i + 1 == len(plans) or not plans[i + 1]["colle"]
            if x["s"]["clip"] and not x["s"]["debut"] and not x["s"]["duree"] and (av or ap) and x["dur"] > PLANCHER:
                marges.append((x, x["dur"] - PLANCHER, av, ap))
        dispo = sum(g[1] for g in marges)
        for x, marge, av, ap in marges:
            c = marge * min(1, trop / dispo)
            x["deb"] += c * (2 / 3 if ap else 1) if av else 0  # le debut d'un clip est le moment ou il se passe le moins de choses
            x["dur"] -= c
    return plans, carton


def monter(p, media, tmp, out, audio_dir, plateforme=""):
    """Assemble les scenes d'un projet : clip retenu (ou image en zoom lent a defaut), texte a l'ecran,
    accroche sur la premiere scene, carton de fin, fondu au noir, musique. Ecrit `out` et renvoie ce qui a ete monte."""
    m = p["montage"]
    w, h = FORMATS[m["format"]]
    fps, x = 32, 0.35
    base = f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}"
    fin = f"fps={fps},setsar=1,format=yuv420p"
    enc = ["-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-video_track_timescale", "16384"]
    style = m.get("style") or "doux"
    label = _texte(tmp, "label", "AI character", 0.0125, 0.04, w, h, alpha=0.6) if m["label"] else []
    gains = [1.0, 1.0, 1.0]  # correction de couleur du plan en cours (raccord sans coupe)
    segs, durs = [], []  # segs : groupes de segments ; rien ne separe les segments d'un meme groupe
    plans, carton = _plans(p, media)
    noir = lambda dur: [f"fade=t=out:st={max(0, dur - NOIR):.3f}:d={NOIR}"] if m.get("noir") else []
    for i, pl in enumerate(plans):
        s, deb, dur = pl["s"], pl["deb"], pl["dur"]
        txt = []
        if m["textes"]:
            if i == 0 and p.get("accroche") and p["accroche"] != s["texte"]:
                # un seul texte a la fois : l'accroche d'abord, le texte de la scene ensuite
                bascule = min(2.5, dur / 2) if s["texte"] else 0
                txt += _texte(tmp, f"acc{i}", p["accroche"], 0.04, 0.19, w, h, style, f"lt(t,{bascule:.2f})" if bascule else "", haut=True)
                txt += _texte(tmp, f"txt{i}", s["texte"], 0.034, 0.72, w, h, style, f"gte(t,{bascule:.2f})")
            else:
                txt += _texte(tmp, f"txt{i}", s["texte"], 0.034, 0.72, w, h, style)
        queue = noir(dur) if i + 1 == len(plans) and not carton else []
        seg = tmp / f"seg{i}.mp4"
        if s["clip"]:
            couleur = []
            if pl["colle"]:  # le modele video assombrit ou teinte le debut du clip suivant : on l'aligne sur la fin du precedent
                a, b = _teinte(media / plans[i - 1]["s"]["clip"]), _teinte(media / s["clip"], deb)
                if a and b:
                    gains = [min(1.1, max(0.9, g * x / max(1.0, y))) for g, x, y in zip(gains, a, b)]
                    couleur = ["colorchannelmixer=rr={:.4f}:gg={:.4f}:bb={:.4f}".format(*gains)]
            else:
                gains = [1.0, 1.0, 1.0]
            ins, graphe = _poser(",".join([base] + couleur + [fin]), txt + label, queue)
            _ff("-ss", f"{deb:.3f}", "-t", f"{dur:.3f}", "-i", media / s["clip"], *ins, *graphe, *enc, seg)
        else:  # pas de clip : image en zoom lent, pour qu'elle ne paraisse pas figee
            nb = round(dur * fps)
            zoom = (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase:flags=lanczos,crop={w * 2}:{h * 2},"
                    f"zoompan=z='1+0.1*on/{nb}':x='iw/2-(iw/zoom/2)':y='ih*0.42-(ih/zoom*0.42)':d={nb}:s={w}x{h}:fps={fps}")
            gains = [1.0, 1.0, 1.0]
            ins, graphe = _poser(zoom + ",setsar=1,format=yuv420p", txt + label, queue)
            _ff("-i", media / s["image"], *ins, *graphe, "-frames:v", nb, *enc, seg)
        if pl["colle"]:
            segs[-1].append(seg)
        else:
            segs.append([seg])
        durs.append(_duree(seg))
    if carton:
        derniere = plans[-1]["s"]
        fond = tmp / "fond.png"
        if derniere["image"]:
            shutil.copy(media / derniere["image"], fond)
        else:
            _ff("-i", media / derniere["clip"], "-frames:v", "1", fond)
        txt = _texte(tmp, "cta", p["cta"], 0.044, 0.46, w, h, style) + _texte(tmp, "plat", plateforme, 0.022, 0.56, w, h, "doux", alpha=0.85)
        seg = tmp / "carton.mp4"
        ins, graphe = _poser(",".join([base, "boxblur=28:3,eq=brightness=-0.22:saturation=0.8", fin]), txt + label, noir(carton))
        _ff("-loop", "1", "-t", f"{carton}", "-i", fond, *ins, *graphe, *enc, seg)
        segs.append([seg])
        durs.append(_duree(seg))
    durs_plans = durs[:len(plans)]
    muet = tmp / "muet.mp4" if m.get("musique") else out

    def coller(fichiers, sortie, *opts):
        liste = tmp / f"{sortie.stem}.txt"
        liste.write_text("".join(f"file '{s}'\n" for s in fichiers), encoding="utf-8")
        _ff("-f", "concat", "-safe", "0", "-i", liste, "-c", "copy", *opts, sortie)

    def fondre(fichiers, ds, d, sortie, *opts):
        args, fc, acc, prev = [], [], 0.0, "0:v"
        for seg in fichiers:
            args += ["-i", seg]
        for i in range(1, len(fichiers)):
            acc += ds[i - 1] - d
            fc.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={d:.5f}:offset={acc:.3f}[v{i}]")
            prev = f"v{i}"
        _ff(*args, "-filter_complex", ";".join(fc), "-map", f"[{prev}]", *opts, sortie)

    k = 0
    for i, g in enumerate(segs):  # un groupe continu devient un seul segment, ses jointures fondues sur quelques images
        if len(g) > 1:
            fondre(g, durs[k:k + len(g)], FONDU_JOINT / fps, tmp / f"groupe{i}.mp4", *enc)
            segs[i] = [tmp / f"groupe{i}.mp4"]
        k += len(g)
    segs = [g[0] for g in segs]
    durs = [_duree(g) for g in segs]
    if m["transition"] == "fondu" and len(segs) > 1:
        fondre(segs, durs, x, muet, "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart")
        total = sum(durs) - x * (len(segs) - 1)
    else:
        coller(segs, muet, "-movflags", "+faststart")
        total = sum(durs)
    if m.get("musique"):
        src = (audio_dir / m["musique"]).resolve()
        if src.parent != audio_dir.resolve() or not src.is_file():
            raise RuntimeError("musique introuvable dans data/audio")
        _ff("-i", muet, "-stream_loop", "-1", "-i", src, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
            "-af", f"afade=t=in:d=0.4,afade=t=out:st={max(0, total - 1.2):.2f}:d=1.2", "-t", f"{total:.2f}", "-movflags", "+faststart", out)
    fondu, debuts, groupe, acc = m["transition"] == "fondu" and len(plans) - sum(x["colle"] for x in plans) + bool(carton) > 1, [], -1, 0.0
    for pl, dur in zip(plans, durs_plans):  # instant ou chaque plan commence dans la video (un fondu recouvre x secondes)
        groupe += not pl["colle"]
        acc -= FONDU_JOINT / fps if pl["colle"] else 0
        debuts.append(round(acc - (x * groupe if fondu else 0), 2))
        acc += dur
    return {"duree": round(total, 2), "label": bool(m["label"]), "cible": m.get("cible") or 0, "plans": len(plans),
            "debuts": debuts, "colle": [x["colle"] for x in plans], "carton": round(total - carton, 2) if carton else 0,
            "images": sum(1 for x in plans if not x["s"]["clip"]), "colles": sum(1 for x in plans if x["colle"]),
            "prises": [[x["s"]["id"], x["s"]["clip"] or x["s"]["image"]] for x in plans]}
