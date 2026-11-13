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
`/home/debian/kb/perso/girls-ai`. Mise a jour automatique toutes les heures :
```bash
(crontab -l 2>/dev/null; echo "17 * * * * $HOME/Depotclaude/server/sync_kb.sh >> $HOME/sync_kb.log 2>&1") | crontab -
```
