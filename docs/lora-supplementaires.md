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

## Quel modele de base choisir pour un LoRA d'image
Les images sont generees avec **Z-Image-Turbo** (`z_image_turbo_bf16.safetensors`). Sur Civitai,
prendre un LoRA dont le modele de base est "Z-Image Turbo" (ou "Z-Image"). Un LoRA entraine sur
Z-Image de base fonctionne aussi sur Turbo mais demande une force plus elevee : c'est le cas de
celui de Lea, entraine sur la base et applique a 1,4. Les autres familles (Flux, SDXL, Pony,
Illustrious, Chroma, Qwen) ne fonctionnent pas.

## Ajouter un LoRA de Civitai en une commande
Dans `server/`, apres avoir mis `CIVITAI_TOKEN=<cle>` dans `server/.env` :

    docker compose run --rm pilot lora add "https://civitai.com/models/<numero>?modelVersionId=<numero>" --name detail --strength 0.6
    docker compose run --rm pilot lora add "modelVersionId=<numero>" --name autre
    docker compose run --rm pilot lora list
    docker compose run --rm pilot lora remove detail

La commande lit la fiche Civitai, puis refuse si le modele de base n'est pas Z-Image ou Z-Image
Turbo, si le fichier n'est pas un `.safetensors`, ou si la licence n'autorise pas l'usage
commercial des images (`--force` passe outre, a vos risques). Elle demarre un pod, depose le
fichier sur le volume, supprime le pod et inscrit le LoRA dans `data/lora_catalog.yaml` avec ses
mots declencheurs, qui sont ajoutes automatiquement au prompt. Cout : environ 0,05 $.
Ce catalogue du serveur complete celui de `persona/production.yaml`. Le LoRA apparait ensuite dans
la page Test avec sa force reglable.

## Voie 1 bis : deposer un LoRA a la main
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

## Declarer plusieurs LoRA et les comparer en lot
Dans `persona/production.yaml`, chaque LoRA depose sur le volume recoit un nom court :

    lora_catalog:
      detail: {file: "mon_lora.safetensors", strength: 0.6}
      autre:  {file: "autre_lora.safetensors", strength: 0.8}

Un plan appelle ensuite les LoRA par leur nom : `loras: [detail]`, ou
`loras: [{name: detail, strength: 0.8}]` pour une autre force, ou `loras: []` pour aucun.
Sans ligne `loras`, le plan utilise `extra_loras_still`.

Pour comparer : copier `server/jobs/test_lora.yaml`, y mettre sa description et la liste des
variantes (une par plan), puis lancer avec `--stills-only`. L'option `same_seed: true` donne le
meme tirage a tous les plans : seule la variante de LoRA change d'une image a l'autre.
Le pilote verifie avant de calculer que chaque fichier existe sur le volume.
Dans le formulaire "Nouveau lot", le champ "LoRA supplementaires" prend les memes noms.

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
- Dans le formulaire "Nouveau lot", les LoRA choisis s'appliquent aux trois temps du lot.
- Deux LoRA de personnage ou de corps appliques ensemble se disputent le visage : baisser la force
  du second, jamais celle de Lea en dessous de 1,2.
- Pour la video, l'identite vient de l'image de depart ; un LoRA Wan 2.2 de mouvement se declare
  dans `lora_clip`.
