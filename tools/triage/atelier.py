"""Atelier : du personnage a la video montee.

Socle : les personnages (fiche, ton, reglages de generation). Au-dessus : les projets, un par video.
Un projet suit cinq etapes : idee, scenario (scenes, textes a l'ecran, voix), images, clips, montage.
L'ecriture est confiee au redacteur IA (server/writer, file d'attente dans data/ecriture) ; s'il ne
repond pas, un redacteur de secours (moteur_local.py) tire un scenario d'une structure toute faite.
Les images et les clips passent par le pilote, donc par le plafond GPU du jour.

Un projet couvre trois temps (docs/feuille-de-route.md) : 1 accroche tous publics, 2 montee pour les
abonnes, 3 final prive. Chaque scene porte son temps. Le redacteur ecrit les temps 1 et 2 ; le temps 3
est a la main du proprietaire, ou alimente par un plan depose par son agent dans server/jobs/atelier/.

Donnees : data/personnages/<slug>.json, data/projets/<id>/ (projet.json, runs/, media/, final_vN.mp4),
data/ecriture/ (demandes et reponses du redacteur), data/audio/ (musiques deposees par le proprietaire).
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path

import moteur_local

AGE_MIN = 21
ETAPES = ("idee", "ecrit", "images", "clips", "monte", "valide")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TEMPS = {1: "accroche", 2: "montee", 3: "final"}
FORMATS = {"vertical": (1080, 1920), "carre": (1080, 1080), "paysage": (1920, 1080)}

SYSTEME = """Tu es scénariste, dialoguiste et monteur de teasers vidéo courts pour un personnage fictif, adulte, généré par IA et présenté comme tel. Tu écris pour vendre : la vidéo doit arrêter le pouce dans la première seconde, faire monter l'envie, couper juste avant la suite et envoyer vers la page payante du personnage.

REGISTRE
Classe, sensuel, aguicheur. Suggestif, jamais explicite : pas de nudité, pas d'acte sexuel, pas de mot cru. Tout passe par le regard, la tenue, le décolleté, le geste lent, le cadrage, le sous-entendu et l'ellipse. Ce qui n'est pas montré vend mieux que ce qui l'est. Le personnage a de l'humour et une vraie personnalité : sers-toi de ses tics, de ses défauts, de son univers.

CE QUI FAIT CLIQUER
- Première scène : une accroche lisible en une seconde (adresse directe, POV, défi, question, promesse, interruption).
- Une boucle ouverte : quelque chose commence et ne se termine pas dans la vidéo.
- Une progression nette : chaque scène va un cran plus loin que la précédente (distance à la caméra, regard, tenue, geste).
- Dernière scène : la coupe arrive au moment où l'on veut voir la suite, avec un appel à l'action court et concret.
- Lisible sans le son : le texte à l'écran porte l'histoire.

