# Installation sur le serveur Oracle

Non teste sur le serveur : verifier chaque etape. Rien ici ne touche a nginx,
PostgreSQL, hermes ou openclaw ; seul le port 8790 de l'adresse Tailscale est utilise.

```bash
git clone git@github.com:yvan3869/Depotclaude.git && cd Depotclaude
git checkout claude/synthetic-artificial-woman-xmbnp0
cd server && cp .env.example .env
sed -i "s/^TRIAGE_TOKEN=.*/TRIAGE_TOKEN=$(openssl rand -hex 24)/" .env
mkdir -p data/inbox && docker compose up -d
grep TRIAGE_TOKEN .env    # jeton a mettre dans l'adresse
```
Interface de tri : `http://100.127.244.10:8790/?t=<jeton>` depuis un appareil du reseau Tailscale.
Les fichiers a trier se deposent dans `server/data/inbox`.

Arret : `docker compose down`. A venir : pilote GPU, montage, publication.

## Base de connaissances
`server/sync_kb.sh` copie le journal, l'architecture, la conformite et les comptes vers
`/home/debian/kb/perso/girls-ai`. Mise a jour horaire par un minuteur systemd nomme
`kb-docs-sync-girls-ai` (service + timer dans `/etc/systemd/system`). Le serveur heberge
d'autres services lies a la base : ne jamais creer d'unite sans verifier que le nom est libre.

## Pilote GPU
Lancement manuel d'un fichier de plans (les clips arrivent dans `data/inbox`, donc dans le tri) :
```bash
cd ~/Depotclaude/server && git pull
docker compose run --rm pilot run jobs/exemple.yaml
```
Autres commandes : `pilot pods` (liste les pods du compte), `pilot reap` (supprime les pods
du projet restes allumes trop longtemps). Le pilote supprime son pod en fin de session ; `reap`
est le filet de securite si le pilote est interrompu brutalement.

## Formulaire "Nouveau lot" (trois temps)
Dans l'interface de tri, le lien "Nouveau lot" (adresse `/nouveau`) ouvre un formulaire : decor et
tenue communs, puis trois temps (accroche tous publics, montee pour les abonnes, final prive en champ
libre). Il ecrit un fichier de plans dans `DATA_DIR/jobs/` et affiche la commande a lancer :

    docker compose run --rm pilot run /data/jobs/<nom>.yaml

Le formulaire ne lance pas le pod lui-meme : la cle RunPod reste dans le conteneur du pilote.
Apres un `git pull`, redemarrer l'interface : `docker compose restart triage`.

Le formulaire accepte le francais. Champs facultatifs : "Image de fin" (clip debut/fin, voir
`jobs/exemple_debut_fin.yaml`) et "LoRA supplementaires" (noms de `lora_catalog`, voir
`docs/lora-supplementaires.md`).

## Studio : menu, page Test, scenes en sous-scenes (14/11/2026)
L'adresse de l'interface ouvre maintenant un menu : Tri (`/tri`), Plan (`/nouveau`), Test (`/test`).
Mise a jour : `git pull` puis `docker compose up -d --build triage` (l'interface utilise desormais
la meme image que le pilote, car la page Test lance le pilote elle-meme).

Page Test : listes a cocher (decor, cadrage, poses, tenue, expression, lumiere), champs libres
(corps, complement), LoRA du catalogue avec force reglable, nombre d'images. Chaque image tire au
hasard un element de chaque liste cochee. Les listes de base sont tous publics a suggestif ; les
elements que vous ajoutez dans l'interface sont enregistres dans `data/listes_perso.json`.
Les tests sont ranges dans `data/tests/<date>/` : images, descriptions, journal. Un test peut etre
marque OK ou pas OK, annote, repris, supprime. Un reglage marque OK se rappelle dans la page Plan.
Un seul test a la fois. Le premier test demarre un pod (2 a 5 min) ; les suivants le reutilisent
(quelques secondes). Le pod s'arrete seul apres 10 minutes sans test ; la page affiche son etat,
son cout en cours et un bouton "Arreter le pod". Son nom commence par `girls-ai-studio-` : le
service `girls-ai-pod-reaper` le supprime de toute facon au-dela de 105 minutes d'age.

