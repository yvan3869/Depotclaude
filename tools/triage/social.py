"""Espace reseaux : selfies tous publics qui font vivre les comptes grand public des personnages.

Un lot = une semaine d'un personnage. Le redacteur ecrit les publications (moment, description de la photo, legende,
hashtags), puis les images sont calculees sur le pod de veille du studio, quand rien d'autre ne tourne et tant que
le plafond du jour le permet. Chaque publication attend ensuite dans la file : rien ne part sans validation, et la
publication elle-meme se fait a la main (texte a copier, image a telecharger).

Tous publics strict : une description de photo qui sort de ce cadre est refusee, y compris a la main.
"""
import datetime
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from atelier import JOURS, MOIS, REPERES, _dump, _ff, _json_de, _load, _loras_plan, _s

FORMATS = {"4:5": [832, 1040], "9:16": [720, 1280], "1:1": [1024, 1024]}
DEFAUT = {"auto": False, "nb": 7, "jour": 5, "mention": "AI-generated character", "format": "4:5"}
MAX_NB = 14        # publications par semaine et par personnage
COUT_IMAGE = 0.02  # constate sur le pod de veille
COUT_POD = 0.05    # demarrage du pod quand il n'est pas deja la

_HORS_CADRE = re.compile(r"\b(nsfw|nud(e|ity)|naked|topless|bottomless|lingerie|underwear|pant(y|ies)|thong|g-string|bra|bralette|braless|"
                         r"see-through|sheer|cleavage|nipples?|areola\w*|undress\w*|stripp(ed|ing)|striptease|sex\w*|erotic\w*|porn\w*|"
                         r"seductive\w*|bare (breasts?|chest|butt|ass))\b", re.I)

SYSTEME = """Tu écris les publications tous publics d'un personnage fictif, adulte, généré par IA, pour ses comptes de réseaux sociaux grand public.
Ces publications font vivre le compte : des selfies du quotidien, comme en poste une vraie personne. Elles ne vendent rien.

Règles :
- Une publication = une photo qu'elle prend elle-même au téléphone (selfie à bout de bras, ou dans un miroir) et sa légende.
- Tous publics strict : elle est entièrement habillée, en tenue de tous les jours adaptée au lieu et à la saison. Rien de suggestif, pas de sous-vêtements, pas de nudité, pas de pose aguicheuse.
- Aucune mention ni allusion à un contenu payant, à un lien, à une autre plateforme, à des messages privés. Aucun appel à l'action commercial.
- Ne nommer aucun réseau social : les textes servent sur plusieurs.
- Varier d'un jour à l'autre le lieu, le moment de la journée, la tenue, le cadrage et l'humeur. Tenir compte de la saison, du jour de la semaine et des repères du calendrier. Rester cohérent avec la fiche (lieux, univers, ton) et ne pas répéter ce qui est déjà prévu ou publié.
- "moment" : 3 à 8 mots en français, pour le propriétaire.
- "still" : description de la photo en anglais, 25 à 55 mots, concrète, au présent, sans nom propre. Dire le cadrage ("selfie at arm's length" ou "mirror selfie, holding her phone"), le lieu, la tenue complète et précise, l'expression, la lumière. Ne décrire ni son visage ni son corps (ils sont déjà fixés). Une seule personne, aucun texte dans l'image. Hors miroir, le téléphone n'apparaît pas dans l'image.
- "legende" : dans la langue des publications de la fiche, à la première personne, dans son ton, une ou deux phrases courtes et naturelles. Pas d'emoji, sauf si le ton de la fiche en demande. Ne pas écrire qu'elle est une IA : la mention est ajoutée à part.
- "hashtags" : 3 à 6, en minuscules, liés au moment, sans mot-clé pour adultes.

Réponds par le seul JSON, sans commentaire :
{"posts": [{"moment": "...", "still": "...", "legende": "...", "hashtags": "#... #..."}]}
Une entrée par jour demandé, dans l'ordre."""

