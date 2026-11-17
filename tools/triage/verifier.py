#!/usr/bin/env python3
"""Verifie un depot avant de l'annoncer au proprietaire : plans (server/jobs/atelier/<nom>.yaml) ou fiche de
personnage (server/jobs/atelier/personnages/<slug>.yaml). Dit exactement ce que la page Atelier en dira : refus,
remarques du controle des plans, modele perime. Lecture seule, sans GPU ni IA, sans rien enregistrer.

    python3 tools/triage/verifier.py server/jobs/atelier/mavideo.yaml [autre.yaml ...]
    python3 tools/triage/verifier.py --etat      # modeles en cours, personnages, projets
    python3 tools/triage/verifier.py --positions     # positions que "acte" peut ecrire aux temps 4 et 5 (une par ligne)
    python3 tools/triage/verifier.py --retour        # retour de tournage : chaque script importe, en une ligne
    python3 tools/triage/verifier.py --retour mavideo   # le detail d'un script, scene par scene (ou --notes pNNNN : un projet entier)

Code de sortie : 0 rien a corriger ; 1 des remarques restent ; 2 un fichier est refuse ou ecrit d'apres un modele perime."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelier  # noqa: E402


def ouvrir():
    """L'atelier en lecture seule : sans son demarrage, qui cree des dossiers et reprend les chaines."""
    a = atelier.Atelier.__new__(atelier.Atelier)
    a.data, a.repo = REPO / "server" / "data", REPO
    a.dp, a.dj = a.data / "personnages", a.data / "projets"
    a.dd = REPO / "server" / "jobs" / "atelier"
    a.df = a.dd / "personnages"
    a.biblio = atelier.biblio.Biblio(a)  # lecture des lieux du personnage qui ont une image
    return a


def modele(nom):
    import yaml
    return str(yaml.safe_load((REPO / "server" / "jobs" / nom).read_text(encoding="utf-8"))["modele"])


def etat(a):
    print(f"modele des plans : {modele('modele.yaml')} (server/jobs/modele.yaml)")
    print(f"modele des fiches de personnage : {modele('personnage.modele.yaml')} (server/jobs/personnage.modele.yaml)")
    print("personnages :")
    for p in a.persos().values():
        print(f"  {p['slug']} : {p['nom']}, {p['age']} ans, {p.get('statut', 'actif')}, "
              f"{'LoRA du visage en place' if (p.get('generation') or {}).get('lora') else 'sans LoRA du visage'}")
        g = p.get("generation") or {}  # ce que le pilote ajoute deja devant chaque image : a ne pas redire dans les plans
        if g.get("identite"):
            for k in ("identite", "allure", "visage", "corps"):
                print(f"      {k} : {g.get(k) or '(vide)'}")
        elif g.get("zimage_prefix"):
            print(f"      description (un seul bloc) : {g['zimage_prefix'].strip()} {g.get('corps') or ''}".rstrip())
    print("projets :")
    for d in sorted(a.dj.glob("p*/projet.json")):
        p = atelier._load(d, {})
        temps = sorted({s.get("temps", 1) for s in p.get("scenes") or []})
        print(f"  {d.parent.name} : {p.get('personnage', '')}, temps ecrits {temps or 'aucun'}")


POINTS = ("decor", "tenue", "geste", "objet", "cadrage")


def _script(s):
    """Nom du script d'ou vient une scene ("" : scene ecrite dans la Production)."""
    return (s.get("origine") or "").rpartition(":")[0].removesuffix(".yaml")


def _bilan(d, pid, sc):
    """Compte d'un lot de scenes : images et clips retenus, scenes refaites, moyenne des notes des images retenues."""
    import re
    n = atelier._load(d / "notes_images.json", {})
    prises = lambda s: len(list((d / "media").glob(f"{pid}r*_{s['id']}.png")))
    sc_n = [n[s["image"]]["score"] for s in sc if isinstance((n.get(s.get("image") or "") or {}).get("score"), int) and n[s["image"]]["score"] >= 0]
    return (f"{len(sc)} scene(s), {sum(bool(s.get('image')) for s in sc)} image(s) retenue(s), {sum(bool(s.get('clip')) for s in sc)} clip(s), "
            f"{sum(prises(s) > 1 for s in sc)} scene(s) refaite(s), "
            + (f"note moyenne {sum(sc_n) / len(sc_n):.1f}/10 sur {len(sc_n)} image(s)" if sc_n else "aucune note"))


def retour(a, nom=""):
    """Retour de tournage pour le scenariste. Sans nom : une ligne par script importe. Avec : le detail de ce script."""
    nom, vu = Path(nom).name.removesuffix(".yaml"), 0
    for f in sorted(a.dj.glob("p*/projet.json")):
        p, pid = atelier._load(f, {}), f.parent.name
        for sn in sorted({_script(s) for s in p.get("scenes") or []} - {""}):
            if nom and sn != nom:
                continue
            vu += 1
            print(f"{sn} (projet {pid}) : " + _bilan(f.parent, pid, [s for s in p["scenes"] if _script(s) == sn]))
            if nom:
                notes(a, pid, sn)
    if not vu:
        print(f"aucun script importe du nom de {nom}" if nom else "aucun script importe pour l'instant")
    return 0 if vu else 2


