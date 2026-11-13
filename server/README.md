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
