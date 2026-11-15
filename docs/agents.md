# Piloter la generation depuis un autre agent (14/11/2026, revu le 15/11 : verificateur, video entiere deposee d'un coup, fiches de personnage, skills)

Fiche destinee a un agent installe sur le serveur Oracle (par exemple OpenClaw) et configure par le
proprietaire. L'agent ecrit des fichiers de plans. Il les livre a la Production, qui
les importe ; le proprietaire les tourne et les monte (voie normale), ou il lance lui-meme le pilote pour un essai,
dont les images arrivent dans le Tri. Rien n'est publie sans validation du proprietaire.

## Vocabulaire
Les memes mots servent dans les pages, dans les fichiers et dans les echanges avec le proprietaire. Ce sont ceux
d'une production audiovisuelle (convention du 15/11/2026). Les noms techniques ne changent pas : adresses des pages
(`/atelier`, `/hub`, `/test`, `/tri`, `/social`), dossier `server/jobs/atelier/`, bloc `atelier:` et champs des fichiers.

Les lieux du studio :

| Nom | Adresse | Ce qu'on y fait | Ancien nom |
|---|---|---|---|
| Studio | `/` | L'accueil. | |
| Production | `/atelier` | Un projet, du script a la video montee. Quatre etapes par temps : Preparation, Decoupage (les scenes), Tournage (images et clips), Montage. | Atelier |
| Casting | `/atelier#/persos` | Les personnages et leurs fiches de casting. | Personnages |
| Materiel | `/hub` | Modeles et LoRA : les chercher, les retenir, les charger. Leurs reglages (force, mots, LoRA par defaut de chaque temps) : `/atelier#/loras`. | Hub, Bibliotheque de LoRA |
| Essais | `/test` | Essais d'image hors projet. | Test |
| Rushes | `/tri` | Tri de ce qui a ete tourne. | Tri |
| Diffusion | `/social` | Publications tous publics des comptes. | Reseaux |

Les metiers : le **scenariste** ecrit les scripts ; le **directeur de casting** ecrit les fiches de casting ; la
**production** (les pages et le pilote) tourne et monte ; le **proprietaire** decide, choisit les prises et valide.

Les objets :

| Terme | Sens |
|---|---|
| Projet | Une video entiere : l'idee, le pitch, les textes de publication et les quatre temps. Numerote `pNNNN`. |
| Idee | La phrase de depart, avant ecriture. |
| Pitch | Le resume du projet en une ou deux phrases, une fois l'idee retenue. |
| Temps | Une des quatre parties du projet : 1 accroche, 2 montee, 3 devoile, 4 final. |
| Scene | Une unite d'un temps : une image, un mouvement eventuel, un texte a l'ecran. |
| Script | Le fichier du scenariste, place dans `server/jobs/atelier/` : une video entiere, les quatre temps. D'anciens passages disent "depot" ou "fichier de plans". |
| Plan | La scene vue du cote du scenariste : une entree de `shots` dans son script. Un plan importe devient une scene. |
| Fiche de casting | La fiche d'un personnage, ecrite par le directeur de casting, placee dans `server/jobs/atelier/personnages/`. |
| Prise | Un resultat calcule pour une scene (image ou clip). Il peut y en avoir plusieurs ; le proprietaire choisit. Pour les images, chaque lancement en calcule trois par scene ; un controle automatique note chacune sur 10 en la comparant a la description de la scene (`pilot serie`, `server/pilot/controle.py`). Une scene dont aucune image ne depasse 4 est refaite toute seule, deux fois au plus. La mieux notee est proposee, le proprietaire garde le choix. |
| Montage | La video finale d'un temps, en versions numerotees. |
| Fiche de continuite | Ce qui ne change pas d'une image a l'autre dans un projet : lieu, tenue, coiffure, lumiere, point de vue. Bloc `continuite`. |
| Image de reference | L'image d'une scene dont les autres images du projet sont tirees par retouche. Champ `reference`. |
| Reglages des LoRA | Page `/atelier#/loras` (ancienne "bibliotheque") : les LoRA du catalogue, leur presence sur le volume, et les LoRA par defaut de chaque temps. |
| Materiel | Page `/hub` (ancien "hub") : catalogue Civitai et Hugging Face par modele de base et par categorie, LoRA retenues, chargement sur le volume, veille des modeles. |
| Categorie d'une LoRA | Ce qu'elle apporte (realisme, smartphone, peau, lumiere, pose, mouvement, vitesse, tenue, corps, nu, porno, autre). Elle fixe le premier temps ou la LoRA est admise. |
| Raccord | Lien d'une scene avec la precedente du meme temps : `coupe`, `continu` ou `arrivee`. |
| Date du personnage | Date fictive du projet : le jour ou le personnage vit la scene. Champ `date_perso`, `AAAA-MM-JJ`. |
| Contexte du moment | Une ligne libre du proprietaire sur ce que le personnage vit ces jours-la. Champ `contexte`. |
| Dates reelles | `cree` et `modifie` dans `projet.json` : quand le projet a ete cree et modifie sur le serveur. Sans effet sur le contenu. |

