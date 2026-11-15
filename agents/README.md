# Skills pour l'agent du proprietaire

Deux skills (format AgentSkills : un dossier, un `SKILL.md` avec en-tete `name` / `description`) a installer
dans l'agent du proprietaire (OpenClaw). Ils sont volontairement courts : ils disent a l'agent de relire a
chaque seance les regles du depot (`docs/agents.md`, `server/jobs/modele.yaml`,
`server/jobs/personnage.modele.yaml`) et de verifier ses fichiers avec `tools/triage/verifier.py` avant de les
annoncer. Un changement de format se fait donc dans le depot, sans toucher aux skills.

- `girls-ai-scenariste/` : ecrire une video (plans des temps 1 a 4) et la deposer dans la Production.
- `girls-ai-casting/` : creer la fiche d'un personnage et la deposer dans la Production.

Installation : par un lien vers ces dossiers plutot que par copie, pour que l'agent suive leurs mises a jour.
