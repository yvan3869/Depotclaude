#!/bin/bash
# Entraine un LoRA Z-Image a partir d'un dossier d'images legendees, sur un pod RunPod qui a le
# volume du projet monte sur /workspace. Generique : personnage, style, tenue, concept.
#
#   bash train_zimage_lora.sh <dossier_images> <nom_du_lora> [passages=30] [taux=2e-4]
#
# Le dossier contient des paires image.png + image.txt (meme nom). Chaque .txt est la legende de
# l'image, en anglais, et commence par le mot declencheur choisi pour ce LoRA.
# Sortie : /workspace/lea_lora/<nom>_comfy.safetensors, deja relie au dossier loras de ComfyUI.
# Duree indicative : 45 images x 30 passages = 1350 pas, environ 40 min sur RTX 5090.
set -e
DS=${1:?dossier des images}; NAME=${2:?nom du LoRA}; EPOCHS=${3:-30}; LR=${4:-2e-4}
M=/workspace/runpod-slim/ComfyUI/models
TM=/workspace/train_models
OUT=/workspace/lea_lora
cd /workspace/musubi-tuner && source venv/bin/activate
N=$(ls "$DS"/*.txt 2>/dev/null | wc -l)
[ "$N" -ge 10 ] || { echo "ARRET : moins de 10 legendes .txt dans $DS"; exit 1; }
FREE=$(df -BG --output=avail /workspace | tail -1 | tr -dc 0-9)
echo "images legendees : $N ; place libre sur le volume : ${FREE} Go"
DIT=$TM/split_files/diffusion_models/z_image_bf16.safetensors
[ -f $DIT ] || hf download Comfy-Org/z_image split_files/diffusion_models/z_image_bf16.safetensors --local-dir $TM
VAE=$M/vae/ae.safetensors; TE=$M/text_encoders/qwen_3_4b.safetensors
CFG=/workspace/train_${NAME}.toml
cat > $CFG <<TOML
[general]
resolution = [1024, 1024]
caption_extension = ".txt"
batch_size = 1
enable_bucket = true
bucket_no_upscale = true

[[datasets]]
image_directory = "$DS"
cache_directory = "/workspace/train_cache_${NAME}"
num_repeats = 1
TOML
python src/musubi_tuner/zimage_cache_latents.py --dataset_config $CFG --vae $VAE
python src/musubi_tuner/zimage_cache_text_encoder_outputs.py --dataset_config $CFG --text_encoder $TE --batch_size 8
accelerate launch --num_cpu_threads_per_process 1 --mixed_precision bf16 src/musubi_tuner/zimage_train_network.py \
  --dit $DIT --vae $VAE --text_encoder $TE --dataset_config $CFG --sdpa --mixed_precision bf16 \
  --timestep_sampling shift --weighting_scheme none --discrete_flow_shift 2.0 \
  --optimizer_type adamw --learning_rate $LR --optimizer_args weight_decay=0.01 \
  --lr_scheduler cosine --lr_warmup_steps 50 --gradient_checkpointing \
  --max_data_loader_n_workers 2 --persistent_data_loader_workers \
  --network_module networks.lora_zimage --network_dim 32 --network_alpha 32 \
  --max_train_epochs $EPOCHS --save_every_n_epochs $EPOCHS --seed 42 \
  --output_dir $OUT --output_name $NAME
python $(find src -name convert_lora.py | head -1) --input $OUT/$NAME.safetensors --output $OUT/${NAME}_comfy.safetensors --target other
ln -sf $OUT/${NAME}_comfy.safetensors $M/loras/${NAME}_comfy.safetensors
rm -rf /workspace/train_cache_${NAME}
echo "TERMINE : ${NAME}_comfy.safetensors (a tester a des forces de 1,0 a 1,8)"