Ne pas dire "sequence" ni "phase" pour un temps, ni "lot" pour un projet, ni "atelier", "hub", "tri" ou "depot" pour un lieu ou un script.

## Regles
- Personnages fictifs et clairement adultes ; aucune ressemblance avec une personne reelle, aucune
  photo de personne reelle en entree (`docs/compliance.md`, regle 1).
- Plafond GPU commun a tous les lanceurs : 7,50 $ par jour (heure de Paris), applique par le pilote
  lui-meme. Au-dela, le pilote refuse de creer un pod (message "plafond GPU du jour atteint").
  Ne pas contourner : le plafond se change seulement par le proprietaire (`infra.daily_cap_usd`
  dans `persona/production.yaml`).
- **Tenue dans les temps 2, 3 et 4** : chaque `still` de ces temps dit ce qu'elle porte ou ne porte plus a cet
  instant, plan apres plan (la tenue part de celle du temps 1 et se defait). La `tenue` de la fiche de continuite ne
  vaut que pour le temps 1 : elle n'est jamais ajoutee aux temps 2 a 4. Un plan qui ne dit rien de la tenue est une faute :
  **le depot entier est refuse** (message "plan X : dans les temps 2 a 4, still dit ce qu'elle porte..."). Ecrire
  "wearing ...", "naked", "topless" ou nommer le vetement. Seul un plan en raccord `continu` en est dispense. Ne pas ecrire "nsfw" : la Production l'ajoute a chaque `still` de ces temps.
- Un seul lancement a la fois. Ne jamais redemarrer le conteneur `triage`.
- Ne rien modifier hors de `server/jobs/` (fichiers de plans de l'agent, dont `server/jobs/atelier/`).
- Verifier chaque script avant de l'annoncer : `python3 tools/triage/verifier.py <fichier>` (voir "Verifier un script").
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
au redacteur de la Production. Le redacteur de la Production, lui, n'ecrit, ne relit et n'analyse jamais les temps 3
et 4, ni une scene qui porte une LoRA reservee (categorie nu, porno ou non classee). Dans tous les
cas l'agent depose un seul fichier par video ; la page l'importe toute seule, et le proprietaire lance le calcul
depuis la page, choisit les prises et monte.

Le temps 1 porte en plus les textes de publication : `pitch` (resume en francais), `accroche`
(texte a l'ecran de la premiere seconde), `legende` (avec l'appel a l'action et la mention que le
personnage est cree par IA), `cta` (carton de fin), `hashtags`. Ils sont dans la langue du
personnage (champ `langue` de sa fiche), sans emoji (la police de montage ne les affiche pas).

Le temps 1 porte aussi `ambiance` : le fond sonore du lieu pour toute la video, en anglais, une phrase,
sans musique ni voix (la piece, deux ou trois sons precis, leur distance). Rien qui doive tomber sur un
geste : le son n'est pas synchronise a l'image. Le proprietaire le fait fabriquer depuis la page (etape
Montage, « Fabriquer les sons » : un pod de quelques minutes, environ 0,05 $, fichier
`data/audio/pNNNN_ambiance.m4a` choisi comme bande-son) ; il sert aux quatre temps.

Chaque scene peut porter `son` : le bruit de son geste, en anglais, UN seul son bref et concret, entendu de
pres, avec la matiere (`a ceramic cup set down on a wooden counter`, `a zipper pulled down slowly`). Vide
quand le geste ne fait pas de bruit (regard, sourire) : une scene sur deux environ. Jamais de voix, de
souffle ni de musique. Le redacteur l'ecrit pour les temps 1 et 2 ; aux temps 3 et 4 le proprietaire
l'ecrit a la main. Le meme bouton de l'etape Montage (« Fabriquer les sons ») fabrique sur un seul pod
l'ambiance et les bruits dont la phrase est nouvelle ou a change (`data/audio/bruits/pNNNN_sN.m4a`, 4 s,
silence du debut retire). Au montage, le bruit est pose sur l'instant ou l'image du plan bouge le plus
(difference entre images successives) ; si rien ne ressort, a une seconde du debut. C'est un calage sur le
mouvement, pas une ecoute de l'image : quand il tombe mal, le champ « Instant (s) » de la scene le fixe a
la main (`son_t`, reglage de la Production, absent des plans deposes).

