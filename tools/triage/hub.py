"""Hub des modeles et des LoRA : catalogue Civitai et Hugging Face par modele de base et par categorie, LoRA retenues,
chargement sur le volume, veille des modeles.

Le serveur ne telecharge aucune image : les vignettes sont des adresses que charge le navigateur du proprietaire.
Une LoRA n'est retenue qu'a partir de sa fiche relue chez la source (jamais d'une adresse fournie par la page), et
n'est chargee que sur clic : un lot = un pod, annonce et consigne comme toute depense.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

from categories import CATS, FAMILLES, temps_min

UA = "girls-ai-hub/1.0"
MAX_MO = 1500   # taille d'un fichier : il transite par la memoire du serveur
MAX_LOT = 6     # LoRA par lot
# Recherche par defaut de chaque categorie (le champ de recherche de la page la remplace)
REQ = {"realisme": "realism", "smartphone": "amateur photo", "peau": "skin detail", "lumiere": "lighting", "pose": "selfie",
       "mouvement": "motion", "vitesse": "lightning", "tenue": "lingerie", "corps": "body", "nu": "nude", "porno": "nsfw", "autre": ""}
LIBRES = ("apache-2.0", "mit", "openrail", "openrail++", "creativeml-openrail-m", "cc-by-4.0", "cc-by-sa-4.0", "cc0-1.0", "bsd-3-clause")


def _get(url, tok=""):
    h = {"User-Agent": UA, "Accept": "application/json"}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"la source a répondu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        raise RuntimeError(f"source injoignable ({str(e)[:80]})") from None


def _niveau(cat):
    """Niveau maximal des vignettes montrees pour une categorie (echelle Civitai : 1 tous publics, 2, 4, 8, 16)."""
    return {1: 2, 2: 4}.get(temps_min(cat), 32)


def _cote(nom):
    n = nom.lower()
    return "high" if re.search(r"high|[_\-. ]hn?[_\-. ]", n) else "low" if re.search(r"low|[_\-. ]ln?[_\-. ]", n) else ""


def _fichiers(noms):
    """Parmi des fichiers (nom, ...), ceux a charger : la paire high/low d'une LoRA video, sinon le premier."""
    hi = next((f for f in noms if _cote(f["nom"]) == "high"), None)
    lo = next((f for f in noms if _cote(f["nom"]) == "low"), None)
    if hi and lo:
        return [{**hi, "role": "high"}, {**lo, "role": "low"}]
    return [{**noms[0], "role": ""}] if noms else []


def _vignette(url, video):
    """Adresse d'une vignette fixe de 320 px chez Civitai (pour une video : sa premiere image)."""
    u = re.sub(r"/(original=true|width=\d+)[^/]*/", "/anim=false,transcode=true,width=320/" if video else "/width=320/", url)
    return re.sub(r"\.(mp4|webm)$", ".jpeg", u) if video else u


def _civitai(m, famille):
    """Fiche normalisee d'un modele Civitai pour une famille, ou None s'il n'a pas de version pour elle."""
    bases = FAMILLES[famille]["civitai"]
    vs = [v for v in m.get("modelVersions") or [] if v.get("baseModel") in bases]
    if not vs:
        return None
    noms = [{"nom": str(f.get("name") or ""), "mo": round((f.get("sizeKB") or 0) / 1024), "url": str(f.get("downloadUrl") or ""), "auth": "civitai"}
            for v in (vs if famille == "wan22" else vs[:1]) for f in v.get("files") or []
            if str(f.get("name") or "").endswith(".safetensors") and str(f.get("downloadUrl") or "").startswith("https://civitai.com/api/download/")]
    if not noms:
        return None
    com = m.get("allowCommercialUse")
    com = [com] if isinstance(com, str) else com or []
    return {"cle": f"civitai:{vs[0]['id']}", "source": "civitai", "ref": str(m["id"]), "titre": str(m.get("name") or "")[:120],
            "version": str(vs[0].get("name") or "")[:60], "base": str(vs[0].get("baseModel") or ""), "famille": famille,
            "fichiers": _fichiers(noms), "telechargements": (m.get("stats") or {}).get("downloadCount") or 0,
            "licence": "usage commercial admis" if any(x in com for x in ("Image", "Rent", "Sell")) else "usage commercial non admis",
            "commercial": any(x in com for x in ("Image", "Rent", "Sell")), "adulte": bool(m.get("nsfw")),
            "trigger": ", ".join(str(w) for w in (vs[0].get("trainedWords") or [])[:6])[:200],
            "page": f"https://civitai.com/models/{m['id']}?modelVersionId={vs[0]['id']}",
            "images": [{"u": _vignette(str(i["url"]), i.get("type") == "video"), "n": int(i.get("nsfwLevel") or 32)}
                       for i in (vs[0].get("images") or [])[:8] if str(i.get("url") or "").startswith("https://image.civitai.com/")]}