def notes(a, pid, script=""):
    """Retour d'un calcul, scene par scene : note de l'image retenue (sinon la mieux notee), points douteux ou absents,
    champs de pose, cases du proprietaire. Rien que des valeurs fermees et des nombres. "script" : ses scenes seulement."""
    import re
    d = a.dj / pid
    if not re.fullmatch(r"p\d{4}", pid) or not (d / "projet.json").is_file():
        print(f"projet inconnu : {pid}")
        return 2
    p, n, v = atelier._load(d / "projet.json", {}), atelier._load(d / "notes_images.json", {}), atelier._load(d / "verdicts.json", {})
    avis = lambda x: "respecte" if x >= 0.6 else "douteux" if x >= 0.35 else "absent"
    for s in p.get("scenes") or []:
        if script and _script(s) != script:
            continue
        ims = [k for k in n if re.fullmatch(rf"{pid}r\d+_{s['id']}\.png", k) and isinstance(n[k].get("score"), int) and n[k]["score"] >= 0]
        im = s.get("image") if s.get("image") in ims else max(ims, key=lambda k: n[k]["score"], default="")
        print(f"{s['id']} [{s.get('origine') or s.get('titre') or ''}] temps {s.get('temps', 1)} : "
              + (f"{im}{' (retenue)' if im == s.get('image') else ''}, note {n[im]['score']}/10, {len(ims)} image(s) notee(s)" if im else "aucune image notee"))
        np = len(list((d / "media").glob(f"{pid}r*_{s['id']}.png")))
        print(f"   tournage : {np} image(s) faite(s){' (scene refaite)' if np > 1 else ''}, "
              f"image {'retenue' if s.get('image') else 'non retenue'}, clip {'fait' if s.get('clip') else 'pas fait'}")
        if not im:
            continue
        x = n[im]
        pr, ch = x.get("p") or {}, x.get("champs") or {}
        faibles = [f"{k} {avis(pr[k])} ({pr[k]})" for k in POINTS if k in pr and pr[k] < 0.6]
        faibles += [m for k, m in (("en_trop", "telephone, personne ou texte en trop"), ("anatomie", "anatomie douteuse")) if pr.get(k, 0) >= 0.6]
        print("   controle : " + ("; ".join(faibles) or "rien a signaler"))
        if ch:
            print("   pose : " + "; ".join(f"{k} {avis(c)} ({c})" for k, c in ch.items()))
        if v.get(im):
            print("   proprietaire : " + ", ".join(v[im]))
    return 0


def verifier(a, f):
    """Rend 0, 1 ou 2 (voir l'en-tete)."""
    print(f"== {f}")
    if not f.is_file():
        print("  REFUSE : fichier absent")
        return 2
    try:
        if f.parent.resolve() == a.df.resolve():
            p, rem = a._fiche_deposee(f)
            perime = str(__import__("yaml").safe_load(f.read_text(encoding="utf-8")).get("modele") or "") != modele("personnage.modele.yaml")
            print(f"  fiche de personnage : {p['nom']}, {p['age']} ans, nom court {p['slug']}"
                  + (" ; REMPLACERA la fiche du meme nom" if p["slug"] in a.persos() else ""))
            rem, ref = [{"plan": "", "grave": False, "msg": m} for m in rem], "server/jobs/personnage.modele.yaml"
        elif f.parent.resolve() == a.dd.resolve():
            x = a.examen(f)
            print(f"  {x['plans']} plan(s) pour " + (f"les temps {', '.join(map(str, x['lestemps']))}, " if len(x['lestemps']) > 1 else f"le temps {x['temps']}, ") + (f"projet {x['projet']}" if x["projet"] else f"projet qu'ouvrira {x['attente']}" if x["attente"] else "nouveau projet"))
            if any(x["garder"].values()):
                print(f"  a garder : {x['garder']['tenues']} tenue(s), {x['garder']['lieux']} lieu(x) nommes dans \"garder\" (la tenue et le lieu de la continuite sont proposes d'office au proprietaire s'ils sont nouveaux)")
            rem, perime, ref = x["remarques"], x["perime"], "server/jobs/modele.yaml"
        else:
            print("  REFUSE : un depot se place dans server/jobs/atelier/ (plans) ou server/jobs/atelier/personnages/ (fiche)")
            return 2
    except Exception as e:
        print(f"  REFUSE : {e}")
        return 2
    for r in rem:
        print(f"  {'GRAVE' if r['grave'] else 'remarque'}{' [' + r['plan'] + ']' if r['plan'] else ''} : {r['msg']}")
    if perime:
        print(f"  PERIME : la ligne \"modele\" n'est pas celle de {ref} ; relire ce modele et refaire le fichier d'apres lui")
        return 2
    if not rem:
        print("  rien a corriger")
    return 1 if rem else 0


if __name__ == "__main__":
    a, args = ouvrir(), sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    if args[0] == "--etat":
        etat(a)
        sys.exit(0)
    if args[0] == "--positions":  # liste fermee des positions des temps 4 et 5 (fiches de capacite des LoRA) ; vide : "acte" est libre
        print("\n".join(sorted(x["acte"] for x in a.capacites().values())) or "aucune position inscrite : \"acte\" s'ecrit librement")
        sys.exit(0)
    if args[0] == "--retour":
        sys.exit(retour(a, *args[1:2]))
    if args[0] == "--notes":
        sys.exit(max([notes(a, x) for x in args[1:]] or [2]))
    sys.exit(max(verifier(a, Path(x).resolve()) for x in args))