# Publications types quand le redacteur ne repond pas : (moment, photo, legende en anglais, legende en francais, hashtags)
SECOURS = (
    ("Café du matin", "selfie at arm's length at a small cafe table by the window, wearing a cream knit sweater and blue jeans, holding a cup of coffee "
     "in her other hand, soft smile, morning daylight", "Slow morning, strong coffee.", "Matin tranquille, café serré.", "#coffee #morning #slowliving"),
    ("Promenade au parc", "selfie at arm's length on a park path lined with trees, wearing a beige trench coat over a white t-shirt and jeans, hair moved "
     "by a light breeze, relaxed smile, overcast daylight", "Needed some air today.", "Besoin de prendre l'air aujourd'hui.", "#walk #park #freshair"),
    ("Miroir avant de sortir", "mirror selfie in a bright hallway, holding her phone in one hand, wearing a black turtleneck, a long camel coat and dark "
     "jeans, small shoulder bag, calm confident look, soft indoor light", "Ready. Almost on time.", "Prête. Presque à l'heure.", "#ootd #mirrorselfie #cityday"),
    ("Cuisine du soir", "selfie at arm's length in a home kitchen, wearing an oversized grey hoodie and leggings, wooden spoon in her other hand, a pot on "
     "the stove behind her, amused look, warm evening light", "Tonight I cook. Wish me luck.", "Ce soir je cuisine. Souhaitez-moi bonne chance.", "#homecooking #dinner #cozy"),
    ("Lecture sur le canapé", "selfie at arm's length curled up on a sofa under a blanket, wearing a thick wool cardigan over a t-shirt, open book on her "
     "knees, cosy smile, lamp light in the evening", "Book, blanket, nothing else planned.", "Un livre, un plaid, rien d'autre de prévu.", "#reading #cozyevening #books"),
    ("Tour au marché", "selfie at arm's length at an outdoor market, wearing a denim jacket over a striped top, stalls of fruit and vegetables behind her, "
     "tote bag on her shoulder, bright smile, morning sun", "Market run. I bought too much again.", "Tour au marché. J'en ai encore trop pris.", "#market #weekend #fresh"),
    ("Après la séance de sport", "mirror selfie at the gym, holding her phone, wearing a loose t-shirt, long leggings and sneakers, hair tied in a ponytail, "
     "towel over her shoulder, tired happy face, neutral indoor light", "Done. Legs are filing a complaint.", "Séance faite. Mes jambes portent plainte.", "#workout #gym #done"),
    ("Journée de travail", "selfie at arm's length at a desk with a laptop and a notebook, wearing a white shirt and a navy blazer, headphones around her "
     "neck, focused half smile, daylight from a side window", "Busy day, good playlist.", "Grosse journée, bonne playlist.", "#workday #desk #focus"),
    ("Coucher de soleil au balcon", "selfie at arm's length on a balcony at sunset, wearing a chunky knit sweater, city rooftops behind her, cup of tea in "
     "her other hand, peaceful look, warm golden light", "This light, every time.", "Cette lumière, à chaque fois.", "#sunset #goldenhour #balcony"),
    ("Sous la pluie en ville", "selfie at arm's length in a city street under an umbrella, wearing a dark raincoat and a scarf, wet pavement and shop lights "
     "behind her, playful grin, grey rainy light", "Rain again. I'm fine with it.", "Encore la pluie. Ça me va.", "#rainyday #city #umbrella"),
)


def public(still):
    """Leve une erreur si la description de photo sort du cadre tous publics."""
    m = _HORS_CADRE.search(still or "")
    if m:
        raise ValueError(f"cet espace est tous publics : « {m.group(0)} » n'y a pas sa place. Le reste se fait dans l'atelier.")


def _lundi(d):
    return d - datetime.timedelta(days=d.weekday())


def _tags(x):
    mots = [re.sub(r"[^\w]", "", m, flags=re.U) for m in re.split(r"[\s,]+", str(x or ""))]
    return " ".join("#" + m for m in mots if m)[:200]


