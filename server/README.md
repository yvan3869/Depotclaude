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
`data/ecriture/` et appelle `claude -p` sans outils, avec l'abonnement Claude du compte `debian`.
Aucune cle dans le conteneur. S'il est arrete, la page bascule sur des structures types (`moteur_local.py`).

    sudo cp server/writer/girls-ai-writer.service /etc/systemd/system/
    sudo systemctl daemon-reload && sudo systemctl enable --now girls-ai-writer
    journalctl -u girls-ai-writer -n 20

### Trois temps et plans deposes par un agent (14/11/2026)
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
