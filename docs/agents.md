# Piloter la generation depuis un autre agent (14/11/2026, revu le 14/11 : quatre temps, bibliotheque de LoRA, depot dans l'atelier, date du personnage, continuite et raccords)

Fiche destinee a un agent installe sur le serveur Oracle (par exemple OpenClaw) et configure par le
proprietaire. L'agent ecrit des fichiers de plans. Il les depose dans l'Atelier, ou le proprietaire
les importe, les calcule et les monte (voie normale), ou il lance lui-meme le pilote pour un essai,
dont les images arrivent dans le Tri. Rien n'est publie sans validation du proprietaire.

## Vocabulaire
Les memes mots servent dans la page Atelier, dans les fichiers et dans les echanges avec le proprietaire.

| Terme | Sens |
|---|---|
| Projet | Une video entiere : l'idee, le pitch, les textes de publication et les quatre temps. Numerote `pNNNN`. |
| Idee | La phrase de depart, avant ecriture. |
| Pitch | Le resume du projet en une ou deux phrases, une fois l'idee retenue. |
| Temps | Une des quatre parties du projet : 1 accroche, 2 montee, 3 devoile, 4 final. |
| Scene | Une unite d'un temps : une image, un mouvement eventuel, un texte a l'ecran. |
| Plan | La scene vue du cote de l'agent : une entree de `shots` dans son fichier. Un plan importe devient une scene. |
| Depot | Un fichier de plans place dans `server/jobs/atelier/`, pour un projet et un temps. |
| Prise | Un resultat calcule pour une scene (image ou clip). Il peut y en avoir plusieurs ; le proprietaire choisit. |
| Montage | La video finale d'un temps, en versions numerotees. |
| Fiche de continuite | Ce qui ne change pas d'une image a l'autre dans un projet : lieu, tenue, coiffure, lumiere, point de vue. Bloc `continuite`. |
| Image de reference | L'image d'une scene dont les autres images du projet sont tirees par retouche. Champ `reference`. |
| Bibliotheque de LoRA | Page `/atelier#/loras` : les LoRA du catalogue, leur presence sur le volume, et les LoRA par defaut de chaque temps. |
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

## Un projet en quatre temps
Chaque video est un projet de l'Atelier (page `/atelier` du studio), decoupe en quatre temps qui se
suivent dans le meme decor et la meme tenue :

| Temps | Contenu | Public | Registre |
|---|---|---|---|
| 1. Accroche | teaser de 15 a 20 s, 3 scenes environ, coupe avant la suite, appel a l'action | reseaux, tous publics | suggestif au plus : il doit passer la moderation des reseaux |
| 2. Montee | la suite du teaser, un cran plus loin a chaque scene, sans appel a l'action | gratuit ou abonnes : il sert a convertir | suggestif pousse (lingerie, nu suggere), rien d'explicite |
| 3. Devoile | la suite, nudite montree | abonnes ou paiement bas | nudite explicite, sans acte ; fixe par le proprietaire |
| 4. Final | la fin de la scene | prive, paiement a l'unite | explicite ; fixe par le proprietaire |

Chaque temps a ses scenes, ses images, ses clips et son montage (`final_vN.mp4` pour le temps 1,
`final_t2_vN.mp4`, `final_t3_vN.mp4`, `final_t4_vN.mp4`).

**Changement du 14/11/2026.** Jusqu'au modele `2026-11-14e`, il y avait trois temps et le 3 etait le final.
Le final est maintenant le temps 4, et le 3 est le devoile. Les projets existants ont ete convertis
(scenes, montages `final_t3_*` renommes en `final_t4_*`). Un depot ecrit avec un modele anterieur a
`2026-11-14f` et `temps: 3` est lu comme `temps: 4` ; avec le modele en cours, `temps: 3` veut dire devoile.
Ne pas reprendre un ancien fichier sans relire son `temps`.