Son d'apres l'image (etape Montage, « Son d'apres l'image ») : un modele (MMAudio) regarde chaque clip retenu du
temps et fabrique le son de ce qu'on y voit, cale sur l'image (`data/audio/image/<clip>.m4a`, un pod de cinq a
dix minutes, environ 0,10 $, `pilot sonimage`). La phrase `son` de la scene l'oriente quand elle existe ; elle
n'est pas necessaire. Au montage, ce son remplace le bruit du geste de la scene (case « L'utiliser au montage »,
reglage `simage` de la Production) ; l'ambiance reste en fond. Il est lie au clip : une nouvelle prise demande un
nouveau son. Licence du modele : CC BY-NC 4.0 (non commerciale), decision du proprietaire. Rien a ecrire de plus
dans un plan : `son` reste un bruit bref et concret, sans voix ni musique.

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
  ("wearing ..."), `cheveux`, `lumiere`, `pdv` (point de vue de la camera). La Production les ajoute a la fin
  de chaque `still` au moment du calcul. Consequence pour l'ecriture : **un `still` ne contient plus que le
  cadrage, la pose et l'expression** ; ne pas y repeter le lieu ni la tenue. Un champ ne contient que ce
  qui vaut pour toute la video ; ce qui change en route (elle retire une veste) reste dans les `still` et
  le champ correspondant reste vide. Un plan qui se passe ailleurs porte `libre: true`.
  **Temps 2 a 4 (modele `2026-11-14g`)** : la `tenue` de la fiche n'est pas ajoutee, parce qu'elle se defait
  d'un plan a l'autre. Chaque `still` de ces temps dit donc ce qu'elle porte a cet instant. La Production ajoute
  aussi "nsfw" a la fin de chaque `still` de ces temps (plans `libre` compris) : ne pas l'ecrire soi-meme.
  Le `pdv` decrit la vue, jamais l'appareil comme un objet : "shot straight on at chest height on a phone",
  pas "phone propped on the counter, filming her" (le telephone serait dessine dans l'image).
- **Image de reference** (`reference`, au projet) : une fois choisie, les autres images sont fabriquees a
  partir d'elle par retouche (meme personne, meme piece, meme tenue, nouvelle pose). Prendre le plan le
  plus large, celui qui montre le mieux le lieu et la tenue. Une retouche garde le cadrage de la reference,
  quoi que dise le `still`. Un plan dont le `still` contient "close-up" est donc tire a part (description et
  fiche de continuite, sans la reference) : ecrire ce mot tel quel pour obtenir un gros plan. Les plans `libre` et ceux qui portent des
  LoRA supplementaires gardent leur propre tirage. Dans les temps 2 a 4, la retouche ne garde pas la tenue de la
  reference : elle prend celle que decrit le `still` (champ de pilote `tenue_libre`, pose par la Production).
- **Tirage des images d'un temps** (`tirage`, au projet, regle par le proprietaire dans la fiche de continuite ;
  ce n'est pas un champ de plan) : `ref` = images tirees de la reference par retouche, `direct` = chaque image creee
  a part (LoRA du visage, description et fiche de continuite). Par defaut `ref` aux temps 1 et 2, `direct` aux temps
  3 et 4 : une retouche garde trop la tenue et la pose de la reference pour un temps ou elle se deshabille. En tirage
  `direct`, le `still` doit donc dire le lieu en plus de la tenue si la fiche ne suffit pas.
  Les images creees a part d'un meme temps partent du meme tirage (`graines`, au projet, un nombre par temps, fixe
  a la premiere image du temps) : le decor bouge moins d'une scene a l'autre. « Autre image » tire un nouveau nombre
  pour la scene concernee seulement.
