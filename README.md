# Persona IA - pipeline de contenu

Personnage 100 % fictif, adulte, assume comme IA. Ce depot contient la bible du
personnage, la planification hebdomadaire et la checklist de conformite.
La generation d'images/videos se fait dans ComfyUI (GPU loue) ; ce depot
orchestre, il ne contient pas de contenu explicite.

## Plateformes (verifie nov. 2026, a revalider avant lancement)
- Fanvue : accepte les createurs entierement IA (compte verifie + tag IA). Cible principale.
- OnlyFans : refuse les comptes entierement IA (le contenu doit montrer le createur verifie).
- Fansly : interdit l'IA photorealiste, meme etiquetee.
- Instagram / TikTok : label "contenu IA" obligatoire.
- DM : sur Fanvue, messagerie IA autorisee via ses outils integres ou son API officielle.

## Structure
- `docs/accounts-setup.md` comptes a creer, acces, regles Fanvue verifiees
- `docs/runpod-setup.md`  installation ComfyUI + Wan 2.2, LoRA
- `tools/triage/`         interface de tri : `python tools/triage/triage.py --dir <sorties>`
- `persona/bible.yaml`   identite, gestuelle, routine, regles de coherence
- `pipeline/plan_week.py` genere le planning de la semaine via l'API Claude
- `docs/compliance.md`   regles non negociables
- `comfyui/`             workflows (a ajouter apres entrainement du LoRA)

## Demarrage
1. Remplir `persona/bible.yaml`.
2. Generer un jeu de references (30-60 images) -> entrainer un LoRA -> valider la coherence.
3. `ANTHROPIC_API_KEY=... python pipeline/plan_week.py`
4. Produire les clips dans ComfyUI, valider manuellement, programmer la publication.

## Budget indicatif
GPU loue 0,3-0,8 EUR/h (RunPod/Vast), entrainement LoRA ~2-5 EUR, generation
video quelques EUR/jour, API LLM < 5 EUR/mois pour la planification.
