"""Graphes ComfyUI (format API). Aucun element propre a un personnage : tout vient de la config."""


def _common(m, pos, neg):
    return {
        "clip": {"class_type": "CLIPLoader", "inputs": {"clip_name": m["text_encoder"], "type": "wan", "device": "default"}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": pos}},
        "neg": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": neg}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": m["vae"]}},
    }


def _lora(g, key, src, name, strength=1.0):
    g[key] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": [src, 0], "lora_name": name, "strength_model": strength}}
    return key


def still(m, char, prompt, w, h, seed, prefix, steps=8):
    """Image fixe : Wan 2.2 T2V low-noise + LoRA du personnage + LoRA rapide."""
    g = _common(m, prompt, char["negative_still"])
    g["unet"] = {"class_type": "UNETLoader", "inputs": {"unet_name": m["t2v_low"], "weight_dtype": "default"}}
    src = _lora(g, "char", "unet", char["lora_still"], char.get("lora_still_strength", 1.0))
    src = _lora(g, "fast", src, m["t2v_low_fast_lora"])
    g["shift"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": [src, 0], "shift": 5.0}}
    g["lat"] = {"class_type": "EmptyHunyuanLatentVideo", "inputs": {"width": w, "height": h, "length": 1, "batch_size": 1}}
    g["ks"] = {"class_type": "KSamplerAdvanced", "inputs": {
        "model": ["shift", 0], "add_noise": "enable", "noise_seed": seed, "steps": steps, "cfg": 1.0,
        "sampler_name": "res_multistep", "scheduler": "beta", "positive": ["pos", 0], "negative": ["neg", 0],
        "latent_image": ["lat", 0], "start_at_step": 0, "end_at_step": steps, "return_with_leftover_noise": "disable"}}
    g["dec"] = {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["vae", 0]}}
    g["save"] = {"class_type": "SaveImage", "inputs": {"images": ["dec", 0], "filename_prefix": prefix}}
    return g


def still_zimage(m, char, prompt, w, h, seed, prefix, steps=9, loras=None, char_strength=None):
    """Image fixe : Z-Image-Turbo + LoRA du personnage (entraine sur Z-Image base)."""
    g = {
        "unet": {"class_type": "UNETLoader", "inputs": {"unet_name": m["zimage"], "weight_dtype": "default"}},
        "clip": {"class_type": "CLIPLoader", "inputs": {"clip_name": m["zimage_text_encoder"], "type": "lumina2", "device": "default"}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": m["zimage_vae"]}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": prompt}},
        "neg": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["pos", 0]}},
        "lat": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
    }
    src = "unet"
    if char.get("lora_still_zimage"):
        st = char_strength if char_strength is not None else char.get("lora_still_zimage_strength", 1.0)
        src = _lora(g, "char", src, char["lora_still_zimage"], float(st))
    # LoRA supplementaires choisis par l'utilisateur : ceux du plan (loras) s'ils sont donnes,
    # sinon ceux declares pour tous les plans (extra_loras_still).
    extras = loras if loras is not None else (char.get("extra_loras_still") or [])
    for i, extra in enumerate(extras):
        src = _lora(g, f"x{i}", src, extra["name"], extra.get("strength", 1.0))
    g["shift"] = {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": [src, 0], "shift": 3.0}}
    g["ks"] = {"class_type": "KSampler", "inputs": {
        "model": ["shift", 0], "seed": seed, "steps": steps, "cfg": 1.0, "sampler_name": "res_multistep",
        "scheduler": "simple", "positive": ["pos", 0], "negative": ["neg", 0], "latent_image": ["lat", 0], "denoise": 1.0}}
    g["dec"] = {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["vae", 0]}}
    g["save"] = {"class_type": "SaveImage", "inputs": {"images": ["dec", 0], "filename_prefix": prefix}}
    return g