- **Raccord** (`raccord`, par plan, par rapport au plan precedent du meme temps) :
  - `coupe` (defaut) : le plan a sa propre image, le montage coupe. Pour un changement de cadrage ou d'angle.
  - `continu` : le plan n'a pas d'image propre. Son clip demarre sur la derniere image du clip precedent et
    le montage colle les deux sans coupe visible. A utiliser quand deux gestes se suivent dans le meme
    cadre ("elle sourit" puis "elle se penche"). Le `motion` reprend la ou le precedent s'arrete. La derive
    s'accumule : deux plans continus de suite au plus. `still` reste obligatoire (il decrit l'image attendue).
  - `arrivee` : le clip precedent se termine exactement sur l'image de ce plan (cout double pour ce clip).
    Pour amener un mouvement de camera ou de pose vers un cadre precis.
  Le premier plan d'un temps est toujours une coupe.
- **Le decoupage se dit, plan par plan.** Tout plan en raccord `coupe` porte `camera`, et `transition` sauf le
  premier plan du temps. Il n'y a pas de valeur par defaut : un plan sans effet ecrit `transition: coupe` et
  `camera: fixe`. Un depot qui ne le dit pas est refuse. Un plan en raccord `continu` ou `arrivee` n'ecrit ni l'un ni l'autre.
- **Transition** (`transition`) : comment on arrive sur ce plan depuis le precedent. Fabriquee au montage, sans calcul ni cout.
  - `coupe` : coupe franche, le cas courant ;
  - `fondu` (0,35 s) : le temps passe, on retrouve le personnage plus tard ; `fondu_lent` (0,9 s) : longue pause,
    moment calme. Les deux plans doivent durer plus de 2 s ;
  - `filage` (0,2 s) : la camera part tres vite vers la droite, comme une main qui tourne le telephone, dans un flou
    de mouvement. `filage_gauche`, `filage_haut`, `filage_bas` : les autres sens. Pour changer de lieu, d'angle ou de
    moment en gardant du rythme. Choisir le sens d'apres l'image : vers le bas si le plan suivant montre plus bas
    (visage puis jambes), vers le cote ou elle regarde ou se deplace ;
  - `glisse`, `glisse_gauche` (0,6 s) : le meme passage, lent et net, d'une image a l'autre. Pour un moment calme ;
  - `zoom` : la fin du plan precedent avance vite dans l'image (0,3 s), puis fondu tres court. Pour arriver sur un
    plan plus serre (plan large puis gros plan) ;
  - `dezoom` : le plan arrive de tres pres et recule vite (0,3 s). Pour arriver sur un plan plus large (gros plan
    puis plan large : on decouvre).
- **Camera** (`camera`) : ce que fait la camera pendant le plan, fabrique au montage par recadrage.
  - `fixe` ;
  - lent, sur toute la duree du plan (8 % de l'image) : `avance` (la tension monte, on s'approche d'elle), `recul`
    (on decouvre le decor ou la tenue), `gauche`, `droite` (glissement lateral, plan d'ambiance), `haut`, `bas` (la
    camera monte ou descend le long du corps) ;
  - vif, en une demi-seconde au debut du plan (18 %) : `avance_vif` (coup de zoom : souligne une reaction, une
    chute), `recul_vif`. Un seul par video.
  Dans un groupe de plans en raccord sans coupe, le mouvement est celui du premier plan et dure tout le groupe.
- **Un vrai mouvement de camera d'un plan a l'autre** (la camera tourne autour d'elle, s'approche jusqu'au cadre
  suivant) ne se fabrique pas au montage : c'est le raccord `arrivee`, ou le modele video relie les deux images (cout
  double pour ce clip). A reserver a un passage par video.
- **Penser le decoupage en ecrivant les plans** : decider pour chaque plan comment on y arrive et si la camera bouge.
  Reperes : la plupart des passages restent des coupes franches ; une ou deux transitions marquees (`filage`, `zoom`)
  par temps, la ou la video bascule (changement de lieu, passage au gros plan, chute) ; une camera qui bouge sur un
  plan sur deux au plus, de preference `avance` sur le plan le plus fort ; alterner les cadrages d'un plan au suivant
  (large, moyen, serre) pour que la transition ait quelque chose a relier, et dire ce cadrage dans `still` avec les
  mots que le controle lit ("wide shot" ou "full-body shot", "medium shot", "close-up"). Ne jamais ecrire un mouvement de camera
  dans `motion` (zoom, pan, travelling) : le modele video le rate, alors que `camera` le rend a coup sur.

