# Guide RunPod - ComfyUI + Wan 2.2

Non teste depuis ce depot : noms de fichiers et tarifs a verifier au moment de
l'installation (ils changent). Compter 1 h pour la premiere mise en place.

## 1. Volume reseau (une seule fois)
- Storage > Network Volume > 100 Go, dans une region qui propose des RTX 4090/5090.
- Tout ce qui est modele, LoRA et sortie vit sur ce volume ; le pod, lui, se supprime
  apres chaque session pour ne pas payer a l'arret.

## 2. Pod
- Deploy > GPU : RTX 4090 (24 Go) pour commencer, RTX 5090 (32 Go) pour le 720p.
- Un volume reseau ne s'attache qu'a un pod Secure Cloud (pas Community Cloud).
  Rester en Secure Cloud : ~0,89 $/h pour une 4090 au lieu de ~0,34 $/h, mais les 70 Go
  de modeles ne sont pas a retelecharger a chaque session.
- Console : + New > Pod. Dans le panneau Compute, choisir le volume dans le filtre
  "Network volume" : seuls les GPU du meme centre de donnees restent proposes.
  (Le type de cloud se regle dans Filter > Cloud type.)
- Template : un template ComfyUI officiel RunPod. Le volume est monte sur /workspace.
- Ports : 8188 (ComfyUI), 8888 (Jupyter pour le terminal).
- Toujours "Terminate" en fin de session (pas "Stop") : le volume conserve tout.

## 3. Modeles a telecharger (terminal Jupyter)
Depot Hugging Face : `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` (dossier `split_files/`).

| Fichier | Dossier ComfyUI/models/ |
|---|---|
| wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors | diffusion_models |
| wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors | diffusion_models |
| wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors | diffusion_models |
| wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors | diffusion_models |
| umt5_xxl_fp8_e4m3fn_scaled.safetensors | text_encoders |
| wan_2.1_vae.safetensors | vae |
| LoRA lightx2v 4 steps (high + low noise, i2v et t2v) | loras |

```bash
pip install -U "huggingface_hub[cli]"
cd /workspace/ComfyUI/models
hf download Comfy-Org/Wan_2.2_ComfyUI_Repackaged \
  --include "split_files/diffusion_models/wan2.2_i2v_*14B_fp8_scaled*" \
            "split_files/diffusion_models/wan2.2_t2v_*14B_fp8_scaled*" \
            "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled*" \
            "split_files/vae/wan_2.1_vae*" \
            "split_files/loras/*lightx2v*" \
  --local-dir /workspace/hf_wan22
# puis deplacer chaque fichier de /workspace/hf_wan22/split_files/<type>/ vers models/<type>/
```
Environ 70 Go au total. Si le template place ComfyUI ailleurs, adapter le chemin.

## 4. Premier test
- Dans ComfyUI : Workflow > Browse Templates > Video > "Wan 2.2 14B Image to Video".
- Charger une image, prompt court, 640x640, 81 frames, 4 steps avec les LoRA lightx2v.
- Reference publiee : ~70 s par clip de 5 s sur 4090. Si c'est bien plus long, un
  modele est mal place ou decharge en RAM.

## 5. Jeu de reference de Lea (avant le LoRA)
Le LoRA a besoin de 30 a 40 images coherentes d'un visage qui n'existe pas encore.
1. Generer 40 a 60 portraits avec Wan 2.2 T2V en image fixe (1 frame), prompt
   "A. Casting" de `persona/lora_reference_prompts.md`. Choisir UN visage.
2. Decliner ce visage avec un modele d'edition d'image open weights
   (Qwen-Image-Edit, template ComfyUI disponible) : angles, expressions, tenues, decors
   (sections B a E du fichier de prompts).
3. Trier severement : ne garder que les images ou visage, taches de rousseur, grain
   de beaute et tatouages sont corrects. Mieux vaut 30 images justes que 60 moyennes.
4. Legender chaque image : `leamorel, <description courte de la tenue, du cadrage, du decor>`.
   Ne pas decrire ce qui doit etre appris comme permanent (visage, tatouages).

## 6. Entrainement du LoRA
- Outil : musubi-tuner ou ai-toolkit (les deux gerent Wan 2.2 ; suivre leur README).
- Mot declencheur : `leamorel`. Resolution 768-1024, rang 16-32, ~2000-3000 pas.
- Entrainer sur le modele T2V low noise en priorite (c'est lui qui porte les details
  du visage) ; high noise ensuite si la silhouette derive.
- Sauvegarder un checkpoint tous les 250 pas et comparer : prendre le dernier avant
  que les images ne deviennent rigides ou toutes identiques.
- Cout attendu : 1 a 3 h de GPU.

## 7. Production
1. Image fixe : Wan 2.2 T2V + LoRA Lea (1 frame) -> valider.
2. Video : Wan 2.2 I2V a partir de l'image validee, LoRA Lea sur les deux experts.
3. Finition : interpolation (RIFE) + upscale, montage ffmpeg de 3 a 6 plans, voix off.
4. Tri humain, puis publication avec le label IA.

## 8. Pieges frequents
- Oublier de terminer le pod : c'est le premier poste de depense inutile.
- LoRA d'une version de modele chargee sur une autre (i2v/t2v, high/low) : resultat degrade.
- Texte tatoue ("respire") : illisible en video la plupart du temps ; le cadrer rarement.
