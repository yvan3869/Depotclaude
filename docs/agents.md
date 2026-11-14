# Piloter la generation depuis un autre agent (14/11/2026, revu le 14/11 : trois temps, depot dans l'atelier)

Fiche destinee a un agent installe sur le serveur Oracle (par exemple OpenClaw) et configure par le
proprietaire. L'agent ecrit des fichiers de plans. Il les depose dans l'Atelier, ou le proprietaire
les importe, les calcule et les monte (voie normale), ou il lance lui-meme le pilote pour un essai,
dont les images arrivent dans le Tri. Rien n'est publie sans validation du proprietaire.

## Regles
- Personnages fictifs et clairement adultes ; aucune ressemblance avec une personne reelle, aucune
  photo de personne reelle en entree (`docs/compliance.md`, regle 1).
- Plafond GPU commun a tous les lanceurs : 7,50 $ par jour (heure de Paris), applique par le pilote
  lui-meme. Au-dela, le pilote refuse de creer un pod (message "plafond GPU du jour atteint").
  Ne pas contourner : le plafond se change seulement par le proprietaire (`infra.daily_cap_usd`
  dans `persona/production.yaml`).
- Un seul lancement a la fois. Ne jamais redemarrer le conteneur `triage`.
- Ne rien modifier hors de `server/jobs/` (fichiers de plans de l'agent, dont `server/jobs/atelier/`).
  Le reste du depot et `server/data/` se lisent, ils ne s'ecrivent pas.

## Le phasage : une video en trois temps
Chaque video est un projet de l'Atelier (page `/atelier` du studio), decoupe en trois temps qui se
suivent dans le meme decor et la meme tenue :

| Temps | Contenu | Public | Qui l'ecrit |
|---|---|---|---|
| 1. Accroche | teaser de 15 a 20 s, suggestif, coupe avant la suite, appel a l'action | reseaux, tous publics | le redacteur de l'atelier |
| 2. Montee | la suite du teaser, un cran plus loin a chaque scene | abonnes | le redacteur de l'atelier, ou l'agent |
| 3. Final | la fin de la scene | prive, payant | le proprietaire ou l'agent ; jamais le redacteur de l'atelier |

Chaque temps a ses scenes, ses images, ses clips et son montage (`final_vN.mp4` pour le temps 1,
`final_t2_vN.mp4`, `final_t3_vN.mp4`). Le role de l'agent : construire les plans du temps 3 (et du
temps 2 si le proprietaire le demande) et les deposer dans l'atelier. Le proprietaire les importe,
lance le calcul depuis la page, choisit les prises et monte.

## Deposer des plans dans l'atelier
1. **Lire le projet** : `server/data/projets/pNNNN/projet.json` (lecture seule). On y trouve le
   personnage, le pitch et les scenes deja ecrites, chacune avec son `temps`. Reprendre dans chaque
   `still` exactement les memes mots de lieu et de tenue que les scenes du temps 1, et repartir de
   l'instant ou le temps precedent s'arrete. Fiches des personnages : `persona/personnages/<slug>.json`
   (versions modifiees dans la page : `server/data/personnages/`).
2. **Ecrire le fichier** `server/jobs/atelier/<nom>.yaml` d'apres `server/jobs/modele.yaml` (voir
   plus bas), avec en plus le bloc `atelier` :

       modele: "<date du modele en cours>"
       name: p0001_final
       atelier:
         projet: p0001        # projet vise ; "" ou absent : la page cree un nouveau projet
         temps: 3             # 1, 2 ou 3
         personnage: lea      # seulement pour un nouveau projet
         titre: ""            # seulement pour un nouveau projet
         note: "une ligne pour le proprietaire"
       defaults:
         seed: 100
         loras: []            # noms du catalogue : docker compose run --rm pilot lora list
       shots:
         - name: plan01       # unique dans le fichier, lettres, chiffres et _
           titre: "..."       # nom de la scene dans la page (facultatif)
           still: "..."       # obligatoire
           motion: "She ..."  # facultatif : sans lui, la scene reste une image fixe
           texte: ""          # texte incruste au montage (facultatif)

   Champs repris par plan : `name`, `still`, `motion`, `end_edit`, `tattoos`, `loras`, `seed`,
   `titre`, `texte`, `voix`, `role`. De 1 a 10 plans par fichier. `steps`, `image` et `character`
   ne sont pas repris ; `body` et `dest` sont inutiles (le temps et la fiche du personnage en
   tiennent lieu). Un fichier par projet et par temps.
3. **Ne pas lancer le pilote sur ce fichier.** Il apparait dans la page du projet (ou a l'accueil de
   l'atelier s'il ne vise aucun projet), avec son erreur s'il est mal forme (bloc `atelier` absent,
   `temps` invalide, nom en double, `still` manquant, modele perime). Le proprietaire appuie sur
   "Importer dans le projet" : les plans deviennent des scenes du temps indique.
4. **Corriger** : modifier le meme fichier, sans changer les `name`. La page signale le changement
   et le proprietaire reimporte ; les scenes sont remplacees une a une, et l'image deja calculee est
   gardee tant que `still` n'a pas change. Un plan retire du fichier reste dans le projet.

Les fichiers de `server/jobs/atelier/` ne sont pas suivis par git. Le lancement direct du pilote
(ci-dessous) reste possible pour des essais hors atelier : ces images vont dans le Tri, pas dans un projet.

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
sous un autre nom dans `server/jobs/` (ou `server/jobs/atelier/` pour un depot) et l'adapter. Ne pas partir d'un ancien plan, d'un exemple du
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