## Controle des plans
La Production relit chaque depot et chaque projet avant tout calcul, sans GPU (`tools/triage/controle.py`), et
affiche ses remarques dans la page (nombre de remarques sur la ligne du depot, detail dans le projet).
Rien n'est bloque, mais un depot sans remarque est l'objectif. Ce qui est verifie :
- fiche de continuite remplie (lieu, tenue, point de vue) ; tenue non repetee dans les `still` du temps 1, tenue decrite dans chaque `still` des temps 2 a 4 ; heure du
  `still` coherente avec la fiche ;
- point de vue respecte : si un telephone filme, il n'est pas dans sa main ; le `pdv` ne decrit pas
  l'appareil comme un objet pose quelque part ;
- premier plan du temps 1 : un `motion` et un texte d'accroche ;
- un seul geste par `motion`, aucun mouvement de camera, aucun geste de la liste des gestes qui ratent ;
- `texte` de 7 mots au plus, sans emoji ;
- progression : chaque plan porte `cran`, de 1 (anodin) a 5 (le plus ose de ce temps), qui ne redescend pas ;
- duree : le temps 1 vise 20 s au plus (un clip dure 5 s) ;
- raccords possibles (un plan continu suit un plan qui a un `motion` ; pas trois continus de suite) ;
- `transition` et `camera` places la ou ils ont un effet (pas sur le premier plan pour la transition, pas sur un plan
  en raccord sans coupe), pas trop de transitions marquees, un seul mouvement vif ; `zoom` vers un cadre plus serre et
  `dezoom` vers un cadre plus large ; un temps de plus de trois plans sans aucun mouvement est signale comme plat.

Lire la fiche et l'image de reference du projet dans `projet.json` (`continuite`, `reference`) avant
d'ecrire les temps 2, 3 et 4 : elles s'appliquent a eux aussi.

