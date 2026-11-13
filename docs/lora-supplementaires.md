# LoRA supplementaires : utiliser ou entrainer (13/11/2026)

Partage des roles (rappel de `docs/feuille-de-route.md`) : l'assistant fournit les outils et la
procedure. Le choix des LoRA pour adultes, les images d'entrainement, leurs legendes et les prompts
explicites sont faits par le proprietaire ; l'assistant ne les produit pas et ne les controle pas.

## Regles a respecter quel que soit le LoRA
- Images d'entrainement : uniquement des images generees, de personnages fictifs clairement adultes.
  Aucune photo de personne reelle, aucune image prise sur un site (regle 1 de `docs/compliance.md`).
- Fichiers `.safetensors` uniquement.
- Verifier la licence d'un LoRA telecharge : usage commercial des images autorise.
- Un LoRA est lie a une famille de modeles. Ceux du projet : Z-Image (images) et Wan 2.2 (video).
  Un LoRA pour Flux, SDXL, Illustrious ou Chroma ne fonctionne pas sur Z-Image.

## Voie 1 : utiliser un LoRA existant (a essayer en premier, aucun entrainement)
1. Dans la console RunPod, deployer un pod avec le volume `lea-models` (modele de pod habituel) et
   ouvrir JupyterLab.
2. Dans un terminal JupyterLab :

       cd /workspace/lea_lora
       wget -O mon_lora.safetensors "<lien de telechargement>"
       ln -sf /workspace/lea_lora/mon_lora.safetensors /workspace/runpod-slim/ComfyUI/models/loras/

   Pour Civitai, ajouter au lien `&token=<cle>` ou telecharger sur son poste puis glisser le fichier
   dans JupyterLab.
3. Supprimer le pod.
4. Dans `persona/production.yaml`, sur le serveur :

       extra_loras_still:
         - {name: mon_lora.safetensors, strength: 0.8}

   Il s'applique alors a toutes les images du pilote, en plus du LoRA de Lea. Commencer vers 0,6
   a 0,8 : un LoRA supplementaire trop fort deforme le visage de Lea.

## Voie 2 : entrainer son propre LoRA
A reserver au cas ou aucun LoRA existant ne convient : compter 30 a 60 images et environ 1 $ a 2 $.
1. Preparer un dossier de paires `image.png` + `image.txt`. La legende decrit l'image en anglais
   et commence par un mot declencheur propre a ce LoRA. Ce qu'on veut que le LoRA apprenne ne
   doit PAS etre decrit dans la legende ; ce qu'on veut pouvoir changer (decor, lumiere, tenue,
   pose) doit l'etre.
2. Deployer un pod avec le volume (RTX 5090 de preference), ouvrir JupyterLab, glisser le dossier
   dans `/workspace/`.
3. Copier `tools/train/train_zimage_lora.sh` sur le pod et lancer :

       bash train_zimage_lora.sh /workspace/mon_dossier mon_lora 30

4. Supprimer le pod, puis declarer le LoRA comme dans la voie 1.
5. Tester plusieurs forces (1,0 a 1,8) avant de conclure : lecon du LoRA de Lea, juge a tort
   inefficace parce qu'il n'avait ete essaye qu'a 1,0.

## Limites connues
- Le formulaire "Nouveau lot" ne permet pas encore de choisir un LoRA par plan : un LoRA declare
  dans `production.yaml` s'applique a tous les plans.
- Deux LoRA de personnage ou de corps appliques ensemble se disputent le visage : baisser la force
  du second, jamais celle de Lea en dessous de 1,2.
- Pour la video, l'identite vient de l'image de depart ; un LoRA Wan 2.2 de mouvement se declare
  dans `lora_clip`.