Page Plan : dans le champ Mouvement, plusieurs actions separees par "puis" ou ";" deviennent des
sous-scenes : pour chacune, le pilote fabrique l'image de fin a partir de la precedente, calcule un
clip debut/fin, puis met les clips bout a bout. Une action par sous-scene, sans changement de cadrage.

## Plafond de depense GPU (14/11/2026)
Toute creation de pod (pilote, page Test, `lora add`) passe par un controle : si la depense du jour
(heure de Paris) atteint `infra.daily_cap_usd` (7,50 $ dans `persona/production.yaml`), le pod
n'est pas cree. Registre : `data/depenses.jsonl` (creation et suppression de chaque pod, tarif).
Depense du jour : `docker compose run --rm pilot depenses`. Fiche pour un agent tiers : `docs/agents.md`.

## Atelier : de l'idee a la video montee (14/11/2026)
Page `/atelier` du studio (`tools/triage/atelier.py`, `atelier.html`). Tout se fait depuis le telephone.

- **Personnages** : une fiche par personnage (identite, voix, maniere de seduire, lieux, tenues, ton,
  reglages d'image). Modeles dans `persona/personnages/<slug>.json` ; les modifications faites dans la
  page vont dans `data/personnages/`. Age minimal 21 ans, refuse en dessous.
- **Projets** (`data/projets/pNNNN/`) : idee, scenario, textes, scenes, prises, montages.
- **Ecriture** : idees, scenario complet (accroche, legende, carton de fin, scenes avec image, mouvement,
  texte a l'ecran, voix off), retouche sur consigne, reecriture d'une scene, variantes de legende, fiche
  de personnage. Registre suggestif uniquement ; l'explicite reste dans les champs libres du proprietaire.
- **Production** : images (pod de veille) puis clips (pod propre au lancement), devis affiche, plafond
  du jour applique par le pilote. Une nouvelle prise ne remplace pas l'ancienne : on choisit.
- **Montage** (ffmpeg, sans GPU) : clips ou images fixes en zoom lent, textes incrustes, carton de fin
  floute avec l'appel a l'action, coupe ou fondu, musique deposee dans `data/audio/`. Versions `final_vN.mp4`.

Redacteur IA : service hote `girls-ai-writer` (`server/writer/`), qui lit les demandes dans
`data/ecriture/` et appelle `claude -p` sans outils ni connecteurs (`--tools "" --strict-mcp-config`), avec
l'abonnement Claude du compte `debian`. Apres une modification de `girls_ai_writer.py` :
`sudo systemctl restart girls-ai-writer`.
Aucune cle dans le conteneur. S'il est arrete, la page bascule sur des structures types (`moteur_local.py`).

    sudo cp server/writer/girls-ai-writer.service /etc/systemd/system/
    sudo systemctl daemon-reload && sudo systemctl enable --now girls-ai-writer
    journalctl -u girls-ai-writer -n 20

### Trois temps et plans deposes par un agent (14/11/2026 ; quatre temps depuis : voir plus bas)
Un projet porte maintenant trois temps, en onglets : 1 accroche tous publics, 2 montee pour les abonnes,
3 final prive. Chaque temps a ses scenes, son devis, sa production et son montage (`final_vN.mp4`,
`final_t2_vN.mp4`, `final_t3_vN.mp4`). Le redacteur IA ecrit le temps 1 et, sur demande, le temps 2
(meme lieu, meme tenue, suggestif) ; il n'ecrit jamais le temps 3, rempli a la main ou par import.
Un agent tiers depose ses plans dans `server/jobs/atelier/<nom>.yaml` (bloc `atelier` : projet, temps) ;
la page les affiche, avec leurs erreurs, et le bouton "Importer dans le projet" en fait des scenes.
Un depot du temps 1 peut porter les textes de publication (pitch, accroche, legende, cta, hashtags).
Les plans importes ne sont pas ecrases par le redacteur. Marche a suivre de l'agent : `docs/agents.md`.
Date du personnage : chaque projet porte une date fictive (`date_perso`, le jour ou le personnage vit la
scene, a choisir proche du jour de publication) et un contexte du moment. Le redacteur en tire la saison,
le jour de la semaine et les fetes proches, pour l'idee, la tenue, la lumiere et les textes ; il voit aussi
les projets voisins du personnage. La liste des projets suit cette date. `cree` et `modifie` restent les
dates reelles du serveur. Un depot du temps 1 peut porter `date_perso` et `contexte`.
Vocabulaire commun a la page et a l'agent (projet, idee, pitch, temps, scene, plan, depot, prise, montage) :
tableau en tete de `docs/agents.md`.
Production en chaine : le panneau "Production en chaine" d'un projet enchaine, pour les temps coches, les images
(un seul lancement), puis pour chaque temps les clips et le montage. Deux deroulements : avec pause apres les images
(par defaut, pour choisir les prises ; "Continuer" lance la suite) ou d'une traite. Seul ce qui manque est calcule,
sauf "Tout refaire" (nouvelles prises, anciennes gardees). Le devis est affiche avant le lancement et refuse s'il
depasse le reste du plafond du jour. Le bouton "Tout produire pour ce temps" fait la meme chose pour un seul temps.
L'etat de la chaine est en memoire : un redemarrage de `triage` l'arrete (et laisse orphelin le pod d'un calcul en
cours). Un depot du temps 1 sans idee remplit le champ "Idee" avec son pitch.

### Continuite et raccords (14/11/2026)
Trois reglages par projet pour qu'une video garde le meme lieu, la meme tenue et la meme personne.
- **Fiche de continuite** (panneau "Continuite") : lieu, tenue, coiffure, lumiere, point de vue, en anglais. Elle est
  ajoutee a la description de chaque image au moment du calcul ; les scenes ne decrivent plus que le cadrage, la pose
  et l'expression. Le redacteur IA la remplit avec le scenario. Une scene "libre" (case dans ses details) l'ignore.
- **Image de reference** : une scene choisie dans le meme panneau. Les autres images sont tirees de la sienne par
  retouche (Qwen-Edit : meme personne, meme piece, meme tenue, nouvelle pose) au lieu d'un nouveau tirage. Les scenes
  libres ou avec LoRA gardent leur tirage. Changer de reference ne refait pas les images deja calculees.
- **Raccord** de chaque scene avec la precedente : "coupe" (image propre), "continu" (pas d'image : le clip part de la
  derniere image du clip precedent ; au montage les deux clips sont colles, l'image en double retiree, jamais de fondu
  entre eux), "arrivee" (le clip precedent finit sur l'image de cette scene, clip debut/fin). Refaire le clip d'amont
  rend le clip continu "a refaire" : la page le dit et le bouton "Creer les clips manquants" le reprend. Une jointure
  n'est propre que si la fin du clip d'amont et le debut du clip continu ne sont pas rognes.
Pilote : champs de plan `edit` (avec `image`), `suite_de`, `end_image` (`server/jobs/modele.yaml`, modele 2026-11-14e).
Controle des plans (14/11/2026) : chaque projet et chaque depot est relu avant calcul par `tools/triage/controle.py`
(regles fixes, sans GPU ni IA) : fiche de continuite, point de vue, premier plan, un geste par clip, texte a l'ecran,
progression (`cran` de 1 a 5 par scene), duree, raccords. Les remarques s'affichent au-dessus de "Images et clips" ;
elles ne bloquent rien.

Relecture des images (14/11/2026) : apres les images, le redacteur IA relit les images retenues des temps 1 et 2
(`relire()` dans `atelier.py`, bouton "Relire les images", d'office a la pause de la chaine). Les images, reduites
en JPEG, voyagent dans la demande elle-meme ; le service les joint au message, toujours sans outil. Resultat dans
`data/projets/<id>/relecture.json`. Jamais les temps 3 et 4 ni les scenes a LoRA supplementaires.

Montage (14/11/2026) : `monter()` dans `atelier.py`. Duree visee (15, 20 ou 30 s) : les plans sont raccourcis en
proportion, 2 s au moins chacun, jamais du cote d'un raccord colle ni sur une duree reglee a la main. Sur la premiere
scene l'accroche s'affiche d'abord, le texte de la scene ensuite (jamais deux textes a la fois). L'accroche est calee
en haut de l'image, au-dessus de la tete : deux lignes au plus, la police retrecit pour y tenir (44 caracteres conseilles). Fin en fondu au noir.
La mention "AI character" est toujours incrustee sur le temps 1 (facultative sur les autres temps). Chaque montage
laisse sa fiche dans `data/projets/<id>/finals.json` (duree, debut de chaque plan, raccords colles, prises montees).
"Valider pour publication" est refuse s'il n'y a pas de video ou si la derniere ne porte pas la mention ; la page
avertit aussi quand la video ne correspond plus aux prises retenues, dure plus de 21 s, ou n'a ni legende ni carton.
Textes sans fond en aplat : blanc sur ombre douce, trois styles au choix dans le panneau Montage (doux, contour,
serif ; polices sous licence OFL dans `tools/triage/polices/`). Mention IA plus petite, a 60 % d'opacite. Une scene sans
clip dure 2 s en zoom lent. Raccord sans coupe : les couleurs du clip suivant sont alignees sur la fin du precedent et la
jointure passe par un fondu de 4 images.

Planche de controle (14/11/2026) : apres chaque montage, `planche()` extrait de la video les images que regarde
l'analyste (debut, milieu de chaque scene, avant et apres chaque jointure, fin) et les range cote a cote dans
`planche_<version>.jpg`, affichee sous la video. Sans IA ni GPU, pour tous les temps. Bouton "Creer la planche de
controle" pour une video montee avant cette date.

Analyse du montage (14/11/2026) : bouton "Analyser la video" sous la video montee des temps 1 et 2 (`analyser()`).
Des images sont extraites de la video (debut, milieu de chaque scene, avant et apres chaque jointure, fin) et envoyees
au redacteur IA avec la fiche du montage et le scenario ; il rend un verdict et six points au plus, chacun avec une
correction. Il ne voit ni le mouvement ni le son. Resultat dans `data/projets/<id>/analyse.json`. Jamais les temps 3 et 4
ni un temps qui contient une scene a LoRA supplementaires.

### Quatre temps et bibliotheque de LoRA (14/11/2026)
Un projet porte quatre temps : 1 accroche tous publics, 2 montee (suggestif pousse), 3 devoile (nudite, sans
acte), 4 final (l'ancien temps 3). Au demarrage, `_migrer()` convertit une fois chaque projet d'avant (marque
`"v": 4` dans `projet.json`) : scenes du temps 3 passees en 4, `final_t3_*` et `planche_t3_*` renommes en `_t4_`,
`finals.json`, `analyse.json`, `montage.json` et la chaine en pause (`chaine.json`) mis a jour. Un depot ecrit avec un
modele anterieur a `2026-11-14f` et `temps: 3` est lu comme temps 4. Le redacteur, le relecteur et l'analyste IA ne
recoivent jamais les temps 3 et 4.
Bibliotheque (`/atelier#/loras`, `bibliotheque()`) : le catalogue du pilote (`persona/production.yaml` puis
`data/lora_catalog.yaml`, que la page ecrit par `save_lora()`), la presence de chaque fichier sur le volume d'apres
`data/lora_volume.json` (ecrit par le pilote a chaque lancement, `inventaire()`), les fichiers du volume hors
catalogue, et les LoRA par defaut des temps 2 a 4 (`data/lora_defauts.json`, `save_defauts()`). Les defauts sont poses
sur une scene ajoutee a la main et sur un plan depose sans `loras`. Le controle (`controle.py`) signale comme grave
une LoRA absente du catalogue ou du volume. La page n'envoie aucun fichier : un `.safetensors` se depose par
`pilot lora add`.
Formulaires : chaque reglage porte une ligne d'explication ; la scene est rangee en "Ce qu'on voit", "Ce qui
s'affiche", "Place dans la video" et "Reglages avances" ; le montage en Image, Texte, Duree et fin, Son.