class Social:
    def __init__(self, data: Path, repo: Path, studio, atelier):
        self.repo, self.studio, self.at = repo, studio, atelier
        self.d = data / "social"
        self.media, self.runs = self.d / "media", self.d / "runs"
        for x in (self.media, self.runs):
            x.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.attente = ""   # pourquoi les images en attente ne partent pas
        self.pause = 0      # pas de nouveau lancement avant cette heure (apres un echec de lancement)
        self.run = None     # {"nom", "ids", "proc", "log"} : calcul d'images en cours
        r = _load(self.d / "run.json")
        if r:  # interface redemarree pendant un calcul : le pilote est mort avec elle, on garde ce qui est sorti
            self.run = {**r, "proc": None}
            self._recolter()
        self.ev = threading.Event()
        threading.Thread(target=self._fond, daemon=True).start()

    # --- Donnees ----------------------------------------------------------------------------------
    def _posts(self):
        return _load(self.d / "posts.json") or {"n": 0, "runs": 0, "posts": []}

    def _lots(self):
        return _load(self.d / "lots.json") or {"n": 0, "lots": []}

    def reglages(self, slug):
        r = {**DEFAUT, **((_load(self.d / "reglages.json") or {}).get(slug) or {})}
        return r

    def _post(self, P, kid):
        for k in P["posts"]:
            if k["id"] == kid:
                return k
        raise ValueError("publication inconnue")

    def fichier(self, nom):
        if not re.fullmatch(r"soc\d{4}_k\d{4}\.(png|jpg)", nom):
            raise ValueError("nom invalide")
        f = self.media / nom
        if not f.is_file():
            raise FileNotFoundError(nom)
        return f

    def estimation(self, n):
        return round(COUT_POD + COUT_IMAGE * n, 2)

    def etat(self):
        auj = datetime.date.today()
        dep = [x for x in (self._lignes(self.d / "depenses.jsonl")) if x.get("jour", "") >= (auj - datetime.timedelta(days=6)).isoformat()]
        P, vieux = self._posts(), (auj - datetime.timedelta(days=60)).isoformat()
        return {"personnages": [{"slug": p["slug"], "nom": p["nom"], "langue": p.get("langue"), "lora": bool((p.get("generation") or {}).get("lora")),
                                 "reglages": self.reglages(p["slug"])} for p in self.at.persos().values() if p.get("statut") != "archive"],
                "posts": sorted((k for k in P["posts"] if not (k["etat"] in ("publie", "refuse") and k["jour"] < vieux)), key=lambda k: (k["jour"], k["id"])),
                "lots": self._lots()["lots"][-6:][::-1], "redacteur": self.at.redacteur_actif(), "depense": self.at.depense(),
                "occupe": self.studio.running(), "can_run": self.studio.can_run(), "calcul": bool(self.run), "attente": self.attente,
                "formats": list(FORMATS), "jours": list(JOURS), "max_nb": MAX_NB, "cout_image": COUT_IMAGE, "cout_pod": COUT_POD,
                "semaines": {"courante": _lundi(auj).isoformat(), "suivante": (_lundi(auj) + datetime.timedelta(days=7)).isoformat()},
                "depense_7j": round(sum(float(x.get("usd") or 0) for x in dep), 2)}

    @staticmethod
    def _lignes(f):
        out = []
        for l in f.read_text(encoding="utf-8").splitlines() if f.exists() else []:
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
        return out

    # --- Reglages et lots -------------------------------------------------------------------------
    def regler(self, b):
        p = self.at.perso(b.get("perso"))
        with self.lock:
            tous = _load(self.d / "reglages.json") or {}
            r = self.reglages(p["slug"])
            r["auto"] = bool(b.get("auto"))
            r["nb"] = max(1, min(MAX_NB, int(b.get("nb") or r["nb"])))
            r["jour"] = max(0, min(6, int(b.get("jour") if b.get("jour") not in (None, "") else r["jour"])))
            r["mention"] = _s(b.get("mention"), 80) or DEFAUT["mention"]
            r["format"] = b.get("format") if b.get("format") in FORMATS else r["format"]
            tous[p["slug"]] = r
            _dump(self.d / "reglages.json", tous)
        self.ev.set()
        return self.etat()

    def lot(self, b, auto=False):
        """Prepare une semaine de publications d'un personnage : demande au redacteur, images ensuite."""
        p = self.at.perso(b.get("perso"))
        if p.get("statut") == "archive":
            raise ValueError("personnage archivé")
        r = self.reglages(p["slug"])
        nb = max(1, min(MAX_NB, int(b.get("nb") or r["nb"])))
        auj = datetime.date.today()
        lundi = _lundi(auj) + datetime.timedelta(days=0 if b.get("semaine") == "courante" else 7)
        reste = 7 - auj.weekday() if b.get("semaine") == "courante" else 7  # semaine en cours : les jours qui restent seulement
        nb = min(nb, 2 * reste)
        jours = [(lundi + datetime.timedelta(days=7 - reste + int(i * reste / nb) % reste)).isoformat() for i in range(nb)]
        with self.lock:
            L = self._lots()
            if any(x["etat"] == "texte" and x["perso"] == p["slug"] for x in L["lots"]):
                raise ValueError("un lot de ce personnage est déjà en cours d'écriture")
            L["n"] += 1
            lot = {"id": f"l{L['n']:04d}", "perso": p["slug"], "semaine": lundi.isoformat(), "jours": jours, "etat": "texte", "auto": auto,
                   "cree": time.strftime("%Y-%m-%d %H:%M"), "moteur": "ia", "rid": "", "erreur": ""}
            if self.at.redacteur_actif():
                lot["rid"] = f"{time.strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"
                req = self.at.de / f"{lot['rid']}.req.json"
                _dump(req, {"systeme": SYSTEME, "demande": self._demande(p, lundi, jours), "kind": "social", "projet": "", "scene": ""})
                os.chmod(req, 0o666)
            else:
                self._creer(lot, [])
            L["lots"].append(lot)
            _dump(self.d / "lots.json", L)
        self.ev.set()
        return self.etat()

    def _demande(self, p, lundi, jours):
        f = p.get("fiche") or {}
        fiche = {"nom": p["nom"], "age": p["age"], "langue_des_publications": p.get("langue"), "phrase": p.get("accroche"),
                 **{k: f.get(k) for k in ("identite", "voix", "personnalite", "univers")}, "lieux (français | anglais)": p.get("lieux"),
                 "ton": (p.get("ecriture") or {}).get("ton"), "interdits": (p.get("ecriture") or {}).get("interdits")}
        dim = lundi + datetime.timedelta(days=6)
        rep = [f"{j} {MOIS[m - 1]} : {nom}" for (m, j), nom in REPERES
               if lundi <= datetime.date(lundi.year if m >= lundi.month else dim.year, m, j) <= dim]
        deja = [f"- {k['jour']} : {k['moment']}" for k in self._posts()["posts"] if k["perso"] == p["slug"] and k["etat"] != "refuse"][-30:]

        def dit(iso):
            d = datetime.date.fromisoformat(iso)
            return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]} {d.year}"
        return ("FICHE DU PERSONNAGE\n" + json.dumps(fiche, ensure_ascii=False, indent=1)
                + f"\n\nSEMAINE du {dit(lundi.isoformat())} au {dit(dim.isoformat())}."
                + (" Repères du calendrier : " + " ; ".join(rep) + "." if rep else "")
                + ("\n\nDÉJÀ PRÉVU OU PUBLIÉ (ne pas répéter)\n" + "\n".join(deja) if deja else "")
                + f"\n\nDEMANDE\n{len(jours)} publication(s), une par jour dans cet ordre : " + ", ".join(dit(j) for j in jours) + ".")

    def _creer(self, lot, ecrits):
        """Cree les publications d'un lot a partir de ce qu'a ecrit le redacteur ; une publication type remplace une entree
        manquante ou hors cadre."""
        fr = str(self.at.perso(lot["perso"]).get("langue") or "").lower().startswith("fr")
        types, secours = random.sample(SECOURS, len(SECOURS)), 0
        P = self._posts()
        for i, jour in enumerate(lot["jours"]):
            e = ecrits[i] if i < len(ecrits) and isinstance(ecrits[i], dict) else {}
            still, legende = _s(e.get("still"), 700), _s(e.get("legende"), 600)
            if not still or not legende or _HORS_CADRE.search(still):
                t = types[i % len(types)]
                e, still, legende, secours = {"moment": t[0], "hashtags": t[4]}, t[1], t[3] if fr else t[2], secours + 1
            P["n"] += 1
            P["posts"].append({"id": f"k{P['n']:04d}", "lot": lot["id"], "perso": lot["perso"], "jour": jour, "moment": _s(e.get("moment"), 120),
                               "still": still, "legende": legende, "hashtags": _tags(e.get("hashtags")), "seed": random.randint(1, 999999),
                               "image": "", "prises": [], "etat": "attente_image", "erreur": ""})
        _dump(self.d / "posts.json", P)
        lot["etat"], lot["moteur"] = "fini", "secours" if secours == len(lot["jours"]) else "ia"
        lot["secours"] = secours

    def _textes(self):
        """Releve les reponses du redacteur."""
        with self.lock:
            L = self._lots()
            for lot in [x for x in L["lots"] if x["etat"] == "texte"]:
                req, res, err = (self.at.de / f"{lot['rid']}.{x}" for x in ("req.json", "res.txt", "err.txt"))
                try:
                    if err.exists():
                        lot["etat"], lot["erreur"] = "echec", "rédacteur : " + err.read_text(encoding="utf-8", errors="replace")[:300]
                    elif res.exists():
                        self._creer(lot, _json_de(res.read_text(encoding="utf-8")).get("posts") or [])
                    elif not req.exists() or time.time() - req.stat().st_mtime > (60 if not self.at.redacteur_actif() else 900):
                        self._creer(lot, [])  # redacteur arrete ou muet : publications types
                    else:
                        continue
                except (ValueError, KeyError, TypeError, AttributeError) as e:
                    lot["etat"], lot["erreur"] = "echec", str(e)[:300]
                for f in (req, res, err):
                    f.unlink(missing_ok=True)
                _dump(self.d / "lots.json", L)

    def _auto(self):
        """Personnages en automatique : la semaine suivante se prepare a partir du jour choisi."""
        auj = datetime.date.today()
        suiv = (_lundi(auj) + datetime.timedelta(days=7)).isoformat()
        lots = self._lots()["lots"]
        for p in self.at.persos().values():
            r = self.reglages(p["slug"])
            if r["auto"] and p.get("statut") != "archive" and auj.weekday() >= r["jour"] \
                    and not any(x["perso"] == p["slug"] and x["semaine"] == suiv for x in lots):
                self.lot({"perso": p["slug"]}, auto=True)

    # --- Images -----------------------------------------------------------------------------------
    def _lancer(self):
        with self.lock:
            P = self._posts()
            att = [k for k in P["posts"] if k["etat"] == "attente_image"]
            if not att:
                self.attente = ""
                return
            if self.run or time.time() < self.pause:
                return
            att = [k for k in att if k["perso"] == att[0]["perso"]][:MAX_NB]  # un calcul = un personnage
            st, at = self.studio, self.at
            if st.running() or at.chaine_active():
                self.attente = "un autre calcul est en cours : les images partiront à sa fin"
                return
            if not st.can_run():
                self.attente = "clé RunPod absente : les images ne peuvent pas être calculées"
                return
            dep, est = at.depense(), self.estimation(len(att))
            if not dep:
                self.attente = "dépense du jour illisible : pas de lancement"
                return
            if dep["jour"] + est > dep["plafond"]:
                self.attente = f"plafond du jour : {dep['jour']:.2f} $ dépensés sur {dep['plafond']:.2f} $, il faut environ {est:.2f} $. Les images partiront demain."
                return
            try:
                perso = at.perso(att[0]["perso"])
                r = self.reglages(perso["slug"])
                loras = at._defauts().get(1) or ""
                with at.lock:
                    if st.running():
                        return
                    P["runs"] = P.get("runs", 0) + 1
                    nom = f"soc{P['runs']:04d}"
                    job = {"name": nom, "character": at.char_override(perso),
                           "defaults": {"still_size": FORMATS[r["format"]], "mode": "natural", "smooth": True, "grain": True, "same_seed": True, "loras": []},
                           "shots": [{"name": k["id"], "still": k["still"], "seed": k["seed"], "tattoos": True, "body": False}
                                     | ({"loras": _loras_plan(loras)} if loras else {}) for k in att]}
                    _dump(self.runs / f"{nom}.json", job)
                    cmd = [sys.executable, "-m", "pilot", "run", str(self.runs / f"{nom}.json"), "--data", str(self.d.parent), "--out", str(self.media),
                           "--stills-only", "--pod-id", os.environ.get("STUDIO_POD_ID") or st.ensure_pod()]
                    log = self.runs / f"{nom}.log"
                    st.proc = subprocess.Popen(cmd, cwd=str(self.repo / "server"), stdout=open(log, "w"), stderr=subprocess.STDOUT)
            except Exception as e:  # pod refuse (plafond, quota) : on n'insiste pas tout de suite
                self.attente, self.pause = f"lancement impossible : {str(e)[:200]}", time.time() + 600
                _dump(self.d / "posts.json", P)
                return
            for k in att:
                k["etat"], k["erreur"] = "calcul", ""
            _dump(self.d / "posts.json", P)
            self.run = {"nom": nom, "ids": [k["id"] for k in att], "proc": st.proc, "log": str(log)}
            _dump(self.d / "run.json", {k: self.run[k] for k in ("nom", "ids", "log")})
            self.attente = ""

    def _recolter(self):
        with self.lock:
            run = self.run
            if not run or (run["proc"] is not None and run["proc"].poll() is None):
                return
            try:
                journal = Path(run["log"]).read_text(encoding="utf-8", errors="replace")
            except OSError:
                journal = ""
            echecs = [l.strip() for l in journal.splitlines() if "ECHEC" in l or "ARRET" in l or "Error" in l]
            motif = (echecs[-1][-200:] if echecs else "image non produite") if run["proc"] is not None else "interface redémarrée pendant le calcul"
            P, faits = self._posts(), 0
            for kid in run["ids"]:
                try:
                    k = self._post(P, kid)
                except ValueError:
                    continue
                f = self.media / f"{run['nom']}_{kid}.png"
                if f.is_file():
                    try:
                        _ff("-i", f, "-vf", "scale=480:-2", "-q:v", "4", f.with_suffix(".jpg"))
                    except (RuntimeError, OSError):
                        pass
                    k["image"], k["etat"], k["erreur"], faits = f.name, "a_valider", "", faits + 1
                    k["prises"].append(f.name)
                elif k["image"]:  # nouvelle prise ratee : l'ancienne reste
                    k["etat"], k["erreur"] = "a_valider", "nouvelle image non produite : " + motif
                else:
                    k["etat"], k["erreur"] = "echec", motif
            _dump(self.d / "posts.json", P)
            # sur le pod de veille le pilote ne donne que la duree : cout = duree x tarif du pod (la veille qui suit n'y est pas)
            m, mn, tarif = re.findall(r'"cost_usd": ([\d.]+)', journal), re.findall(r'"minutes": ([\d.]+)', journal), (self.studio.pod() or {}).get("cost")
            with open(self.d / "depenses.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"jour": datetime.date.today().isoformat(), "run": run["nom"], "images": faits, "demandees": len(run["ids"]),
                                    "usd": float(m[-1]) if m else round(float(mn[-1]) / 60 * tarif, 2) if mn and tarif else None}) + "\n")
            (self.d / "run.json").unlink(missing_ok=True)
            self.run = None

    def _fond(self):
        while True:
            self.ev.wait(15)
            self.ev.clear()
            for f in (self._textes, self._recolter, self._auto, self._lancer):
                try:
                    f()
                except Exception as e:  # le fil de fond ne doit jamais mourir
                    self.attente = f"erreur : {str(e)[:200]}"

    # --- File a valider ---------------------------------------------------------------------------
    def modifier(self, b):
        with self.lock:
            P = self._posts()
            k = self._post(P, b.get("id"))
            if "still" in b and _s(b["still"], 700) != k["still"]:
                if k["etat"] == "calcul":
                    raise ValueError("image en cours de calcul : attendre sa fin")
                still = _s(b["still"], 700)
                if not still:
                    raise ValueError("description de la photo obligatoire")
                public(still)
                k["still"] = still
            if "jour" in b:
                k["jour"] = datetime.date.fromisoformat(str(b["jour"])).isoformat()
            for c, n in (("moment", 120), ("legende", 600)):
                if c in b:
                    k[c] = _s(b[c], n)
            if "hashtags" in b:
                k["hashtags"] = _tags(b["hashtags"])
            _dump(self.d / "posts.json", P)
        return self.etat()

    def decider(self, b):
        e = b.get("etat")
        if e not in ("a_valider", "valide", "refuse", "publie"):
            raise ValueError("décision inconnue")
        with self.lock:
            P = self._posts()
            k = self._post(P, b.get("id"))
            if k["etat"] == "calcul":
                raise ValueError("image en cours de calcul : attendre sa fin")
            if e != "refuse" and not k["image"]:
                raise ValueError("pas encore d'image : rien à valider")
            if e == "publie" and k["etat"] != "valide":
                raise ValueError("une publication se valide avant d'être marquée publiée")
            k["etat"] = e
            if e == "publie":
                k["publie_le"] = datetime.date.today().isoformat()
            _dump(self.d / "posts.json", P)
        return self.etat()

    def refaire(self, b):
        with self.lock:
            P = self._posts()
            k = self._post(P, b.get("id"))
            if k["etat"] in ("calcul", "attente_image"):
                raise ValueError("une image est déjà demandée pour cette publication")
            if k["etat"] == "publie":
                raise ValueError("publication déjà publiée")
            public(k["still"])
            k["seed"], k["etat"], k["erreur"] = random.randint(1, 999999), "attente_image", ""
            _dump(self.d / "posts.json", P)
            self.pause = 0
        self.ev.set()
        return self.etat()

    def supprimer(self, b):
        with self.lock:
            P = self._posts()
            k = self._post(P, b.get("id"))
            if k["etat"] == "calcul":
                raise ValueError("image en cours de calcul : attendre sa fin")
            for n in k["prises"]:
                for f in (self.media / n, (self.media / n).with_suffix(".jpg")):
                    f.unlink(missing_ok=True)
            P["posts"].remove(k)
            _dump(self.d / "posts.json", P)
        return self.etat()

    def annuler(self, b):
        """Arrete ce qui est en route : lots en ecriture, images en attente, calcul en cours."""
        with self.lock:
            L = self._lots()
            for lot in L["lots"]:
                if lot["etat"] == "texte":
                    lot["etat"], lot["erreur"] = "echec", "annulé"
                    for f in self.at.de.glob(f"{lot['rid']}.*"):
                        f.unlink(missing_ok=True)
            _dump(self.d / "lots.json", L)
            P = self._posts()
            for k in P["posts"]:
                if k["etat"] == "attente_image":
                    k["etat"], k["erreur"] = ("a_valider", "") if k["image"] else ("echec", "annulé")
            _dump(self.d / "posts.json", P)
            if self.run and self.run["proc"] is not None and self.run["proc"].poll() is None:
                self.run["proc"].terminate()
        self.ev.set()
        return self.etat()

    def get(self, path, q):
        return self.etat() if path == "/api/s/etat" else None

    def post(self, path, b):
        f = {"/api/s/reglages": self.regler, "/api/s/lot": self.lot, "/api/s/post": self.modifier, "/api/s/decider": self.decider,
             "/api/s/refaire": self.refaire, "/api/s/supprimer": self.supprimer, "/api/s/annuler": self.annuler}.get(path)
        return f(b) if f else None
