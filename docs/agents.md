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
**La seule reference est `server/jobs/modele.yaml`**, tenu a jour a chaque evolution du pilote.
Avant d'ecrire un plan, relire ce fichier (il peut avoir change depuis la derniere fois), le copier
sous un autre nom dans `server/jobs/` et l'adapter. Ne pas partir d'un ancien plan, d'un exemple du
dossier ni de sa memoire : ils peuvent etre perimes.

- Recopier la ligne `modele: "<date>"` telle quelle. Le pilote la compare a sa version et ecrit
  "ATTENTION : plan ecrit d'apres le modele ..." si le plan est en retard : dans ce cas, refaire le
  plan d'apres le modele en cours avant de relancer.
- N'utiliser que les champs presents dans le modele. Un champ inconnu est ignore sans message.
- Ne pas remplir `body` ni `dest` (reserves au proprietaire).

Le debut du prompt qui decrit le personnage (mot declencheur, cheveux, yeux) est ajoute par le
pilote : ne pas le repeter, ni decrire les tatouages (le LoRA les porte ; les decrire les double).

## Resultats et couts
- Images et clips : `server/data/inbox/<name>_<plan>.png|mp4`, visibles dans le Tri.
- Rapport : `server/data/work/<name>/report.json`. Registre des depenses : `server/data/depenses.jsonl`.
- Reperes (RTX PRO 4500, 0,72 $/h) : demarrage du pod ~1 a 5 min ; image ~9 s ; un lot de 20 images
  coute ~0,05 $. Clip 5 s en 480p ~0,035 $ (RTX 4090).