def _hf(m, famille):
    """Fiche normalisee d'un depot Hugging Face."""
    tags = [str(t) for t in m.get("tags") or []]
    lic = next((t[8:] for t in tags if t.startswith("license:")), "")
    sib = [s for s in m.get("siblings") or [] if isinstance(s, dict)]
    rid = str(m.get("id") or m.get("modelId") or "")
    noms = [{"nom": s["rfilename"], "mo": round((s.get("size") or 0) / 1048576),
             "url": f"https://huggingface.co/{rid}/resolve/main/{urllib.parse.quote(s['rfilename'])}", "auth": ""}
            for s in sib if str(s.get("rfilename") or "").endswith(".safetensors")]
    if not noms or not re.fullmatch(r"[\w.\-]+/[\w.\-]+", rid):
        return None
    adulte = "not-for-all-audiences" in tags
    return {"cle": f"hf:{rid}", "source": "hf", "ref": rid, "titre": rid.split("/")[1][:120], "version": rid.split("/")[0][:60],
            "base": next((b for b in FAMILLES[famille]["hf"] if any(b in t for t in tags)), FAMILLES[famille]["hf"][0]), "famille": famille,
            "fichiers": _fichiers(noms), "telechargements": m.get("downloads") or 0,
            "licence": f"licence {lic}" if lic else "licence non dite", "commercial": lic in LIBRES, "adulte": adulte, "trigger": "",
            "page": f"https://huggingface.co/{rid}",
            "images": [{"u": f"https://huggingface.co/{rid}/resolve/main/{urllib.parse.quote(s['rfilename'])}", "n": 32 if adulte else 1}
                       for s in sib if re.search(r"\.(png|jpe?g|webp)$", str(s.get("rfilename") or ""), re.I)][:8]}


