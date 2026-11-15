"""Atelier du personnage : sa bibliotheque d'images. Une image par lieu (la piece vide) et par tenue (a plat sur fond
blanc), creees d'apres les lignes de sa fiche ; ses planches (photos d'elle, pour entrainer sa LoRA) ; ses LoRA
entrainees et leurs essais. Les lignes restent dans la fiche ("lieux", "tenues") : ici il n'y a que les images et les
choix. Tout est range dans data/personnages/<slug>/ ; le nom d'un fichier dit ce qu'il est :
l_<cle>_<tirage>.png lieu, t_<cle>_<tirage>.png tenue, v_<tirage>.png portrait, c_<serie>_<rang>.png planche,
e_<version>_<force>_<rang>.png essai d'une LoRA. Les calculs passent par le pilote (server/pilot/perso.py)."""
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
FIN = ", smartphone photo, natural skin texture"
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
ESSAIS = ("medium shot, eye-level, front view, she stands, soft smile, looking at the camera, in a bright living room, wearing a white t-shirt and jeans",
          "full-body shot, eye-level, three-quarter view, she stands, one hand on her hip, on a city street, wearing a black dress")
FORCES = (1.0, 1.3, 1.6)


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
        if f.parent == d.resolve() and f.is_file() and f.suffix == ".png":
            return f
        raise FileNotFoundError(name)

    def image(self, slug, quoi, ligne):
        """Image choisie d'un lieu ("l") ou d'une tenue ("t") de la fiche, ou None : c'est ce que lit la Production."""
        try:
            nom = self._b(slug)["choix"].get(f"{quoi}_{h8(ligne)}")
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
        return {"etat": etat, "faites": t.count(" : image ("), "echecs": t.count("ECHEC"), "cout": float(m.group(1)) if m else None,
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
                            "choix": ch if ch in imgs else "", "genre": b["genres"].get(h, "tenue")} if q == "t" else
                           {"cle": h, "fr": _s(x.partition("|")[0]) if "|" in x else "", "en": _s(x.rpartition("|")[2]), "images": imgs, "choix": ch if ch in imgs else ""})
            return out
        g = p.get("generation") or {}
        vis = [n for n in noms if n.startswith("v_")]
        j = self.job if self.job and self.job["slug"] == slug else None
        return {"slug": slug, "nom": p["nom"], "lora": bool(g.get("lora")), "lora_force": g.get("lora_strength"), "prefixe": bool(g.get("zimage_prefix")),
                "lieux": lignes("lieux", "l"), "tenues": lignes("tenues", "t"),
                "visage": {"images": vis, "choix": b["choix"].get("visage") if b["choix"].get("visage") in vis else ""},
                "planches": [{"nom": n, "garde": bool(b["planches"].get(n, {}).get("garde")), "legende": b["planches"].get(n, {}).get("legende", "")}
                             for n in noms if n.startswith("c_")],
                "loras": [{k: lo.get(k) for k in ("nom", "etat", "date", "passages", "images", "cout")} | {"en_place": bool(lo.get("fichier")) and lo.get("fichier") == g.get("lora"),
                           "essais": [n for n in noms if n.startswith(f"e_{lo['v']}_")]} for lo in b["loras"]],
                "job": ({"quoi": j["quoi"], "n": j["n"]} | self._etat(j["log"], self._ici(j["log"]))) if j else None,
                "occupe": self.at.studio.running(), "pod": bool(self.at.studio.pod()), "forces": FORCES}

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
        for f in d.glob(f"{q}_{re.sub(r'[^0-9a-f]', '', str(b.get('cle')))}_*.png"):
            shutil.move(str(f), str(d / "retire" / f.name))
        return self.vue(slug)

    def choix(self, b):
        slug, bb = b["slug"], self._b(b["slug"])
        nom = self.fichier(slug, str(b["image"])).name
        m = re.fullmatch(r"([lt])_([0-9a-f]{8})_\d+\.png", nom)
        if m:
            bb["choix"][f"{m.group(1)}_{m.group(2)}"] = nom
        elif nom.startswith("v_"):
            bb["choix"]["visage"] = nom
        else:
            raise ValueError("image sans choix possible")
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
        log = d / "lots" / f"{nom}.log"
        cmd = [sys.executable, "-m", "pilot", "perso" if veille else "entrainer", str(d / "lots" / f"{nom}.json")]
        if veille:  # pod de veille du studio, partage avec la Production et la page Essais
            cmd += ["--pod-id", os.environ.get("STUDIO_POD_ID") or self.at.studio.ensure_pod()]
        self.at.studio.proc = subprocess.Popen(cmd, cwd=str(self.at.repo / "server"), stdout=open(log, "w"), stderr=subprocess.STDOUT)
        self.job = {"slug": slug, "quoi": quoi, "log": str(log), "n": n}
        return log

    def _prefixe(self, p):
        g = p.get("generation") or {}
        return (g.get("zimage_prefix") or f"a {p.get('age', 25)} year old woman, ") + ((g["corps"].rstrip(", ") + ", ") if g.get("corps") else "")

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
            deja = {int(i.rsplit("_", 1)[1][:-4]) for i in x["images"]}
            for s in [s for s in range(1, 60) if s not in deja][:n]:
                if q == "l":
                    pr = f"vertical wide shot, eye-level, photo of an empty deserted place, {_sans_elle(x['en'])}, natural light, smartphone photo"
                else:
                    pr = f"product photo, flat lay on a plain white background, {re.sub(r'^wearing ', '', x['en'])} laid flat, nothing else, no person, no mannequin"
                taches.append({"sortie": f"{q}_{x['cle']}_{s}", "prompt": pr, "seed": 7 * s + int(x["cle"][:4], 16), "taille": [720, 1280], "lora": False})
        self._lancer(slug, k, {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def visage(self, b):
        """Personnage sans LoRA : quatre portraits d'apres sa description, le proprietaire en choisit un ; les planches en seront tirees."""
        slug = b["slug"]
        self._libre()
        p = self.at.perso(slug)
        deja = {int(f.stem.split("_")[1]) for f in self.dir(slug).glob("v_*.png")} if self.dir(slug).is_dir() else set()
        taches = [{"sortie": f"v_{s}", "seed": 1000 + 37 * s, "taille": [720, 1280], "lora": False,
                   "prompt": f"{self._prefixe(p)}vertical medium close-up portrait, eye-level, front view, she looks at the camera, soft smile, "
                             f"in front of a plain light grey wall, wearing a white t-shirt, soft natural daylight{FIN}"}
                  for s in [s for s in range(1, 60) if s not in deja][:4]]
        self._lancer(slug, "visage", {"taches": taches}, len(taches))
        return {"lance": len(taches)}

    def planches(self, b):
        """Serie de planches : photos d'elle, cadrages et fonds varies. "tenue" vide : les tenues de sa fiche a tour de role ;
        sinon le texte du proprietaire (anglais), tel quel, pour toute la serie. "loras" : LoRA en plus, choisies par lui.
        Avec la LoRA du personnage si elle existe ; sinon par retouche du portrait choisi."""
        slug = b["slug"]
        self._libre()
        p, v, bb = self.at.perso(slug), self.vue(slug), self._b(slug)
        n = max(4, min(int(b.get("n") or 24), 40))
        tenue = _s(b.get("tenue"), 400)
        ref = None
        if not v["lora"]:
            if not v["visage"]["choix"]:
                raise ValueError("choisir d'abord un portrait : les planches en sont tirées")
            ref = str(self.fichier(slug, v["visage"]["choix"]))
        tenues = [x["en"] for x in v["tenues"] if x["genre"] != "dessous"] or ["a white t-shirt and jeans"]
        serie = bb["series"] = int(bb.get("series") or 0) + 1
        pre, taches = self._prefixe(p), []
        for i in range(n):
            cadre, fond = CADRES[(i * 7 + serie) % len(CADRES)], FONDS[(i + serie) % len(FONDS)]
            if "bed" in cadre:
                fond = FONDS[1]
            habit = tenue or "wearing " + re.sub(r"^wearing ", "", tenues[(i + serie) % len(tenues)])
            desc = f"{cadre}, {fond}, {habit}" + (", nsfw" if b.get("nsfw") else "")
            nom = f"c_{serie}_{i + 1:02d}"
            bb["planches"][nom + ".png"] = {"garde": False, "legende": f"{pre}{desc}"}
            t = {"sortie": nom, "seed": 5000 + 101 * serie + i, "taille": [720, 1280]}
            if ref:
                t |= {"ref": ref, "prompt": f"Same woman, same face, same hair. New photo of her: {desc}. Natural smartphone photo."}
            else:
                t |= {"lora": True, "loras": [str(x) for x in b.get("loras") or []][:4], "prompt": f"{pre}vertical {desc}{FIN}"}
            taches.append(t)
        self._ecrire(slug, bb)
        self._lancer(slug, "planches", {"taches": taches}, n)
        return {"lance": n}

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
             "/api/a/b/visage": self.visage, "/api/a/b/planches": self.planches, "/api/a/b/garde": self.garde, "/api/a/b/entrainer": self.entrainer,
             "/api/a/b/adopter": self.adopter, "/api/a/b/revenir": self.revenir}.get(path)
        if not f:
            return None
        with self.at.lock:
            return f(b)
