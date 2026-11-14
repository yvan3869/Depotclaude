# Piloter la generation depuis un autre agent (14/11/2026, revu le 14/11 : trois temps, depot dans l'atelier, date du personnage, continuite et raccords)

Fiche destinee a un agent installe sur le serveur Oracle (par exemple OpenClaw) et configure par le
proprietaire. L'agent ecrit des fichiers de plans. Il les depose dans l'Atelier, ou le proprietaire
les importe, les calcule et les monte (voie normale), ou il lance lui-meme le pilote pour un essai,
dont les images arrivent dans le Tri. Rien n'est publie sans validation du proprietaire.

## Vocabulaire
Les memes mots servent dans la page Atelier, dans les fichiers et dans les echanges avec le proprietaire.

| Terme | Sens |
|---|---|
| Projet | Une video entiere : l'idee, le pitch, les textes de publication et les trois temps. Numerote `pNNNN`. |
| Idee | La phrase de depart, avant ecriture. |
| Pitch | Le resume du projet en une ou deux phrases, une fois l'idee retenue. |
| Temps | Une des trois parties du projet : 1 accroche, 2 montee, 3 final. |
| Scene | Une unite d'un temps : une image, un mouvement eventuel, un texte a l'ecran. |
| Plan | La scene vue du cote de l'agent : une entree de `shots` dans son fichier. Un plan importe devient une scene. |
| Depot | Un fichier de plans place dans `server/jobs/atelier/`, pour un projet et un temps. |
| Prise | Un resultat calcule pour une scene (image ou clip). Il peut y en avoir plusieurs ; le proprietaire choisit. |
| Montage | La video finale d'un temps, en versions numerotees. |
| Fiche de continuite | Ce qui ne change pas d'une image a l'autre dans un projet : lieu, tenue, coiffure, lumiere, point de vue. Bloc `continuite`. |
| Image de reference | L'image d'une scene dont les autres images du projet sont tirees par retouche. Champ `reference`. |
| Raccord | Lien d'une scene avec la precedente du meme temps : `coupe`, `continu` ou `arrivee`. |
| Date du personnage | Date fictive du projet : le jour ou le personnage vit la scene. Champ `date_perso`, `AAAA-MM-JJ`. |
| Contexte du moment | Une ligne libre du proprietaire sur ce que le personnage vit ces jours-la. Champ `contexte`. |
| Dates reelles | `cree` et `modifie` dans `projet.json` : quand le projet a ete cree et modifie sur le serveur. Sans effet sur le contenu. |

Ne pas dire "sequence" ni "phase" pour un temps, ni "lot" pour un projet.

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

## Un projet en trois temps
Chaque video est un projet de l'Atelier (page `/atelier` du studio), decoupe en trois temps qui se
suivent dans le meme decor et la meme tenue :

| Temps | Contenu | Public | Registre |
|---|---|---|---|
| 1. Accroche | teaser de 15 a 20 s, 3 scenes environ, coupe avant la suite, appel a l'action | reseaux, tous publics | suggestif au plus : il doit passer la moderation des reseaux |
| 2. Montee | la suite du teaser, un cran plus loin a chaque scene, sans appel a l'action | abonnes | suggestif |
| 3. Final | la fin de la scene | prive, payant | fixe par le proprietaire |

Chaque temps a ses scenes, ses images, ses clips et son montage (`final_vN.mp4` pour le temps 1,
`final_t2_vN.mp4`, `final_t3_vN.mp4`).

**Role de l'agent** : il peut ecrire une video entiere, c'est-a-dire les trois temps, ou seulement
ceux que le proprietaire lui demande. Sans consigne, il ecrit le temps 3 et laisse les temps 1 et 2
au redacteur de l'atelier. Le redacteur de l'atelier, lui, n'ecrit jamais le temps 3. Dans tous les
cas l'agent depose ; le proprietaire importe, lance le calcul depuis la page, choisit les prises et monte.

Le temps 1 porte en plus les textes de publication : `pitch` (resume en francais), `accroche`
(texte a l'ecran de la premiere seconde), `legende` (avec l'appel a l'action et la mention que le
personnage est cree par IA), `cta` (carton de fin), `hashtags`. Ils sont dans la langue du
personnage (champ `langue` de sa fiche), sans emoji (la police de montage ne les affiche pas).