## Relecture des images
Apres les images et avant les clips, le redacteur IA relit les images retenues des temps 1 et 2 (bouton
"Relire les images", ou d'office a la pause de la chaine) : meme personne, lieu et tenue de la fiche, defauts
d'anatomie, image conforme au `still`, pose d'ou le `motion` peut partir, place pour le texte. Ses remarques
s'affichent sous chaque image et valent tant que l'image retenue est celle relue. Les temps 3 et 4 et les plans
qui portent une LoRA reservee (nu, porno, non classee) ne sont jamais relus : leur verification reste au proprietaire.

## LoRA supplementaires et bibliotheque
Les LoRA supplementaires (hors LoRA du personnage) se gerent dans la page `/atelier#/loras` :

- **Catalogue** : chaque LoRA a un nom court (celui qu'on ecrit dans `loras`), un fichier `.safetensors`, une force
  conseillee, des mots declencheurs et une note du proprietaire. Il se lit dans `persona/production.yaml`
  (`lora_catalog`) et `server/data/lora_catalog.yaml`, ou par `docker compose run --rm pilot lora list`.
- **Mots declencheurs** : le pilote les ajoute d'office a la fin du prompt d'image. Ne pas les recopier dans `still`.
- **Force** : `loras: [nom]` prend la force conseillee ; `loras: [{name: nom, strength: 0.6}]` la remplace.
- **Categorie et temps (modele `2026-11-14h`)** : chaque LoRA a une categorie, qui fixe le premier temps ou elle est
  admise. Des le temps 1 : realisme, smartphone, peau, lumiere, pose, mouvement, vitesse. Des le temps 2 : tenue, corps.
  Temps 3 et 4 : nu. Temps 4 : porno. Une LoRA non classee (`autre`) n'est admise qu'aux temps 3 et 4. Un depot dont un
  plan nomme une LoRA trop tot est **refuse a l'import** ; le lancement d'un calcul aussi. Les categories et les LoRA
  chargees se lisent dans `/hub` (onglet « Notre liste ») ; le champ `cat` figure dans le catalogue.
- **LoRA video** : une LoRA de la famille Wan 2.2 (`famille: wan22` au catalogue) nommee dans `loras` s'applique au clip
  du plan, pas a son image. Les autres s'appliquent a l'image ; une image qui porte une LoRA d'image est tiree
  directement, sans retouche depuis l'image de reference.
- **LoRA par defaut d'un temps** (modele `2026-11-15c`) : le proprietaire en fixe pour chaque temps dans la
  Bibliotheque de LoRA (une d'image, une de clip). Elles sont posees dans les « LoRA de ce temps » de tout nouveau
  projet, et d'un projet existant au premier depot de ce temps (`lora_def` du projet note les temps deja servis) ; il
  les retire ensuite s'il veut. Elles valent pour toutes les scenes du temps : le `loras` d'un plan s'y **ajoute**, et
  `loras: []` ne les retire pas. Le scenariste n'a donc rien a ecrire pour elles. Le controle des plans signale un
  temps 4 sans LoRA porno d'image ou de clip (grave, sans bloquer le calcul) et un temps 3 sans LoRA de nu d'image (rien n'est demande pour le clip au temps 3).
- **LoRA du projet et d'un temps** (`loras` au projet : `"0"` = tout le projet, `"1"` a `"4"` = un temps ; choisies
  par le proprietaire dans la section LoRA de la page, ce n'est pas un champ de plan). Au calcul (images et clips),
  une scene recoit celles du projet, puis de son temps, puis les siennes ; pour un meme nom la derniere force
  l'emporte. Une LoRA que sa categorie n'admet pas a ce temps est laissee de cote. Le `loras` d'un plan sert donc
  rarement : seulement pour une LoRA propre a une scene. Les mots declencheurs du catalogue sont ajoutes par le
  pilote (a l'image, ou au mouvement pour une LoRA video) : ne pas les ecrire dans le plan.
  Une LoRA n'est jamais chargee d'apres ce que dit la description : seulement si elle est nommee.
- **Verdict du proprietaire** : sous chaque image retenue, des cases (bonne, tenue fausse, geste absent, objet en
  trop, visage, corps, decor, cadrage), gardees dans `verdicts.json` du projet (`{image: [codes]}`, rendu par
  `/api/a/projet` sous `verdicts`). Des codes, pas de texte : ils se lisent sans voir l'image, temps 3 et 4 compris.
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
pour juger raccords et textes. Une transition recouvre la fin d'un plan et le debut du suivant (0,2 a 0,35 s) : ne pas
y placer un geste ni un texte important. Elle est remplacee par une coupe si l'un des deux plans dure moins d'une seconde.

## Livrer un script a la Production
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
         projet: ""           # "" ou absent : nouvelle video, la page ouvre son projet ; pNNNN : projet existant
         personnage: lea      # seulement pour un nouveau projet
         titre: ""            # seulement pour un nouveau projet
         note: "une ligne pour le proprietaire"
         # pas de "temps" ici : chaque plan dit le sien
         # facultatifs, lus si le fichier porte des plans du temps 1 (un champ vide garde celui du projet) :
         pitch: ""
         accroche: ""
         legende: ""
         cta: ""
         hashtags: ""
         ambiance: ""               # fond sonore du lieu, une phrase en anglais, sans musique ni voix
         # facultatifs (absents : ceux du projet sont gardes) :
         date_perso: "2026-12-19"   # date du personnage, fictive, entre guillemets
         contexte: ""               # contexte du moment, une ligne en francais
         continuite:                # ecrite une fois pour les quatre temps ; voir "Continuite et raccords"
           lieu: "in ..."
           tenue: "wearing ..."
           cheveux: ""
           lumiere: "..."
           pdv: "..."
         reference: plan01          # nom d'un plan du temps 1 de ce fichier
         garder:                    # facultatif : tenues et lieux nouveaux a garder dans la fiche du personnage
           tenues: ["robe rouge a fines bretelles | wearing a red slip dress with thin straps"]
           lieux: []
       defaults:
         seed: 100
         # loras: [nom]       # noms du catalogue ; s'ajoutent aux LoRA par defaut du temps, posees sur le projet
       shots:
         - name: plan01       # unique dans le fichier, lettres, chiffres et _
           temps: 1           # obligatoire : 1, 2, 3 ou 4 (voir "Un projet en quatre temps") ; plans dans l'ordre des temps
           titre: "..."       # nom de la scene dans la page (facultatif)
           still: "..."       # obligatoire
           motion: "She ..."  # facultatif : sans lui, la scene reste une image fixe
           texte: ""          # texte incruste au montage (facultatif)
           raccord: coupe     # coupe, continu ou arrivee (facultatif)
           transition: coupe  # obligatoire sauf premier plan et raccord sans coupe : coupe, fondu, fondu_lent, filage,
                              # filage_gauche, filage_haut, filage_bas, glisse, glisse_gauche, zoom, dezoom
           camera: fixe       # obligatoire sauf raccord sans coupe : fixe, avance, recul, gauche, droite, haut, bas,
                              # avance_vif, recul_vif (voir "Continuite et raccords")
           cran: 1            # 1 a 5, ne redescend pas (voir "Controle des plans")
           pose:              # facultatif : la pose decomposee (position, appui, bassin, genoux, mains, regard)
             mains: "right hand in her hair"
           contact: ""        # facultatif : ce que son corps touche et ou
           autres: ""         # facultatif : les autres personnes visibles a l'image ; vide quand elle est seule

   Champs repris par plan : `name`, `still`, `motion`, `end_edit`, `tattoos`, `loras`, `seed`,
   `temps`, `titre`, `texte`, `voix`, `son`, `role`, `raccord`, `transition`, `camera`, `libre`, `cran`, `pose`, `contact`, `autres`. 30 plans au plus par fichier, 10 par temps. `steps`, `image`,
   `edit`, `suite_de`, `end_image` et `character` ne sont pas repris (un depot qui en porte est refuse) ; `body` et `dest` sont inutiles (le temps et la fiche du personnage en
   tiennent lieu).
   **Une video, un fichier** (modele `2026-11-15e`) : les quatre temps, ou ceux qui sont demandes, dans le meme
   fichier. Chaque plan dit son `temps` et les plans se suivent dans l'ordre des temps ; chaque temps est une video a
   part, donc son premier plan n'a pas de `transition` et un raccord ne traverse pas deux temps. Une video nouvelle ne
   nomme pas de `projet` (elle porte `personnage` et `titre`) : la page ouvre le projet. Ne jamais deviner un numero
   de projet. L'ancienne forme (un fichier par temps, avec `atelier.temps` et `projet_de`) reste lue, mais ne
   s'importe pas toute seule : ne plus l'ecrire.
   Date du personnage : pour un nouveau projet, la mettre dans le fichier (celle donnee par
   le proprietaire) ; sans elle, la page prend le jour de l'import. Pour un projet existant, ne pas la
   remettre : celle du projet fait foi. Une date mal formee bloque le depot.
3. **Ne pas lancer le pilote sur ce fichier.** Un fichier accepte est importe par la page toute seule, sans bouton,
   des que le proprietaire l'ouvre et qu'aucun calcul ne tourne : les plans deviennent les scenes de leur temps. Un
   fichier refuse n'ouvre rien : il reste affiche a l'accueil de la Production avec sa raison (bloc `atelier` absent,
   `temps` invalide, nom en double, `still` manquant, decoupage non dit, date mal formee). Le verificateur dit la meme
   chose avant : ne jamais annoncer un fichier qu'il refuse.
4. **Corriger** : modifier le meme fichier, sans changer les `name`. La page reprend le fichier toute seule ; les
   scenes sont remplacees une a une, et l'image deja calculee est gardee tant que `still` n'a pas change. Un plan
   retire du fichier quitte le projet. Ce que le proprietaire regle dans la page et que le fichier ne dit pas reste
   en place (ses LoRA, ses prises choisies).
   Les textes de publication remplis dans le fichier remplacent ceux du projet a chaque import.

## Pose decomposee et retour du controle
Modele `2026-11-15b`. Un plan peut porter, en plus de `still`, les champs facultatifs `pose` (`position`, `appui`,
`bassin`, `genoux`, `mains`, `regard`), `contact` et `autres`, en anglais, une courte phrase chacun. Un champ rempli est
ajoute a la description envoyee au modele d'image (la pose en tete, `autres` a la fin), puis verifie a part par le controle automatique (une question
oui/non par champ). Ne remplir que ce qui compte pour le plan et ne pas le redire dans `still`. Les champs aident a
verifier ; ils ne forcent pas le modele d'image.

`autres` decrit les autres personnes visibles a l'image (qui, ou, quelle partie du corps). Vide dans le cas courant :
elle est seule, et le controle signale toute autre personne. Ne pas le remplir pour quelqu'un qui reste hors champ.
Toute personne decrite est adulte et fictive (`docs/compliance.md`).

Tenues et lieux nouveaux (`atelier.garder`, modele `2026-11-15f`). Les listes `tenues` et `lieux` de la fiche du
personnage sont sa garde-robe et ses lieux de vie : on y pioche, mais une discussion peut en inventer d'autres, et
rien ne l'interdit. Une tenue d'un jour reste dans le script. Une tenue ou un lieu qui doit revenir se declare dans
`garder`, sous la forme de la fiche (`francais | anglais`), avec en anglais exactement les mots utilises dans la
fiche de continuite ou les `still`. La page le montre au proprietaire une fois une image retenue (« A garder pour
... ? ») ; d'un appui il l'ajoute a la fiche du personnage, ou l'ecarte. Le scenariste ne modifie jamais la fiche
lui-meme. Une ligne deja dans la fiche n'est pas reproposee. A la video suivante, la tenue se reprend dans la fiche,
mot pour mot : pour le modele d'image, d'autres mots font un autre vetement.

Le retour de tournage, a lire avant d'ecrire la video suivante :

    python3 tools/triage/verifier.py --retour            # chaque script importe, en une ligne
    python3 tools/triage/verifier.py --retour mavideo    # le detail du script mavideo.yaml, scene par scene
    python3 tools/triage/verifier.py --notes pNNNN       # le meme detail pour un projet entier

La ligne d'un script : nombre de scenes, images retenues, clips faits, scenes refaites, note moyenne. Par scene : le
nombre d'images faites (plus d'une : la scene a ete refaite), si une image est retenue et un clip fait, la note de
l'image retenue (sinon la mieux notee), les points douteux ou absents (decor, tenue, geste, objet, cadrage, chaque
champ de pose) et les cases cochees par le proprietaire. Aucun texte libre : des valeurs fermees et des nombres.
Toujours a jour : la commande lit les donnees du moment, il n'y a pas de fichier a attendre.

## Verifier un script
Avant d'annoncer un fichier au proprietaire, le passer au verificateur (sur le serveur, compte `debian`, sans
GPU ni IA, lecture seule) :

    cd /home/debian/Depotclaude
    python3 tools/triage/verifier.py server/jobs/atelier/<nom>.yaml [autre.yaml ...]
    python3 tools/triage/verifier.py --etat    # modeles en cours, personnages, projets

Il dit ce que la page dira : `REFUSE` (le depot ne sera pas importable), `PERIME` (la ligne `modele` n'est pas
celle du modele en cours), `GRAVE` et `remarque` (controle des plans, avec le nom du plan), ou "rien a corriger".
Code de sortie : 0 rien a corriger, 1 des remarques restent, 2 refuse ou perime. Corriger et relancer jusqu'a 0 ;
une remarque laissee expres s'explique dans `note`. Le controle des plans passe sur chaque temps du fichier.

## Livrer une fiche de casting
L'agent peut aussi creer un personnage. Il copie `server/jobs/personnage.modele.yaml` (seule reference du
format, avec sa ligne `modele` et son historique) vers `server/jobs/atelier/personnages/<nom_court>.yaml`, le
remplit et le verifie avec le meme outil. La fiche apparait dans la page Production, Casting, sous "Fiches livrees
par votre directeur de casting" (et un rappel a l'accueil) : le proprietaire l'ouvre dans le formulaire du personnage,
la corrige et l'enregistre. Rien n'entre en service sans lui ; une fiche de moins de 21 ans est refusee.
`generation.lora` reste vide : la LoRA du visage est entrainee par le proprietaire, et sans elle le visage change
d'une image a l'autre. Le nom court du fichier est celui qu'on ecrit ensuite dans `atelier.personnage`.

## Skills de l'agent
`agents/girls-ai-scenariste/SKILL.md` et `agents/girls-ai-casting/SKILL.md` : deux skills a installer dans
l'agent du proprietaire (par un lien vers ces dossiers). Ils ne contiennent pas le format : ils imposent de
relire a chaque seance ce document, `server/jobs/modele.yaml` et `server/jobs/personnage.modele.yaml`, puis de
verifier avant de livrer. Une evolution du format se fait donc ici et dans les modeles, pas dans les skills.

Les fichiers de `server/jobs/atelier/` ne sont pas suivis par git. Le lancement direct du pilote
(ci-dessous) reste possible pour des essais hors Production : ces images vont dans les Rushes, pas dans un projet.

## Commandes (depuis `/home/debian/Depotclaude/server`)
    docker compose run --rm pilot depenses                            # depense du jour / plafond
    docker compose run --rm pilot run jobs/<plan>.yaml --stills-only  # images seules
    docker compose run --rm pilot run jobs/<plan>.yaml                # images puis clips (plans avec "motion")
    docker compose run --rm pilot lora list                           # LoRA supplementaires disponibles
    docker compose run --rm pilot son "Quiet kitchen room tone" --nom cuisine   # ambiance sonore, rangee dans data/audio
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