CONTRAINTES TECHNIQUES (modèles d'image et de vidéo)
- Chaque scène = une image de départ, puis un clip de 5 secondes animé à partir de cette image.
- "still" : en anglais, une seule phrase dense : cadrage, lieu, tenue, pose, expression, lumière. Format vertical. Une seule personne à l'image. Ne décris ni le visage, ni les cheveux, ni les tatouages, ni les bijoux : ils sont ajoutés automatiquement. Aucun texte dans l'image.
- "motion" : en anglais, UN geste simple et lent, en une phrase commençant par "She". Gestes fiables : regarder l'objectif, sourire lentement, pencher la tête, se mordre la lèvre, se pencher vers la caméra, marcher vers la caméra, faire glisser une bretelle, ajuster un décolleté, s'étirer doucement, boire, respirer. Gestes interdits (ils ratent) : tourner le dos, attacher ses cheveux, passer la main devant le visage, renverser la tête, éclater de rire, cheveux au vent, manipuler un objet compliqué, changer de vêtement.
- "end_edit" : presque toujours "". À remplir seulement si la pose doit changer nettement entre le début et la fin du clip (assise puis debout) : une phrase en anglais qui décrit la pose finale, même cadrage.
- Continuité : dans une même séquence, répète le lieu et la tenue avec exactement les mêmes mots d'une scène à l'autre.
- "texte" : texte incrusté pendant la scène, dans la langue du personnage, 7 mots au plus. Aucun emoji, ni là ni dans l'accroche (la police de montage ne les affiche pas). "voix" : phrase de voix off dans sa voix, 12 mots au plus, ou "".
- "tattoos" : false si la tenue couvre les épaules et la poitrine (pull, peignoir fermé), sinon true.
- "role" : "accroche", "montee" ou "chute".
- Le personnage ne prétend jamais être une personne réelle. Aucune personne réelle, aucune marque, aucun mineur, rien qui évoque la jeunesse.

SORTIE
Un seul objet JSON valide, sans texte autour, sans bloc de code. Les champs "titre" et "pitch" sont en français ; les textes publiés (accroche, texte, voix, legende, cta, hashtags) sont dans la langue du personnage."""

SCHEMA = ('{"titre": "...", "pitch": "une phrase", "accroche": "texte à l\'écran de la première seconde", '
          '"scenes": [{"titre": "...", "role": "accroche|montee|chute", "still": "...", "motion": "...", "end_edit": "", '
          '"texte": "...", "voix": "", "tattoos": true}], "legende": "légende de la publication, 1 à 2 phrases, avec l\'appel à l\'action", '
          '"cta": "carton de fin, 6 mots au plus", "hashtags": "3 à 5 mots-dièse"}')


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
        self._dep = (0, None)

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
        for s in p.get("scenes") or []:  # projets d'avant les trois temps
            s.setdefault("temps", 1), s.setdefault("loras", ""), s.setdefault("origine", "")
        p.setdefault("brief2", ""), p.setdefault("nb2", 3), p.setdefault("depots", {})
        return p

    def _scene(self, d, proj):
        sid = d.get("id") if re.fullmatch(r"s\d+", str(d.get("id") or "")) else None
        if not sid:
            sid = f"s{proj['next']}"
            proj["next"] += 1
        return {"id": sid, "titre": _s(d.get("titre"), 80), "role": d.get("role") if d.get("role") in ("accroche", "montee", "chute") else "montee",
                "temps": int(d.get("temps") or 1) if str(d.get("temps") or 1) in ("1", "2", "3") else 1,
                "loras": _loras(d.get("loras")), "origine": _s(d.get("origine"), 120),
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
                old = {"id": pid, "personnage": b["personnage"], "cree": time.strftime("%Y-%m-%d %H:%M"), "next": 1}
            m = b.get("montage") or old.get("montage") or {}
            p = {"id": pid, "personnage": old["personnage"], "cree": old.get("cree"), "modifie": time.strftime("%Y-%m-%d %H:%M"),
                 "next": int(old.get("next") or 1), "titre": _s(b.get("titre", old.get("titre")), 100) or "Sans titre",
                 "statut": b.get("statut", old.get("statut")) if b.get("statut", old.get("statut")) in ("", "valide", "publie", "archive") else "",
                 "brief": _s(b.get("brief", old.get("brief")), 1500), "suite": _s(b.get("suite", old.get("suite")), 600),
                 "nb_scenes": max(2, min(int(b.get("nb_scenes", old.get("nb_scenes")) or 3), 8)),
                 "brief2": _s(b.get("brief2", old.get("brief2")), 1500), "nb2": max(2, min(int(b.get("nb2", old.get("nb2")) or 3), 6)),
                 "depots": old.get("depots") or {},
                 "pitch": _s(b.get("pitch", old.get("pitch")), 400), "accroche": _s(b.get("accroche", old.get("accroche")), 120),
                 "legende": _s(b.get("legende", old.get("legende")), 600), "cta": _s(b.get("cta", old.get("cta")), 120),
                 "hashtags": _s(b.get("hashtags", old.get("hashtags")), 200), "attente": old.get("attente") or "",
                 "montage": {"transition": m.get("transition") if m.get("transition") in ("coupe", "fondu") else "coupe",
                             "format": m.get("format") if m.get("format") in FORMATS else "vertical",
                             "textes": bool(m.get("textes", True)), "carton": bool(m.get("carton", True)),
                             "label": bool(m.get("label", False)), "musique": _s(m.get("musique"), 120)}}
            p["scenes"] = [self._scene(s, p) for s in (b["scenes"] if "scenes" in b else old.get("scenes") or [])][:30]
            _dump(self.dj / pid / "projet.json", p)
            return p

    def prises(self, pid):
        """Prises de chaque scene, de la plus ancienne a la plus recente. "source" : image dont un clip est tire."""
        d, out, runs = self._pdir(pid), {}, {}
        for f in sorted((d / "media").iterdir(), key=lambda f: f.stat().st_mtime):
            m = re.fullmatch(rf"{pid}(r\d+)_(s\d+)\.(png|mp4)", f.name)
            if not m:
                continue
            t = out.setdefault(m.group(2), {"images": [], "clips": [], "source": {}})
            if m.group(3) == "png":
                t["images"].append(f.name)
                continue
            if m.group(1) not in runs:
                runs[m.group(1)] = {x["name"]: Path(x.get("image") or "").name for x in (_load(d / "runs" / f"{m.group(1)}.json") or {}).get("shots", [])}
            t["clips"].append(f.name)
            t["source"][f.name] = runs[m.group(1)].get(m.group(2), "")
        return out

    def _choix(self, p, pr=None):
        """Prise retenue pour chaque scene : celle choisie si elle existe encore, sinon la derniere.
        Un clip ne compte que s'il a ete tire de l'image retenue."""
        pr = pr if pr is not None else self.prises(p["id"])
        out = {}
        for s in p["scenes"]:
            t = pr.get(s["id"], {"images": [], "clips": [], "source": {}})
            img = s["image"] if s["image"] in t["images"] else (t["images"][-1] if t["images"] else "")
            clips = [c for c in t["clips"] if t["source"].get(c) == img]
            out[s["id"]] = {"image": img, "clip": s["clip"] if s["clip"] in clips else (clips[-1] if clips else "")}
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
        if all(s["image"] for s in sc):
            return "images"
        return "ecrit"

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
                "devis": {t: self.devis(e, t) for t in TEMPS}, "depots": [x for x in self.depots() if x.get("projet") == pid]}

    def liste(self):
        out = []
        for d in sorted(self.dj.glob("p*/projet.json"), reverse=True):
            p = self._raw(d.parent.name)
            if p.get("statut") == "archive":
                continue
            p = self._eff(p)
            finals = self._finals(p["id"])
            out.append({"id": p["id"], "personnage": p["personnage"], "titre": p["titre"], "pitch": p.get("pitch", ""),
                        "modifie": p.get("modifie"), "etape": self._etape(p, finals), "scenes": len(p["scenes"]),
                        "temps": sorted({s["temps"] for s in p["scenes"]}),
                        "vignette": next((s["image"] for s in p["scenes"] if s["image"]), ""), "final": finals[-1] if finals else ""})
        return out

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
        """Texte d'un temps du projet pour le redacteur. Le temps 3 ne lui est jamais envoye."""
        keep = ("id", "titre", "role", "still", "motion", "end_edit", "texte", "voix", "tattoos")
        tete = {k: p.get(k) for k in ("titre", "pitch", "accroche", "legende", "cta", "hashtags")} if temps == 1 else {}
        return json.dumps(tete | {"scenes": [{k: s[k] for k in keep} for s in p["scenes"] if s["temps"] == temps]}, ensure_ascii=False, indent=1)

    def ecrire(self, b):
        kind = b.get("kind")
        consigne = _s(b.get("consigne"), 1500)
        proj = self._raw(b["projet"]) if b.get("projet") else None
        perso = self.perso(proj["personnage"] if proj else b.get("personnage")) if kind != "personnage" else None
        n = max(1, min(int(b.get("n") or 8), 12))
        if kind == "scenario":
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\nCOMMANDE\nÉcris le scénario complet d'un teaser en {proj['nb_scenes']} scènes.\n"
                      f"Idée de départ : {proj.get('brief') or 'libre, choisis l angle le plus vendeur pour ce personnage'}\n"
                      f"Suite payante annoncée : {proj.get('suite') or 'non précisée, reste vague sur son contenu'}\n"
                      f"{'Consigne : ' + consigne if consigne else ''}\n\nFORMAT\n{SCHEMA}")
        elif kind == "retouche":
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\nSCÉNARIO ACTUEL\n{self._texte_projet(proj)}\n\nCOMMANDE\nRéécris ce scénario selon la consigne : "
                      f"{consigne or 'rends-le plus accrocheur et plus vendeur'}\nGarde le champ \"id\" des scènes que tu conserves, et laisse leur \"still\" "
                      f"identique au mot près si l'image ne doit pas changer. Une scène nouvelle n'a pas d'\"id\".\n\nFORMAT\n{SCHEMA}")
        elif kind == "scene":
            sc = next((s for s in proj["scenes"] if s["id"] == b.get("scene")), None)
            if not sc:
                raise ValueError("scène inconnue")
            if sc["temps"] == 3:
                raise ValueError("le temps 3 est à votre main : le rédacteur IA ne l'écrit pas")
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\nSCÉNARIO\n{self._texte_projet(proj, sc['temps'])}\n\nCOMMANDE\nRéécris uniquement la scène \"{sc['id']}\" "
                      f"selon la consigne : {consigne or 'plus forte, plus sensuelle, toujours suggestive'}\n\nFORMAT\n"
                      '{"titre": "...", "role": "...", "still": "...", "motion": "...", "end_edit": "", "texte": "...", "voix": "", "tattoos": true}')
        elif kind == "temps2":
            if not [s for s in proj["scenes"] if s["temps"] == 1]:
                raise ValueError("écrire d'abord le teaser (temps 1) : la montée en est la suite")
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\nTEASER PUBLIC (temps 1, déjà écrit)\n{self._texte_projet(proj)}\n\nCOMMANDE\n"
                      f"Écris le temps 2 : la suite réservée aux abonnés, en {proj['nb2']} scènes. Ce n'est plus une publicité, c'est la récompense de "
                      "l'abonnement : elle reprend à l'instant où le teaser a coupé et va un cran plus loin à chaque scène (plus près, plus lente, plus "
                      "intime, regard plus appuyé, tenue plus défaite). Même lieu et même tenue que le teaser, avec exactement les mêmes mots dans "
                      "\"still\". Même registre : suggestif, jamais explicite. Pas d'appel à l'action ; la dernière scène laisse seulement entendre "
                      f"qu'un final privé existe, sans le décrire.\n{'Consigne : ' + (consigne or proj.get('brief2')) if (consigne or proj.get('brief2')) else ''}\n\nFORMAT\n"
                      '{"scenes": [{"titre": "...", "role": "accroche|montee|chute", "still": "...", "motion": "...", "end_edit": "", "texte": "...", "voix": "", "tattoos": true}]}')
        elif kind == "legendes":
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\nSCÉNARIO\n{self._texte_projet(proj)}\n\nCOMMANDE\nPropose {min(n, 5)} variantes d'accroche, de légende "
                      f"et de carton de fin pour cette vidéo, d'angles différents (défi, confidence, humour, promesse, urgence). {consigne}\n\nFORMAT\n"
                      '{"variantes": [{"angle": "...", "accroche": "...", "legende": "...", "cta": "..."}]}')
        elif kind == "idees":
            deja = [x["titre"] for x in self.liste() if x["personnage"] == perso["slug"]]
            prompt = (f"PERSONNAGE\n{self._fiche(perso)}\n\nCOMMANDE\nPropose {n} idées de teasers différentes, classées de la plus vendeuse à la moins vendeuse. "
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
                        p["scenes"][i] = self._scene({**s, **{k: res[k] for k in ("titre", "role", "still", "motion", "end_edit", "texte", "voix", "tattoos") if k in res}}, p)
            else:
                t = 2 if kind == "temps2" else 1  # les scenes des autres temps ne bougent pas
                old = {s["id"]: s for s in p["scenes"] if s["temps"] == t}
                for k in ("pitch", "accroche", "legende", "cta", "hashtags") if t == 1 else ():
                    p[k] = _s(res.get(k), 600)
                if t == 1 and res.get("titre") and (kind == "retouche" or p.get("titre") in ("", "Sans titre")):
                    p["titre"] = _s(res["titre"], 100)
                scenes = []
                for d in res.get("scenes") or []:
                    o = old.get(d.get("id")) or {}
                    scenes.append(self._scene({**{k: o[k] for k in ("id", "seed", "image", "clip", "debut", "duree") if k in o}, **d,
                                               **({"id": o["id"]} if o else {"id": None}), "temps": t, "loras": o.get("loras", ""), "origine": ""}, p))
                if not scenes:
                    raise ValueError("le rédacteur n'a renvoyé aucune scène")
                # les plans deposes par l'agent (origine) ne sont jamais ecrases par le redacteur
                garde = [s for s in p["scenes"] if s["temps"] != t or (kind == "temps2" and s["origine"])]
                p["scenes"] = sorted(scenes[:10] + garde, key=lambda s: s["temps"])
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
        if a.get("temps") not in (1, 2, 3):
            raise ValueError('"atelier.temps" doit valoir 1, 2 ou 3')
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
            if sh.get("steps") or sh.get("image"):
                raise ValueError(f"plan {nom} : \"steps\" et \"image\" ne sont pas repris par l'atelier")
            seed = sh.get("seed") or (int(d["seed"]) + (0 if d.get("same_seed") else i) if d.get("seed") else 0)
            scenes.append({"titre": sh.get("titre") or nom, "role": sh.get("role"), "temps": a["temps"], "still": sh["still"], "motion": sh.get("motion"),
                           "end_edit": sh.get("end_edit"), "texte": sh.get("texte"), "voix": sh.get("voix"), "tattoos": sh.get("tattoos", True),
                           "loras": sh.get("loras", d.get("loras")), "seed": seed, "origine": f"{f.name}:{nom}"})
        return {"projet": str(a.get("projet") or ""), "temps": a["temps"], "personnage": str(a.get("personnage") or ""),
                "titre": _s(a.get("titre"), 100), "note": _s(a.get("note"), 300), "modele": str(j.get("modele") or ""), "scenes": scenes}

    def depots(self):
        import yaml
        if not self.dd.is_dir():
            return []
        try:
            modele = str(yaml.safe_load((self.dd.parent / "modele.yaml").read_text(encoding="utf-8"))["modele"])
        except Exception:
            modele = ""
        vus, out = {}, []
        for f in sorted(self.dd.glob("*.yaml"), key=lambda f: f.stat().st_mtime, reverse=True)[:60]:
            x = {"fichier": f.name, "mtime": int(f.stat().st_mtime), "date": time.strftime("%d/%m %H:%M", time.localtime(f.stat().st_mtime))}
            try:
                if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}\.yaml", f.name):
                    raise ValueError("nom de fichier invalide (lettres, chiffres, _ . -)")
                pl = self._plan(f)
                x |= {k: pl[k] for k in ("projet", "temps", "personnage", "titre", "note")} | {"n": len(pl["scenes"]), "perime": bool(modele) and pl["modele"] != modele}
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

    def importer(self, b):
        """Verse les plans d'un fichier depose dans les scenes d'un temps du projet. Un nouvel import du meme
        fichier met a jour ses scenes (reperees par leur origine) en gardant leurs images tant que "still" est inchange."""
        f = self.dd / str(b.get("fichier"))
        if f.parent != self.dd or not f.is_file() or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}\.yaml", f.name):
            raise ValueError("fichier inconnu")
        pl = self._plan(f)
        pid = pl["projet"]
        if not pid:  # depot sans projet : en ouvrir un
            pid = self.save_projet({"personnage": pl["personnage"] or b.get("personnage"), "titre": pl["titre"] or f.stem})["id"]
        with self.lock:
            p = self._raw(pid)
            old = {s["origine"]: s for s in p["scenes"] if s["origine"].startswith(f.name + ":")}
            neuves = []
            for d in pl["scenes"]:
                o = old.get(d["origine"]) or {}
                garde = ("id", "seed", "image", "clip", "debut", "duree") if o and o["still"] == _s(d["still"], 1200) else ("id",) if o else ()
                neuves.append(self._scene({**d, **{k: o[k] for k in garde}, "seed": (o.get("seed") if "seed" in garde else 0) or d["seed"],
                                           "id": o.get("id")}, p))
            reste = [s for s in p["scenes"] if s["origine"] not in old]
            if len(reste) + len(neuves) > 30:
                raise ValueError("trop de scènes dans ce projet")
            p["scenes"] = sorted(reste + neuves, key=lambda s: s["temps"])
            p.setdefault("depots", {})[f.name] = int(f.stat().st_mtime)
            p["modifie"] = time.strftime("%Y-%m-%d %H:%M")
            _dump(self.dj / pid / "projet.json", p)
        return {"id": pid, "temps": pl["temps"], "scenes": len(neuves)}

    # --- Production (pilote) ----------------------------------------------------------------------
    def devis(self, p, temps=1):
        """Cout estime des deux lancements d'un temps, d'apres les couts constates (docs/journal-projet.md)."""
        img = [s for s in p["scenes"] if s["temps"] == temps and s["still"] and not s["image"]]
        clp = [s for s in p["scenes"] if s["temps"] == temps and s["image"] and s["motion"] and not s["clip"]]
        return {"images": {"n": len(img), "usd": round(0.003 * len(img) + (0 if self.studio.pod() else 0.05), 2)},
                "clips": {"n": len(clp), "usd": round(sum(0.07 if s["end_edit"] else 0.035 for s in clp) + 0.12, 2),
                          "usd_hd": round(sum(0.26 if s["end_edit"] else 0.13 for s in clp) + 0.12, 2)}}

    def produire(self, b):
        pid, quoi = b["id"], b.get("quoi")
        if quoi not in ("images", "clips"):
            raise ValueError("lancement inconnu")
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
            shots = []
            for s in p["scenes"]:
                if (want and s["id"] not in want) or (not want and s["temps"] != int(b.get("temps") or 1)):
                    continue
                c = ch[s["id"]]
                if quoi == "images":
                    if not s["still"] or (not want and c["image"]):
                        continue
                    if c["image"]:  # nouvelle prise demandee : autre tirage
                        s["seed"] = random.randint(1, 999999)
                    s["image"], s["clip"] = "", ""  # la prise retenue sera la nouvelle
                    shots.append({"name": s["id"], "still": s["still"], "seed": s["seed"], "tattoos": s["tattoos"],
                                  "body": bool((perso.get("generation") or {}).get("corps"))}
                                 | ({"loras": _loras_plan(s["loras"])} if s["loras"] else {}))
                else:
                    if not c["image"] or not s["motion"] or (not want and c["clip"]):
                        continue
                    sh = {"name": s["id"], "image": str(d / "media" / c["image"]), "still": s["still"], "motion": s["motion"],
                          "seed": s["seed"] + len(pr.get(s["id"], {}).get("clips", []))}
                    if s["end_edit"]:
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

    # --- Montage ----------------------------------------------------------------------------------
    def monter(self, b):
        pid, t = b["id"], int(b.get("temps") or 1)
        if t not in TEMPS:
            raise ValueError("temps inconnu")
        p = self._eff(self._raw(pid))
        p["scenes"] = [s for s in p["scenes"] if s["temps"] == t]
        if t != 1:  # l'accroche et le carton de fin sont ceux du teaser
            p |= {"accroche": "", "cta": ""}
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
            monter(p, d / "media", tmp, out, self.da, (perso.get("ecriture") or {}).get("plateforme", ""))
            _dump(d / "montage.json", {"etat": "pret", "fichier": out.name})
        except Exception as e:
            _dump(d / "montage.json", {"etat": "erreur", "erreur": str(e)[-400:]})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            self.montages.pop(pid, None)

    def supprimer_final(self, pid, name):
        if not re.fullmatch(r"final_(t[23]_)?v\d+\.mp4", str(name)):
            raise ValueError("fichier invalide")
        (self._pdir(pid) / name).unlink(missing_ok=True)

    def vers_tri(self, pid, name):
        """Copie une video montee dans la boite du Tri (validation humaine avant publication)."""
        if not re.fullmatch(r"final_(t[23]_)?v\d+\.mp4", str(name)):
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
            return {"projet": self.save_projet(b)}
        if path == "/api/a/ecrire":
            return self.ecrire(b)
        if path == "/api/a/produire":
            return self.produire(b)
        if path == "/api/a/monter":
            return self.monter(b)
        if path == "/api/a/depot/importer":
            return self.importer(b)
        if path == "/api/a/final/supprimer":
            self.supprimer_final(b["id"], b["fichier"])
            return {}
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