def edit_image(m, image_name, prompt, w, h, seed, prefix, steps=8):
    """Variante d'une image par edition (Qwen-Image-Edit + LoRA rapide) : meme personnage, meme decor,
    pose ou etat different. Sert a fabriquer l'image de fin d'un clip debut/fin."""
    return {
        "unet": {"class_type": "UNETLoader", "inputs": {"unet_name": m["edit"], "weight_dtype": "default"}},
        "fast": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["unet", 0], "lora_name": m["edit_fast_lora"], "strength_model": 1.0}},
        "shift": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["fast", 0], "shift": 3.0}},
        "norm": {"class_type": "CFGNorm", "inputs": {"model": ["shift", 0], "strength": 1.0}},
        "clip": {"class_type": "CLIPLoader", "inputs": {"clip_name": m["edit_text_encoder"], "type": "qwen_image", "device": "default"}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": m["edit_vae"]}},
        "img": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "pos": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["clip", 0], "vae": ["vae", 0], "image1": ["img", 0], "prompt": prompt}},
        "neg": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["clip", 0], "vae": ["vae", 0], "image1": ["img", 0], "prompt": ""}},
        "lat": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "ks": {"class_type": "KSampler", "inputs": {
            "model": ["norm", 0], "seed": seed, "steps": steps, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
            "positive": ["pos", 0], "negative": ["neg", 0], "latent_image": ["lat", 0], "denoise": 1.0}},
        "dec": {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["vae", 0]}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["dec", 0], "filename_prefix": prefix}},
    }


def clip(m, char, image_name, prompt, w, h, seed, prefix, mode="natural", frames=81, end_image_name=None):
    """Clip : Wan 2.2 I2V. mode 'fast' (4 pas, LoRA rapide partout) ou 'natural'
    (4 pas high-noise sans LoRA rapide avec CFG 3,5, puis 4 pas low-noise rapides)."""
    g = _common(m, prompt, char["negative_clip"])
    g["img"] = {"class_type": "LoadImage", "inputs": {"image": image_name}}
    g["i2v"] = {"class_type": "WanImageToVideo", "inputs": {
        "positive": ["pos", 0], "negative": ["neg", 0], "vae": ["vae", 0], "width": w, "height": h,
        "length": frames, "batch_size": 1, "start_image": ["img", 0]}}
    if end_image_name:  # clip debut/fin : le modele relie l'image de depart a l'image de fin
        g["img_end"] = {"class_type": "LoadImage", "inputs": {"image": end_image_name}}
        g["i2v"] = {"class_type": "WanFirstLastFrameToVideo", "inputs": {
            "positive": ["pos", 0], "negative": ["neg", 0], "vae": ["vae", 0], "width": w, "height": h,
            "length": frames, "batch_size": 1, "start_image": ["img", 0], "end_image": ["img_end", 0]}}
    g["hi_u"] = {"class_type": "UNETLoader", "inputs": {"unet_name": m["i2v_high"], "weight_dtype": "default"}}
    g["lo_u"] = {"class_type": "UNETLoader", "inputs": {"unet_name": m["i2v_low"], "weight_dtype": "default"}}
    hi = "hi_u" if mode == "natural" else _lora(g, "hi_fast", "hi_u", m["i2v_high_fast_lora"])
    lo = "lo_u"
    if char.get("lora_clip"):
        lo = _lora(g, "lo_char", lo, char["lora_clip"], char.get("lora_clip_strength", 1.0))
    lo = _lora(g, "lo_fast", lo, m["i2v_low_fast_lora"])
    g["hi_s"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": [hi, 0], "shift": 5.0}}
    g["lo_s"] = {"class_type": "ModelSamplingSD3", "inputs": {"model": [lo, 0], "shift": 5.0}}
    hi_steps, total, hi_cfg = (4, 8, 3.5) if mode == "natural" else (2, 4, 1.0)

    def ks(model, latent, add, s, e, ret, cfg):
        return {"class_type": "KSamplerAdvanced", "inputs": {
            "model": [model, 0], "add_noise": add, "noise_seed": seed, "steps": total, "cfg": cfg,
            "sampler_name": "euler", "scheduler": "simple", "positive": ["i2v", 0], "negative": ["i2v", 1],
            "latent_image": latent, "start_at_step": s, "end_at_step": e, "return_with_leftover_noise": ret}}
    g["ks_hi"] = ks("hi_s", ["i2v", 2], "enable", 0, hi_steps, "enable", hi_cfg)
    g["ks_lo"] = ks("lo_s", ["ks_hi", 0], "disable", hi_steps, total, "disable", 1.0)
    g["dec"] = {"class_type": "VAEDecode", "inputs": {"samples": ["ks_lo", 0], "vae": ["vae", 0]}}
    g["save"] = {"class_type": "SaveWEBM", "inputs": {"images": ["dec", 0], "filename_prefix": prefix, "codec": "vp9", "fps": 16.0, "crf": 18}}
    return g