## Date du personnage et dates reelles
Un projet porte deux sortes de dates, a ne jamais confondre.

- **Date du personnage** (`date_perso`, fictive). C'est le jour ou le personnage vit la scene, dans
  son monde. Le proprietaire la choisit proche du jour de publication prevu : une video ecrite en
  novembre pour etre publiee le 19 decembre porte `2026-12-19`. Quand l'agent ecrit ou parle de
  "la date" d'un projet sans autre precision, c'est celle-ci.
- **Dates reelles** (`cree`, `modifie`) : horodatage du serveur. Elles ne disent rien de la scene et
  ne servent jamais a ecrire. Le jour ou l'agent travaille ne compte pas non plus.

Ce que la date du personnage impose, sur les trois temps du projet :
- la saison (hemisphere nord, le personnage vit en France sauf mention contraire dans sa fiche) :
  tenue, meteo, activite, et dans chaque `still` une lumiere et une heure du jour plausibles (nuit a
  17 h 30 en decembre, jour jusqu'a 21 h 30 en juin) ;
- le jour de la semaine (travail, week-end) et les reperes du calendrier a dix jours pres (Noel,
  nouvel an, Saint-Valentin, 14 juillet, rentree, Halloween...) ;
- le `contexte` saisi par le proprietaire, a reprendre tel quel s'il est rempli.

Limites : ne pas ecrire la date elle-meme dans les textes ; aucune actualite reelle (politique, faits
divers, sport, sorties) et aucune personne reelle, meme si la date y invite. Seuls comptent la
saison, le calendrier et le `contexte`.

Continuite : les projets d'un meme personnage forment sa chronologie, classee par date du personnage.
Avant d'ecrire, lire les projets voisins (`date_perso` proche dans `server/data/projets/*/projet.json`,
meme `personnage`) pour ne pas contredire ni repeter ce qu'elle a fait ces jours-la.

Si `date_perso` est vide dans le projet et que le proprietaire n'a rien dit, la lui demander plutot
que de prendre la date du jour.

## Continuite et raccords
Trois outils evitent qu'une video change de piece, de tenue ou de personne d'une scene a l'autre.

- **Fiche de continuite** (`continuite`, au projet) : cinq champs en anglais, `lieu` ("in ..."), `tenue`
  ("wearing ..."), `cheveux`, `lumiere`, `pdv` (point de vue de la camera). L'atelier les ajoute a la fin
  de chaque `still` au moment du calcul. Consequence pour l'ecriture : **un `still` ne contient plus que le
  cadrage, la pose et l'expression** ; ne pas y repeter le lieu ni la tenue. Un champ ne contient que ce
  qui vaut pour toute la video ; ce qui change en route (elle retire une veste) reste dans les `still` et
  le champ correspondant reste vide. Un plan qui se passe ailleurs porte `libre: true`.
- **Image de reference** (`reference`, au projet) : une fois choisie, les autres images sont fabriquees a
  partir d'elle par retouche (meme personne, meme piece, meme tenue, nouvelle pose). Prendre le plan le
  plus large, celui qui montre le mieux le lieu et la tenue. Les plans `libre` et ceux qui portent des
  LoRA supplementaires gardent leur propre tirage.
- **Raccord** (`raccord`, par plan, par rapport au plan precedent du meme temps) :
  - `coupe` (defaut) : le plan a sa propre image, le montage coupe. Pour un changement de cadrage ou d'angle.
  - `continu` : le plan n'a pas d'image propre. Son clip demarre sur la derniere image du clip precedent et
    le montage colle les deux sans coupe visible. A utiliser quand deux gestes se suivent dans le meme
    cadre ("elle sourit" puis "elle se penche"). Le `motion` reprend la ou le precedent s'arrete. La derive
    s'accumule : deux plans continus de suite au plus. `still` reste obligatoire (il decrit l'image attendue).
  - `arrivee` : le clip precedent se termine exactement sur l'image de ce plan (cout double pour ce clip).
    Pour amener un mouvement de camera ou de pose vers un cadre precis.
  Le premier plan d'un temps est toujours une coupe.