def _duree(path):
    r = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise RuntimeError(f"durée illisible : {Path(path).name}")


def _texte(tmp, cle, texte, taille, centre, w, h, boite=True):
    """Filtres drawtext d'un texte centre sur la hauteur `centre` (fraction de h), une ligne par filtre."""
    texte = "".join(c for c in str(texte or "") if ord(c) < 0x2190).strip()  # la police n'a pas les emojis
    if not texte:
        return []
    fs = round(h * taille)
    lignes = textwrap.wrap(texte, max(8, int(w * 0.86 / (fs * 0.6)))) or [texte]
    pas = round(fs * 1.45)
    y0 = round(h * centre - pas * len(lignes) / 2)
    out = []
    for i, li in enumerate(lignes):
        f = tmp / f"{cle}_{i}.txt"
        f.write_text(li, encoding="utf-8")
        deco = f":box=1:boxcolor=black@0.45:boxborderw={round(fs * 0.28)}" if boite else f":borderw={max(2, fs // 14)}:bordercolor=black@0.7"
        out.append(f"drawtext=fontfile={FONT}:textfile={f}:fontsize={fs}:fontcolor=white{deco}:x=(w-text_w)/2:y={y0 + i * pas}")
    return out


def monter(p, media, tmp, out, audio_dir, plateforme=""):
    """Assemble les scenes d'un projet : clip retenu (ou image en zoom lent a defaut), texte a l'ecran,
    accroche sur la premiere scene, carton de fin, musique. Ecrit `out`."""
    m = p["montage"]
    w, h = FORMATS[m["format"]]
    fps, x = 32, 0.35
    base = f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}"
    fin = f"fps={fps},setsar=1,format=yuv420p"
    enc = ["-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-video_track_timescale", "16384"]
    label = _texte(tmp, "label", "AI character", 0.016, 0.045, w, h) if m["label"] else []
    segs, durs, derniere = [], [], None
    scenes = [s for s in p["scenes"] if s["clip"] or s["image"]]
    for i, s in enumerate(scenes):
        txt = []
        if m["textes"]:
            if i == 0 and p.get("accroche") and p["accroche"] != s["texte"]:
                txt += _texte(tmp, f"acc{i}", p["accroche"], 0.04, 0.2, w, h)
            txt += _texte(tmp, f"txt{i}", s["texte"], 0.034, 0.72, w, h)
        seg = tmp / f"seg{i}.mp4"
        if s["clip"]:
            src = media / s["clip"]
            total = _duree(src)
            deb = min(s["debut"], max(0, total - 1))
            dur = min(s["duree"] or total, total - deb)
            _ff("-ss", f"{deb:.2f}", "-t", f"{dur:.2f}", "-i", src, "-vf", ",".join([base, fin] + txt + label), *enc, seg)
        else:  # pas encore de clip : image avec un zoom lent
            dur = s["duree"] or 3.0
            nb = round(dur * fps)
            zoom = (f"scale={w * 3 // 2}:{h * 3 // 2}:force_original_aspect_ratio=increase:flags=lanczos,crop={w * 3 // 2}:{h * 3 // 2},"
                    f"zoompan=z='1+0.07*on/{nb}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nb}:s={w}x{h}:fps={fps}")
            _ff("-i", media / s["image"], "-vf", ",".join([zoom, "setsar=1,format=yuv420p"] + txt + label), "-frames:v", nb, *enc, seg)
        segs.append(seg)
        durs.append(_duree(seg))
        derniere = s
    if m["carton"] and p.get("cta"):
        fond = tmp / "fond.png"
        if derniere["image"]:
            shutil.copy(media / derniere["image"], fond)
        else:
            _ff("-i", media / derniere["clip"], "-frames:v", "1", fond)
        txt = _texte(tmp, "cta", p["cta"], 0.044, 0.46, w, h, boite=False) + _texte(tmp, "plat", plateforme, 0.022, 0.56, w, h, boite=False)
        seg = tmp / "carton.mp4"
        _ff("-loop", "1", "-t", "2.6", "-i", fond, "-vf", ",".join([base, "boxblur=28:3,eq=brightness=-0.22:saturation=0.8", fin] + txt + label), *enc, seg)
        segs.append(seg)
        durs.append(_duree(seg))
    muet = tmp / "muet.mp4" if m.get("musique") else out
    if m["transition"] == "fondu" and len(segs) > 1:
        args, fc, acc, prev = [], [], 0.0, "0:v"
        for seg in segs:
            args += ["-i", seg]
        for i in range(1, len(segs)):
            acc += durs[i - 1] - x
            fc.append(f"[{prev}][{i}:v]xfade=transition=fade:duration={x}:offset={acc:.3f}[v{i}]")
            prev = f"v{i}"
        _ff(*args, "-filter_complex", ";".join(fc), "-map", f"[{prev}]", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", muet)
        total = sum(durs) - x * (len(segs) - 1)
    else:
        liste = tmp / "liste.txt"
        liste.write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
        _ff("-f", "concat", "-safe", "0", "-i", liste, "-c", "copy", "-movflags", "+faststart", muet)
        total = sum(durs)
    if m.get("musique"):
        src = (audio_dir / m["musique"]).resolve()
        if src.parent != audio_dir.resolve() or not src.is_file():
            raise RuntimeError("musique introuvable dans data/audio")
        _ff("-i", muet, "-stream_loop", "-1", "-i", src, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
            "-af", f"afade=t=in:d=0.4,afade=t=out:st={max(0, total - 1.2):.2f}:d=1.2", "-t", f"{total:.2f}", "-movflags", "+faststart", out)