class Hub:
    def __init__(self, data, repo, studio, atelier):
        self.data, self.repo, self.studio, self.at = data, repo, studio, atelier
        self.f = data / "hub.json"
        self.log = data / "hub_sync.log"
        self.proc = None

    # --- etat -----------------------------------------------------------------------------------------------
    def _retenues(self):
        try:
            d = json.loads(self.f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            d = {}
        return d if isinstance(d, dict) else {}

    def _ecrire(self, d):
        self.f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    def _vue(self, x, cat=None):
        """Fiche telle que la page la recoit : une seule vignette, choisie d'apres le niveau admis pour la categorie."""
        lim = _niveau(cat or x.get("cat"))
        v = next((i["u"] for i in x.get("images") or [] if i["n"] <= lim), "")
        return {k: v2 for k, v2 in x.items() if k != "images"} | {"vignette": v, "mo": sum(f["mo"] for f in x["fichiers"]),
                                                                 "fichiers": [{"nom": f["nom"], "mo": f["mo"], "role": f["role"]} for f in x["fichiers"]]}

    def en_cours(self):
        return self.proc is not None and self.proc.poll() is None

    def etat(self):
        bib = self.at.bibliotheque()
        par_cle = {}
        try:
            for k, v in self.at._catalogue().items():
                if v.get("hub"):
                    par_cle[v["hub"]] = k
        except Exception:
            pass
        sur = {x["name"]: x["volume"] for x in bib["loras"]}
        ret = []
        for cle, x in self._retenues().items():
            nom = par_cle.get(cle)
            ret.append(self._vue(x) | {"chargee": bool(nom), "volume": sur.get(nom) if nom else None, "catalogue": nom or ""})
        veille = self.repo / "docs" / "veille-modeles.md"
        journal = []
        if self.log.is_file():
            journal = [l[:300] for l in self.log.read_text(encoding="utf-8", errors="replace").splitlines()
                       if re.search(r"CHARGE |ECHEC |rapport :|pod .* (cree|supprime)|Error|erreur", l)][-12:]
        return {"retenues": ret, "interne": bib["loras"], "inventaire": bib["inventaire"], "defauts": bib["defauts"],
                "categories": bib["categories"], "familles": bib["familles"], "requetes": REQ,
                "veille": veille.read_text(encoding="utf-8") if veille.is_file() else "",
                "occupe": self.studio.running(), "en_cours": self.en_cours(), "journal": journal,
                "can_run": self.studio.can_run(), "cle_civitai": bool(os.environ.get("CIVITAI_TOKEN")), "max_mo": MAX_MO, "max_lot": MAX_LOT}

    # --- recherche ------------------------------------------------------------------------------------------
    def chercher(self, q):
        def un(k, d=""):
            return str((q.get(k) or [d])[0])[:200]
        source, famille, cat = un("source", "civitai"), un("famille", "zimage"), un("cat", "realisme")
        if famille not in FAMILLES or cat not in CATS or source not in ("civitai", "hf"):
            raise ValueError("recherche : source, famille ou catégorie inconnue")
        mots = un("q").strip() or REQ[cat]
        doux = temps_min(cat) <= 2
        deja = self._retenues()
        if source == "civitai":
            p = [("types", "LORA"), ("sort", "Most Downloaded"), ("limit", "24"), ("nsfw", "false" if doux else "true")]
            p += [("baseModels", b) for b in FAMILLES[famille]["civitai"]]
            if mots:
                p.append(("query", mots))
            if un("cursor"):
                p.append(("cursor", un("cursor")))
            r = _get("https://civitai.com/api/v1/models?" + urllib.parse.urlencode(p), os.environ.get("CIVITAI_TOKEN", ""))
            items = [x for x in (_civitai(m, famille) for m in r.get("items") or []) if x]
            suite = str((r.get("metadata") or {}).get("nextCursor") or "")
        else:
            page = int(un("cursor", "0") or 0) if un("cursor", "0").isdigit() else 0
            items = []
            for base in FAMILLES[famille]["hf"]:
                p = [("filter", f"base_model:adapter:{base}"), ("sort", "downloads"), ("direction", "-1"), ("limit", "40"), ("full", "true")]
                if un("q").strip():  # la recherche de Hugging Face porte sur le nom du depot : pas de mot par defaut
                    p.append(("search", un("q").strip().split()[0]))
                items += [x for x in (_hf(m, famille) for m in _get("https://huggingface.co/api/models?" + urllib.parse.urlencode(p))) if x]
            items.sort(key=lambda x: -x["telechargements"])
            items, suite = items[page * 24:page * 24 + 24], str(page + 1) if len(items) > page * 24 + 24 else ""
        if doux:  # categories tous publics ou suggestives : les fiches marquees pour adultes n'y figurent pas
            items = [x for x in items if not x["adulte"]]
        return {"resultats": [self._vue(x, cat) | {"retenue": x["cle"] in deja} for x in items], "suite": suite,
                "mots": mots if source == "civitai" else un("q").strip() or "toutes les LoRA de ce modèle"}

    # --- retenues -------------------------------------------------------------------------------------------
    def _nom(self, titre, pris):
        base = re.sub(r"[^a-z0-9]+", "_", titre.lower()).strip("_")[:32] or "lora"
        nom, i = base, 2
        while nom in pris:
            nom, i = f"{base}_{i}", i + 1
        return nom

    def retenir(self, b):
        """Retient une LoRA : sa fiche est relue chez la source, rien n'est pris de la page hors la reference et la categorie."""
        source, ref, famille, cat = str(b.get("source")), str(b.get("ref") or ""), str(b.get("famille")), str(b.get("cat"))
        if famille not in FAMILLES or cat not in CATS:
            raise ValueError("famille ou catégorie inconnue")
        if source == "civitai" and ref.isdigit():
            x = _civitai(_get(f"https://civitai.com/api/v1/models/{ref}", os.environ.get("CIVITAI_TOKEN", "")), famille)
        elif source == "hf" and re.fullmatch(r"[\w.\-]+/[\w.\-]+", ref):
            x = _hf(_get(f"https://huggingface.co/api/models/{ref}?blobs=true"), famille)
        else:
            raise ValueError("référence inconnue")
        if not x:
            raise ValueError("cette fiche n'a pas de fichier .safetensors pour ce modèle de base")
        with self.at.lock:
            d = self._retenues()
            if len(d) >= 200 and x["cle"] not in d:
                raise ValueError("200 LoRA retenues : en retirer avant d'en ajouter")
            pris = set(self.at._lib()["cat"]) | {v["name"] for k, v in d.items() if k != x["cle"]}
            vieux = d.get(x["cle"]) or {}
            d[x["cle"]] = x | {"cat": cat, "name": vieux.get("name") or self._nom(x["titre"], pris), "label": vieux.get("label") or x["titre"][:80],
                               "strength": vieux.get("strength") or (1.0 if famille == "wan22" else 0.6), "trigger": vieux.get("trigger") or x["trigger"]}
            self._ecrire(d)
        return self.etat()

    def retirer(self, b):
        with self.at.lock:
            d = self._retenues()
            d.pop(str(b.get("cle")), None)
            self._ecrire(d)
        return self.etat()

    def regler(self, b):
        """Categorie, nom court, intitule, force conseillee et mots declencheurs d'une LoRA retenue. Si elle est deja
        chargee, le catalogue suit (sauf le nom court, qui est celui de son fichier)."""
        cle = str(b.get("cle"))
        with self.at.lock:
            d = self._retenues()
            if cle not in d:
                raise ValueError("LoRA non retenue")
            x = d[cle]
            if b.get("cat") is not None:
                if b["cat"] not in CATS:
                    raise ValueError("catégorie inconnue")
                x["cat"] = b["cat"]
            if b.get("strength") is not None:
                try:
                    f = float(b["strength"])
                except (TypeError, ValueError):
                    f = 0
                if not 0 < f <= 2:
                    raise ValueError("force conseillée : entre 0,1 et 2")
                x["strength"] = round(f, 2)
            if b.get("label") is not None:
                x["label"] = str(b["label"]).strip()[:80] or x["titre"][:80]
            if b.get("trigger") is not None:
                x["trigger"] = str(b["trigger"]).strip()[:200]
            charge = next((k for k, v in self.at._catalogue().items() if v.get("hub") == cle), "")
            if b.get("name") is not None and not charge:
                nom = str(b["name"])
                if not re.fullmatch(r"[a-z0-9_]{1,40}", nom):
                    raise ValueError("nom court : lettres minuscules, chiffres, tirets bas")
                if nom in self.at._lib()["cat"] or any(v["name"] == nom for k, v in d.items() if k != cle):
                    raise ValueError("ce nom court est déjà pris")
                x["name"] = nom
            self._ecrire(d)
            if charge:
                import yaml
                f = self.data / "lora_catalog.yaml"
                cat = (yaml.safe_load(f.read_text(encoding="utf-8")) or {}) if f.is_file() else {}
                if charge in cat:
                    cat[charge] |= {"cat": x["cat"], "strength": x["strength"], "label": x["label"], "trigger": x["trigger"]}
                    f.write_text(yaml.safe_dump(cat, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return self.etat()

    # --- chargement -----------------------------------------------------------------------------------------
    def charger(self, b):
        """Charge sur le volume les LoRA retenues nommees : un seul pod pour le lot, supprime a la fin."""
        cles = [str(c) for c in b.get("cles") or []]
        if not cles or len(cles) > MAX_LOT:
            raise ValueError(f"de 1 à {MAX_LOT} LoRA par lot")
        if self.studio.running() or self.en_cours() or self.at.chaine_active():
            raise ValueError("un calcul est déjà en cours : attendre sa fin")
        if not self.studio.can_run():
            raise ValueError("clé RunPod absente : chargement impossible depuis l'interface")
        d, todo = self._retenues(), []
        for c in cles:
            x = d.get(c)
            if not x:
                raise ValueError("LoRA non retenue")
            if not x["commercial"]:
                raise ValueError(f"« {x['label']} » : {x['licence']}. Le projet est commercial : elle ne se charge pas.")
            if any(f["mo"] > MAX_MO for f in x["fichiers"]):
                raise ValueError(f"« {x['label']} » : fichier de plus de {MAX_MO} Mo")
            if x["source"] == "civitai" and not os.environ.get("CIVITAI_TOKEN"):
                raise ValueError("clé Civitai absente du service : chargement depuis Civitai impossible")
            lim = _niveau(x["cat"])
            todo.append({"cle": c, "name": x["name"], "label": x["label"], "strength": x["strength"], "base": x["base"], "famille": x["famille"],
                         "cat": x["cat"], "trigger": x["trigger"], "source": x["page"],
                         "vignette": next((i["u"] for i in x.get("images") or [] if i["n"] <= lim), ""),
                         "fichiers": [{"role": f["role"], "url": f["url"], "auth": f["auth"]} for f in x["fichiers"]]})
        (self.data / "hub_charger.json").write_text(json.dumps(todo, ensure_ascii=False), encoding="utf-8")
        self.proc = self.studio.proc = subprocess.Popen([sys.executable, "-m", "pilot", "lora", "sync", "--data", str(self.data)],
                                                        cwd=str(self.repo / "server"), stdout=open(self.log, "w"), stderr=subprocess.STDOUT)
        return {"lance": len(todo)}

    # --- routes ---------------------------------------------------------------------------------------------
    def get(self, path, q):
        if path == "/api/h/etat":
            return self.etat()
        if path == "/api/h/chercher":
            return self.chercher(q)
        return None

    def post(self, path, b):
        f = {"/api/h/retenir": self.retenir, "/api/h/retirer": self.retirer, "/api/h/regler": self.regler, "/api/h/charger": self.charger}.get(path)
        return f(b) if f else None
