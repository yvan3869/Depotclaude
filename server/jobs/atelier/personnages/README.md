# Fiches de personnage deposees pour l'atelier

Un agent tiers depose ici ses fiches (`<nom_court>.yaml`, d'apres `server/jobs/personnage.modele.yaml`) ; la page
Atelier, Personnages, les liste et le proprietaire les ouvre, les relit et les enregistre. Verification avant
depot : `python3 tools/triage/verifier.py server/jobs/atelier/personnages/<nom_court>.yaml`.

Les `.yaml` de ce dossier ne sont pas suivis par git.