**Role de l'agent** : il peut ecrire une video entiere, c'est-a-dire les quatre temps, ou seulement
ceux que le proprietaire lui demande. Sans consigne, il ecrit les temps 3 et 4 et laisse les temps 1 et 2
au redacteur de l'atelier. Le redacteur de l'atelier, lui, n'ecrit, ne relit et n'analyse jamais les temps 3
et 4, ni une scene qui porte des `loras`. Dans tous les
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

Ce que la date du personnage impose, sur les quatre temps du projet :
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
  Le `pdv` decrit la vue, jamais l'appareil comme un objet : "shot straight on at chest height on a phone",
  pas "phone propped on the counter, filming her" (le telephone serait dessine dans l'image).
- **Image de reference** (`reference`, au projet) : une fois choisie, les autres images sont fabriquees a
  partir d'elle par retouche (meme personne, meme piece, meme tenue, nouvelle pose). Prendre le plan le
  plus large, celui qui montre le mieux le lieu et la tenue. Une retouche garde le cadrage de la reference,
  sauf si le `still` nomme le sien : "close-up" (ou "extreme close-up") rapproche la camera, "wide shot" ou
  "full-body shot" l'eloigne. Ecrire ces mots tels quels en tete du `still`. Les plans `libre` et ceux qui portent des
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

## Controle des plans
L'atelier relit chaque depot et chaque projet avant tout calcul, sans GPU (`tools/triage/controle.py`), et
affiche ses remarques dans la page (nombre de remarques sur la ligne du depot, detail dans le projet).
Rien n'est bloque, mais un depot sans remarque est l'objectif. Ce qui est verifie :
- fiche de continuite remplie (lieu, tenue, point de vue) ; tenue non repetee dans les `still` ; heure du
  `still` coherente avec la fiche ;
- point de vue respecte : si un telephone filme, il n'est pas dans sa main ; le `pdv` ne decrit pas
  l'appareil comme un objet pose quelque part ;
- premier plan du temps 1 : un `motion` et un texte d'accroche ;
- un seul geste par `motion`, aucun mouvement de camera, aucun geste de la liste des gestes qui ratent ;
- `texte` de 7 mots au plus, sans emoji ;
- progression : chaque plan porte `cran`, de 1 (anodin) a 5 (le plus ose de ce temps), qui ne redescend pas ;
- duree : le temps 1 vise 20 s au plus (un clip dure 5 s) ;
- raccords possibles (un plan continu suit un plan qui a un `motion` ; pas trois continus de suite).

Lire la fiche et l'image de reference du projet dans `projet.json` (`continuite`, `reference`) avant
d'ecrire les temps 2, 3 et 4 : elles s'appliquent a eux aussi.

## Relecture des images
Apres les images et avant les clips, le redacteur IA relit les images retenues des temps 1 et 2 (bouton
"Relire les images", ou d'office a la pause de la chaine) : meme personne, lieu et tenue de la fiche, defauts
d'anatomie, image conforme au `still`, pose d'ou le `motion` peut partir, place pour le texte. Ses remarques
s'affichent sous chaque image et valent tant que l'image retenue est celle relue. Les temps 3 et 4 et les plans
qui portent des `loras` ne sont jamais relus : leur verification reste au proprietaire.

## LoRA supplementaires et bibliotheque
Les LoRA supplementaires (hors LoRA du personnage) se gerent dans la page `/atelier#/loras` :

- **Catalogue** : chaque LoRA a un nom court (celui qu'on ecrit dans `loras`), un fichier `.safetensors`, une force
  conseillee, des mots declencheurs et une note du proprietaire. Il se lit dans `persona/production.yaml`
  (`lora_catalog`) et `server/data/lora_catalog.yaml`, ou par `docker compose run --rm pilot lora list`.
- **Mots declencheurs** : le pilote les ajoute d'office a la fin du prompt d'image. Ne pas les recopier dans `still`.
- **Force** : `loras: [nom]` prend la force conseillee ; `loras: [{name: nom, strength: 0.6}]` la remplace.
- **LoRA par defaut d'un temps** : le proprietaire en fixe pour les temps 2, 3 et 4. Un plan depose **sans** champ
  `loras` (ni dans le plan ni dans `defaults`) les recoit a l'import ; `loras: []` veut dire aucune ; une liste
  ecrite est prise telle quelle. A un nouvel import, une scene deja importee garde les LoRA que le proprietaire
  lui a posees dans la page tant que le plan n'en dit rien. Le temps 1 n'a pas de LoRA par defaut.
- **Presence sur le volume** : a chaque lancement, le pilote note les fichiers du volume dans
  `server/data/lora_volume.json`. Le controle des plans signale comme grave une LoRA absente du catalogue ou dont le
  fichier n'est pas sur le volume : le calcul s'arreterait au demarrage du pod. N'employer que des noms du catalogue.
- Le choix des LoRA et leur inscription restent au proprietaire. L'agent ne modifie ni le catalogue ni les defauts ;
  s'il lui manque une LoRA, il le dit dans `note`.

## Montage
Le montage vise une duree (15 s conseille pour l'accroche) en raccourcissant les plans, sauf du cote d'un raccord
`continu` ou `arrivee`. Consequences pour l'ecriture : le geste important d'un plan se place au milieu du clip, pas
dans la premiere seconde ; sur le premier plan, l'accroche du projet s'affiche d'abord et le `texte` du plan ensuite,
donc un `texte` de premier plan doit pouvoir se lire en 2 secondes. Avant un raccord sans coupe, le texte du plan
s'efface 0,3 s plus tot pour ne pas croiser celui du plan suivant. La mention "AI character" est incrustee d'office
sur le temps 1 (au choix du proprietaire sur les autres) : ne pas l'ecrire dans les textes.

L'accroche doit etre vraie des la premiere scene : ce qu'elle annonce se voit dans l'image de la scene 1 (tenue,
lieu, objet, geste), pas seulement plus tard. Une accroche qui parle d'un peignoir alors que la scene 1 montre un
pull est une faute ; le relecteur et l'analyste la signalent.

Les textes sont incrustes sans bandeau, en blanc sur une ombre douce : eviter de placer le `texte` d'un plan sur une
zone tres claire et chargee de l'image (drap blanc froisse, fenetre en plein jour) ; le decrire dans le `still` si
besoin ("plain dark wall behind her"). Un plan sans `motion` dure 2 s au montage, en zoom lent. Apres chaque montage,
une planche de controle (les images cles cote a cote) s'affiche sous la video : c'est elle que le proprietaire regarde
pour juger raccords et textes.

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
         temps: 3             # 1, 2, 3 ou 4 (voir "Un projet en quatre temps")
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
         # loras: [nom]       # noms du catalogue ; ligne absente : LoRA par defaut du temps ; [] : aucune
       shots:
         - name: plan01       # unique dans le fichier, lettres, chiffres et _
           titre: "..."       # nom de la scene dans la page (facultatif)
           still: "..."       # obligatoire
           motion: "She ..."  # facultatif : sans lui, la scene reste une image fixe
           texte: ""          # texte incruste au montage (facultatif)
           raccord: coupe     # coupe, continu ou arrivee (facultatif)
           cran: 1            # 1 a 5, ne redescend pas (voir "Controle des plans")

   Champs repris par plan : `name`, `still`, `motion`, `end_edit`, `tattoos`, `loras`, `seed`,
   `titre`, `texte`, `voix`, `role`, `raccord`, `libre`, `cran`. De 1 a 10 plans par fichier. `steps`, `image`,
   `edit`, `suite_de`, `end_image` et `character` ne sont pas repris (un depot qui en porte est refuse) ; `body` et `dest` sont inutiles (le temps et la fiche du personnage en
   tiennent lieu). Un fichier par projet et par temps.
   Video entiere : quatre fichiers. Deposer d'abord celui du temps 1 sans `projet` (avec `personnage`
   et `titre`) ; une fois importe, le proprietaire donne le numero du projet cree, a reporter dans
   `projet` pour les fichiers des temps 2, 3 et 4. Ne pas deviner ce numero.
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
