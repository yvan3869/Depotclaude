# Piloter la generation depuis un autre agent (14/11/2026)

Fiche destinee a un agent installe sur le serveur Oracle (par exemple OpenClaw) et configure par le
proprietaire. L'agent ecrit des fichiers de plans et lance le pilote ; les images arrivent dans le
Tri, ou le proprietaire valide. Rien n'est publie sans ce tri.

## Regles
- Personnages fictifs et clairement adultes ; aucune ressemblance avec une personne reelle, aucune
  photo de personne reelle en entree (`docs/compliance.md`, regle 1).
- Plafond GPU commun a tous les lanceurs : 7,50 $ par jour (heure de Paris), applique par le pilote
  lui-meme. Au-dela, le pilote refuse de creer un pod (message "plafond GPU du jour atteint").
  Ne pas contourner : le plafond se change seulement par le proprietaire (`infra.daily_cap_usd`
  dans `persona/production.yaml`).
- Un seul lancement a la fois. Ne jamais redemarrer le conteneur `triage`.
- Ne rien modifier hors de `server/jobs/` (fichiers de plans de l'agent).

## Commandes (depuis `/home/debian/Depotclaude/server`)
    docker compose run --rm pilot depenses                            # depense du jour / plafond
    docker compose run --rm pilot run jobs/<plan>.yaml --stills-only  # images seules
    docker compose run --rm pilot run jobs/<plan>.yaml                # images puis clips (plans avec "motion")
    docker compose run --rm pilot lora list                           # LoRA supplementaires disponibles
    docker compose run --rm pilot pods                                # pods en cours

Le pilote cree un pod, calcule, supprime le pod et ecrit un rapport (duree, cout) a la fin de sa
sortie. Code de sortie 0 : tout est fait ; 1 : au moins un plan a echoue ; 2 : arret (plafond,
pas de machine disponible, cle refusee).

## Format d'un fichier de plans
    name: monlot                 # prefixe des fichiers produits (lettres, chiffres, _)
    defaults:
      still_size: [864, 1152]    # largeur, hauteur de l'image
      seed: 100                  # tirage ; chaque plan ajoute son rang, sauf same_seed: true
      same_seed: false           # true : meme tirage pour tous les plans (comparaisons)
      char_strength: 1.4         # force du LoRA du personnage (1,2 a 1,4 ; en dessous, l'identite faiblit)
      loras: []                  # LoRA supplementaires : [nom] ou [{name: nom, strength: 0.6}]
    shots:
      - name: img01
        still: "description de l'image en anglais : cadrage, lieu, tenue, pose, expression, lumiere"
      - name: img02
        still: "..."
        motion: "mouvement du clip de 5 s (facultatif)"

Le debut du prompt qui decrit le personnage (mot declencheur, cheveux, yeux) est ajoute par le
pilote : ne pas le repeter, ni decrire les tatouages (le LoRA les porte ; les decrire les double).

## Resultats et couts
- Images et clips : `server/data/inbox/<name>_<plan>.png|mp4`, visibles dans le Tri.
- Rapport : `server/data/work/<name>/report.json`. Registre des depenses : `server/data/depenses.jsonl`.
- Reperes (RTX PRO 4500, 0,72 $/h) : demarrage du pod ~1 a 5 min ; image ~9 s ; un lot de 20 images
  coute ~0,05 $. Clip 5 s en 480p ~0,035 $ (RTX 4090).
