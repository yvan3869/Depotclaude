# Veille des modèles

Relevé du 14/11/2026. Sources : articles et guides publics, à recouper avec les fiches officielles avant toute
décision. Ce qui n'est confirmé que par un seul article est signalé comme tel.

## Ce que nous utilisons

- **Images** : Z-Image Turbo, LoRA de visage à 1,4.
- **Retouche** : Qwen-Image-Edit 2509.
- **Vidéo** : Wan 2.2 I2V 14B, deux passes (high et low noise), LoRA rapide lightx2v en 4 pas.

## Vidéo

### Wan 2.2 reste la référence ouverte

- Les comparatifs de 2026 le citent encore comme le meilleur modèle vidéo à poids ouverts pour le rendu photo, sous licence Apache 2.0, avec le plus grand choix de LoRA et d'accélérateurs.
- Aucun successeur à poids ouverts confirmé. Un article range « Wan 2.6 » parmi les modèles ouverts : non vérifié, les poids ne semblent pas publiés.
- **Avis** : on reste sur Wan 2.2. Rien à changer.
- Sources : [Thunder Compute](https://www.thundercompute.com/blog/best-open-source-ai-video-generation-models), [Local AI Master](https://localaimaster.com/blog/local-ai-video-generation), [scriptbyai](https://www.scriptbyai.com/best-open-ai-video-generation-models/).

### LTX-2 et LTX-2.3 (Lightricks) : image et son en une passe

- Premier modèle ouvert qui produit la vidéo et le son synchronisé ensemble (ambiance, voix, musique). Version 2.3 sortie en mars 2026 : détail plus net, format portrait natif, jusqu'à 20 s.
- Taille : environ 19 à 22 milliards de paramètres (14 pour la vidéo, 5 pour le son). Tourne sur 12 à 16 Go de mémoire vidéo en version allégée (FP8), 24 Go en pleine précision. Pris en charge par ComfyUI.
- Licence : « LTX-2 Community », gratuite sous 10 M$ de chiffre d'affaires selon la page ComfyUI ; un article parle d'Apache 2.0. **À lire sur la fiche officielle avant usage commercial.**
- Limites : qualité d'image par clip jugée en dessous de Wan 2.2, bien moins de LoRA, et nos LoRA Wan n'y fonctionnent pas.
- **Avis** : le candidat sérieux pour le lot « son ». À essayer sur un clip du temps 1, à côté de la solution plus simple (son ajouté au montage). Coût d'un essai : environ 0,30 à 0,50 $.
- Sources : [Lightricks](https://ltx.io/blog/ltx-2-is-now-open-source), [ComfyUI](https://blog.comfy.org/p/ltx-2-open-source-audio-video-ai), [Wikipedia](https://en.wikipedia.org/wiki/LTX-2), [dev.to](https://dev.to/gary_yan_86eb77d35e0070f5/ltx-23-open-source-audio-video-sync-20s-4k-video-on-gpu-471e).

### HunyuanVideo 1.5 (Tencent)

- Image vers vidéo jusqu'en 1080p, à partir de 14 Go de mémoire vidéo, version distillée rapide et outils d'entraînement de LoRA.
- **Avis** : pas d'avantage net sur Wan 2.2 pour nos plans de 5 s. En réserve.
- Source : [Thunder Compute](https://www.thundercompute.com/blog/best-open-source-ai-video-generation-models).

## Images

### Z-Image : Turbo et Base

- Turbo est sorti le 26/11/2025, la version Base (non distillée) le 27/01/2026. Les deux sont publiques.
- La Base sert surtout à entraîner des LoRA plus fidèles ; certaines LoRA du catalogue sont faites pour elle (mention « ZIB ») et se comportent différemment sur Turbo.
- Pas de « Turbo 2 » officiel : le nom n'apparaît que dans un outil commercial.
- **Avis** : on reste sur Turbo. Si le visage dérive encore, réentraîner la LoRA de visage sur la Base est la piste à essayer.
- Sources : [dépôt officiel](https://github.com/Tongyi-MAI/Z-Image), [Local AI Master](https://localaimaster.com/blog/z-image-base-edit-guide).

### Z-Image-Edit : toujours pas publié

- Annoncé pour début 2026, encore marqué « à paraître » dans le dépôt officiel en août 2026. Des sites tiers disent y donner accès : non officiel.
- **Avis** : on garde Qwen-Image-Edit pour la retouche.
- Source : [demande sur le dépôt officiel](https://github.com/Tongyi-MAI/Z-Image/issues/169).

### Qwen-Image 2.1

- Un seul article décrit une version 2.1 sortie en septembre 2026 sous licence réservée à la recherche, avec une variante rapide en octobre. Non recoupé.
- **Avis** : inutilisable pour nous si la licence est bien non commerciale. À revérifier.
- Source : [orcarouter](https://www.orcarouter.ai/blog/qwen-image-2-1-vs-z-image-turbo).

### FLUX.2 Klein

- Cité comme l'autre modèle rapide qui tient sur 16 Go. Pas d'essai chez nous, et notre LoRA de visage serait à refaire.
- Source : [runaihome](https://runaihome.com/blog/z-image-turbo-16gb-vram-home-lab-image-gen-2026/).

## LoRA : où chercher

La recherche sur le web ne remonte rien d'utile sur les LoRA : c'est l'onglet **Catalogue** qui sert à cela, il
interroge Civitai et Hugging Face en direct, triés par nombre de téléchargements. Relevé du 14/11/2026 :

- **Z-Image, Réalisme** : choix large sur Civitai (plus de 24 fiches).
- **Z-Image, Smartphone et photo amateur** : 6 fiches sur Civitai. C'est la catégorie la plus utile pour le temps 1.
- **Wan 2.2, Mouvement** : 6 fiches sur Civitai, livrées en paire (high et low), et 19 dépôts sur Hugging Face.
- **Hugging Face, Z-Image** : 4 dépôts seulement ; Civitai est la bonne source pour les images.

À savoir avant de charger :

- Une LoRA sous licence non commerciale est refusée au chargement. C'est déjà le cas de « detailed perfection », présente dans notre liste : à remplacer ou à retirer, au choix du propriétaire.
- Les LoRA vidéo n'ont encore jamais été essayées dans un clip chez nous : premier essai à faire sur un seul plan.
- Une LoRA d'image fait tirer l'image directement, sans retouche depuis l'image de référence : le décor peut bouger.

## À suivre

- Sortie de Z-Image-Edit.
- Publication éventuelle de poids pour un Wan plus récent que 2.2.
- Licence exacte de LTX-2.3, puis essai du son.
