# Jeu de reference de Lea (13/11/2026)

Visage : casting n.29. Image maitre : `master.jpg`. Les fichiers originaux (PNG) sont sur
le volume RunPod `lea-models`, dossier `/workspace/runpod-slim/ComfyUI/output`
(prefixes `set_` et `nm_`). Ici : planches de controle uniquement.

## Methode
- Casting : Wan 2.2 T2V low-noise + LoRA lightx2v, 8 pas, res_multistep/beta, 864x1152 (~10 s/image).
- Declinaisons : Qwen-Image-Edit 2509 + LoRA Lightning 8 pas, image maitre en reference (~16 s/image).
- Sans maquillage : seconde passe d'edition avec cette seule consigne (melangee a d'autres, elle est ignoree).

## Tri (40 images + 14 sans maquillage)
A exclure de l'entrainement :
- a08, b01 : tatouages recopies dans le dos.
- e05, o04 : lune dessinee sur le vetement.
- t03 : lavande sur les cotes (tatouage pas encore canon).
- e03 nm, b03 nm : taches de rousseur excessives.
Restent 35 images maquillees et 12 sans maquillage.

## Limites connues
- Peau encore lisse, rendu "studio" ; meme salon en arriere-plan sur beaucoup d'images
  (a decrire dans les legendes pour que le LoRA ne l'apprenne pas).
- Cheveux plus cuivres qu'auburn fonce.
