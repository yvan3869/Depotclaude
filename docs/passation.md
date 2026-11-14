# Passation vers la session du serveur (14/11/2026)

Tu es Claude, lance par `claude remote-control` sur le serveur Oracle du proprietaire, dans
`/home/debian/Depotclaude` (utilisateur `debian`, branche `claude/synthetic-artificial-woman-xmbnp0`).
Tu prends la suite d'une session cloud qui ne pouvait pas acceder a ce serveur. Tout ce qui a ete
decide est dans le depot ; ce fichier est le point d'entree.

## Le proprietaire
Francophone. Reponses courtes, resultat en premier, pas de flatterie, pas d'emojis. Il veut de
l'autonomie et un cout minimal. Il est souvent sur telephone.

## A lire avant d'agir
1. `docs/feuille-de-route.md` : regles de travail et direction.
2. `docs/journal-projet.md` : faits, lecons, couts (lire au moins les lecons).
3. `server/README.md` : pile Docker, studio (tri, plan, test), pilote.
4. `docs/lora-supplementaires.md`, `docs/compliance.md`.

## Regles non negociables sur ce serveur
- Ne toucher a aucun service existant : hermes, openclaw, base de connaissances, nginx, postgres.
- Tout ce qui est cree porte `girls-ai` dans son nom ; verifier qu'un nom est libre avant.
- Les commandes systemd se lancent en root ; le depot appartient a `debian`.
- Aucun secret dans le depot ni dans la conversation : ils vivent dans `server/.env`.
- Chaque depense GPU est annoncee et plafonnee ; jamais de pod sans arret automatique.
- Ne pas redemarrer le conteneur `triage` pendant qu'un test tourne (le pod reste orphelin).

## Partage des roles sur le contenu
L'assistant construit et pilote toute la chaine et produit le contenu tous publics ou suggestif.
Les prompts et les images explicites, le choix des LoRA pour adultes et les listes de poses
explicites sont l'affaire du proprietaire, avec les outils fournis (page Test, champs libres).

## Etat au 14/11/2026
- Lea : images Z-Image-Turbo + LoRA `leamorel_zimage_v2` a 1,4 ; video Wan 2.2 I2V ; clips
  debut/fin (`end_edit`) et scenes en sous-scenes (`steps`). Langue : anglais. Fanvue : compte en
  attente de validation ; textes dans `persona/profile_texts_en.md`. Instagram : banni deux fois,
  ne pas recreer.
- Studio (port 8790 sur l'adresse Tailscale) : menu, Tri, Plan, Test. La page Test lance le pilote,
  garde un pod en veille 10 minutes, affiche les listes en francais et envoie l'anglais.
- LoRA au catalogue (`persona/production.yaml`) : deux LoRA supplementaires ajoutes par le proprietaire.
- Hrafnvik (autre projet, dossier `hrafnvik/`) : planches des trois personnages livrees.

## A faire en arrivant
1. `git pull`, puis dans `server/` : `docker compose up -d --build triage` (l'interface utilise
   desormais l'image du pilote). Verifier `docker compose logs --tail 20 triage` et que la page repond.
2. Verifier que `server/.env` contient `RUNPOD_API_KEY` et, pour `pilot lora add`, `CIVITAI_TOKEN`
   (demander au proprietaire de les saisir lui-meme s'ils manquent).
3. Verifier que le service `girls-ai-pod-reaper` tourne toujours (`systemctl list-timers | grep girls-ai`).

## Points ouverts connus
- Trace de ceinture a la taille sur les images sans vetements : vient du LoRA de Lea a 1,4 (jeu de
  reference en legging). Essai propose : force 1,2 puis 1,0 a seed constante ; sinon nouveau jeu de
  reference et reentrainement (~2 $).
- Sous-scenes : un fondu fantome quand l'image de fin change de cadrage ; consigne renforcee, a reverifier.
- Rappel d'un reglage valide dans la page Plan : verifie cote serveur, pas au clic.
- Le dossier `data/` appartient a root (cree par Docker) : ecrire les fichiers de plans dans `jobs/`.
- Veille planifiee lundi et jeudi : verifier le premier passage (`docs/veille.md`).

## Travailler avec la session cloud
Elle peut encore servir pour des essais GPU. Le depot est la passerelle : pousser sur la branche,
`git pull` de l'autre cote. Consigner toute decision dans le journal.