Lire la fiche et l'image de reference du projet dans `projet.json` (`continuite`, `reference`) avant
d'ecrire les temps 2 et 3 : elles s'appliquent a eux aussi.

## Deposer des plans dans l'atelier
1. **Lire le projet** : `server/data/projets/pNNNN/projet.json` (lecture seule). On y trouve le
   personnage, le pitch, la date du personnage (`date_perso`), le `contexte` et les scenes deja
   ecrites, chacune avec son `temps`, ainsi que la fiche de continuite (`continuite`). Si la fiche est
   remplie, ne pas repeter le lieu ni la tenue dans les `still` ; si elle est vide, reprendre dans chaque
   `still` exactement les memes mots de lieu et de tenue que les scenes du temps 1. Repartir de
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
         # avec temps: 1 seulement, facultatifs (un champ vide garde celui du projet) :
         pitch: ""
         accroche: ""
         legende: ""
         cta: ""
         hashtags: ""
         # avec temps: 1 seulement, facultatifs (absents : ceux du projet sont gardes) :
         date_perso: "2026-12-19"   # date du personnage, fictive, entre guillemets
         contexte: ""               # contexte du moment, une ligne en francais
         continuite:                # avec temps: 1 seulement ; voir "Continuite et raccords"
           lieu: "in ..."
           tenue: "wearing ..."
           cheveux: ""
           lumiere: "..."
           pdv: "..."
         reference: plan01          # avec temps: 1 seulement : nom d'un plan de ce fichier
       defaults:
         seed: 100
         loras: []            # noms du catalogue : docker compose run --rm pilot lora list
       shots:
         - name: plan01       # unique dans le fichier, lettres, chiffres et _
           titre: "..."       # nom de la scene dans la page (facultatif)
           still: "..."       # obligatoire
           motion: "She ..."  # facultatif : sans lui, la scene reste une image fixe
           texte: ""          # texte incruste au montage (facultatif)
           raccord: coupe     # coupe, continu ou arrivee (facultatif)

   Champs repris par plan : `name`, `still`, `motion`, `end_edit`, `tattoos`, `loras`, `seed`,
   `titre`, `texte`, `voix`, `role`, `raccord`, `libre`. De 1 a 10 plans par fichier. `steps`, `image`,
   `edit`, `suite_de`, `end_image` et `character` ne sont pas repris (un depot qui en porte est refuse) ; `body` et `dest` sont inutiles (le temps et la fiche du personnage en
   tiennent lieu). Un fichier par projet et par temps.
   Video entiere : trois fichiers. Deposer d'abord celui du temps 1 sans `projet` (avec `personnage`
   et `titre`) ; une fois importe, le proprietaire donne le numero du projet cree, a reporter dans
   `projet` pour les fichiers des temps 2 et 3. Ne pas deviner ce numero.
   Date du personnage : pour un nouveau projet, la mettre dans le fichier du temps 1 (celle donnee par
   le proprietaire) ; sans elle, la page prend le jour de l'import. Pour un projet existant, ne pas la
   remettre : celle du projet fait foi. Une date mal formee bloque le depot.
3. **Ne pas lancer le pilote sur ce fichier.** Il apparait dans la page du projet (ou a l'accueil de
   l'atelier s'il ne vise aucun projet), avec son erreur s'il est mal forme (bloc `atelier` absent,
   `temps` invalide, nom en double, `still` manquant, date mal formee, modele perime). Le proprietaire appuie sur
   "Importer dans le projet" : les plans deviennent des scenes du temps indique.
4. **Corriger** : modifier le meme fichier, sans changer les `name`. La page signale le changement
   et le proprietaire reimporte ; les scenes sont remplacees une a une, et l'image deja calculee est
   gardee tant que `still` n'a pas change. Un plan retire du fichier reste dans le projet.
   Les textes de publication remplis dans le fichier remplacent ceux du projet a chaque import.

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
- Reperes (RTX PRO 4500, 0,72 $/h) : demarrage du pod ~1 a 5 min ; image ~9 s ; 20 images
  coute ~0,05 $. Clip 5 s en 480p ~0,035 $ (RTX 4090).
