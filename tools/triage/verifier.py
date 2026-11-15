#!/usr/bin/env python3
"""Verifie un depot avant de l'annoncer au proprietaire : plans (server/jobs/atelier/<nom>.yaml) ou fiche de
personnage (server/jobs/atelier/personnages/<slug>.yaml). Dit exactement ce que la page Atelier en dira : refus,
remarques du controle des plans, modele perime. Lecture seule, sans GPU ni IA, sans rien enregistrer.

    python3 tools/triage/verifier.py server/jobs/atelier/mavideo.yaml [autre.yaml ...]
    python3 tools/triage/verifier.py --etat      # modeles en cours, personnages, projets
    python3 tools/triage/verifier.py --notes pNNNN   # ce que le controle automatique et le proprietaire ont trouve, par scene

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
    print("projets :")
    for d in sorted(a.dj.glob("p*/projet.json")):
        p = atelier._load(d, {})
        temps = sorted({s.get("temps", 1) for s in p.get("scenes") or []})
        print(f"  {d.parent.name} : {p.get('personnage', '')}, temps ecrits {temps or 'aucun'}")


POINTS = ("decor", "tenue", "geste", "objet", "cadrage")


def notes(a, pid):
    """Retour d'un calcul, scene par scene : note de l'image retenue (sinon la mieux notee), points douteux ou absents,
    champs de pose, cases du proprietaire. Rien que des valeurs fermees et des nombres."""
    import re
    d = a.dj / pid
    if not re.fullmatch(r"p\d{4}", pid) or not (d / "projet.json").is_file():
        print(f"projet inconnu : {pid}")
        return 2
    p, n, v = atelier._load(d / "projet.json", {}), atelier._load(d / "notes_images.json", {}), atelier._load(d / "verdicts.json", {})
    avis = lambda x: "respecte" if x >= 0.6 else "douteux" if x >= 0.35 else "absent"
    for s in p.get("scenes") or []:
        ims = [k for k in n if re.fullmatch(rf"{pid}r\d+_{s['id']}\.png", k) and isinstance(n[k].get("score"), int) and n[k]["score"] >= 0]
        im = s.get("image") if s.get("image") in ims else max(ims, key=lambda k: n[k]["score"], default="")
        print(f"{s['id']} [{s.get('origine') or s.get('titre') or ''}] temps {s.get('temps', 1)} : "
              + (f"{im}{' (retenue)' if im == s.get('image') else ''}, note {n[im]['score']}/10, {len(ims)} image(s) notee(s)" if im else "aucune image notee"))
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
    if args[0] == "--notes":
        sys.exit(max([notes(a, x) for x in args[1:]] or [2]))
    sys.exit(max(verifier(a, Path(x).resolve()) for x in args))
