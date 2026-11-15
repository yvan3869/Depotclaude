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


def decor_gele(g, brouillon, epais, denoise=0.8):
    """Decor fixe : l'image part du brouillon (deja depose) et seule la zone du personnage est refaite ; le reste de
    l'image est celui du brouillon, au pixel. La zone vient du squelette epais (deja depose), elargie, au bord adouci
    pour le collage. A 0,8 la tenue et la piece du brouillon tiennent (essai du 15/11/2026, 4 sur 4)."""
    g["bi"] = {"class_type": "LoadImage", "inputs": {"image": brouillon}}
    g["mi"] = {"class_type": "LoadImage", "inputs": {"image": epais}}
    for ch in ("red", "green", "blue"):
        g["m" + ch[0]] = {"class_type": "ImageToMask", "inputs": {"image": ["mi", 0], "channel": ch}}
    g["m1"] = {"class_type": "MaskComposite", "inputs": {"destination": ["mr", 0], "source": ["mg", 0], "x": 0, "y": 0, "operation": "add"}}
    g["m2"] = {"class_type": "MaskComposite", "inputs": {"destination": ["m1", 0], "source": ["mb", 0], "x": 0, "y": 0, "operation": "add"}}
    g["mt"] = {"class_type": "ThresholdMask", "inputs": {"mask": ["m2", 0], "value": 0.04}}
    g["mw"] = {"class_type": "GrowMask", "inputs": {"mask": ["mt", 0], "expand": 56, "tapered_corners": True}}
    g["mim"] = {"class_type": "MaskToImage", "inputs": {"mask": ["mw", 0]}}
    g["mbl"] = {"class_type": "ImageBlur", "inputs": {"image": ["mim", 0], "blur_radius": 12, "sigma": 6.0}}
    g["mz"] = {"class_type": "ImageToMask", "inputs": {"image": ["mbl", 0], "channel": "red"}}
    g["enc"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["bi", 0], "vae": ["vae", 0]}}
    g["lat"] = {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["enc", 0], "mask": ["mw", 0]}}
    g["ks"]["inputs"]["denoise"] = denoise
    g["comp"] = {"class_type": "ImageCompositeMasked", "inputs": {"destination": ["bi", 0], "source": ["dec", 0], "x": 0, "y": 0,
                                                                  "resize_source": False, "mask": ["mz", 0]}}
    g["save"]["inputs"]["images"] = ["comp", 0]
    return g


def lieu_depart(g, lieu, w, h, denoise=0.8):
    """Lieu tenu sans brouillon (scene a plusieurs personnes, que le brouillon de la pose ne sait pas placer) : l'image
    part de la photo du lieu vide (deja deposee), recadree au format, et le modele dessine les personnes par-dessus
    d'apres le texte. Plus `denoise` est bas, plus la piece tient et moins les personnes s'y posent librement."""
    g["li"] = {"class_type": "LoadImage", "inputs": {"image": lieu}}
    g["ls"] = {"class_type": "ImageScale", "inputs": {"image": ["li", 0], "upscale_method": "lanczos", "width": w, "height": h, "crop": "center"}}
    g["lat"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["ls", 0], "vae": ["vae", 0]}}
    g["ks"]["inputs"]["denoise"] = denoise
    return g


def imposer_pose(g, m, pose_name, force=0.9):
    """Ajoute a un graphe de still_zimage une pose imposee : le dessin d'un squelette (image deja deposee) guide la
    position du corps et le cadrage ; le visage, la tenue et le lieu restent ceux du texte et de la LoRA."""
    g["cnp"] = {"class_type": "ModelPatchLoader", "inputs": {"name": m["zimage_controlnet"]}}
    g["cni"] = {"class_type": "LoadImage", "inputs": {"image": pose_name}}
    g["cn"] = {"class_type": "ZImageFunControlnet", "inputs": {"model": g["ks"]["inputs"]["model"], "model_patch": ["cnp", 0],
                                                               "vae": ["vae", 0], "strength": force, "image": ["cni", 0]}}
    g["ks"]["inputs"]["model"] = ["cn", 0]
    return g


def squelette(m, image_name, prefix):
    """Dessin du squelette (corps seul, sur fond noir) de la personne d'une image."""
    return {
        "ck": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": m["sdpose"]}},
        "img": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "kp": {"class_type": "SDPoseKeypointExtractor", "inputs": {"model": ["ck", 0], "vae": ["ck", 2], "image": ["img", 0], "batch_size": 1}},
        "dr": {"class_type": "SDPoseDrawKeypoints", "inputs": {
            "keypoints": ["kp", 0], "draw_body": True, "draw_hands": False, "draw_face": False, "draw_feet": False,
            "stick_width": 4, "face_point_size": 3, "score_threshold": 0.3, "draw_head": True}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["dr", 0], "filename_prefix": prefix}},
    }


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


def clip(m, char, image_name, prompt, w, h, seed, prefix, mode="natural", frames=81, end_image_name=None, loras=None):
    """Clip : Wan 2.2 I2V. mode 'fast' (4 pas, LoRA rapide partout) ou 'natural'
    (4 pas high-noise sans LoRA rapide avec CFG 3,5, puis 4 pas low-noise rapides).
    `loras` : LoRA video supplementaires, {"name": fichier du modele high-noise ou des deux, "low": fichier du modele
    low-noise s'il est distinct, "strength"}. Un fichier dont le nom dit "high" ou "low" ne va que sur ce modele."""
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
    hi, lo = "hi_u", "lo_u"
    for i, x in enumerate(loras or []):
        f, low, st = x["name"], x.get("low") or "", float(x.get("strength", 1.0))
        cote = "" if low else "high" if "high" in f.lower() else "low" if "low" in f.lower() else ""
        if cote != "low":
            hi = _lora(g, f"hi_x{i}", hi, f, st)
        if low or cote != "high":
            lo = _lora(g, f"lo_x{i}", lo, low or f, st)
    if mode != "natural":
        hi = _lora(g, "hi_fast", hi, m["i2v_high_fast_lora"])
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


def son(prompt, neg, secondes, seed, prefix, steps=50):
    """Ambiance sonore ou musique d'apres une phrase (Stable Audio Open 1.0, 47 s au plus, stereo 44,1 kHz)."""
    return {
        "ckpt": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "stable-audio-open-1.0.safetensors"}},
        "clip": {"class_type": "CLIPLoader", "inputs": {"clip_name": "t5-base.safetensors", "type": "stable_audio", "device": "default"}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": prompt}},
        "neg": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": neg}},
        "lat": {"class_type": "EmptyLatentAudio", "inputs": {"seconds": float(secondes), "batch_size": 1}},
        "ks": {"class_type": "KSampler", "inputs": {
            "model": ["ckpt", 0], "seed": seed, "steps": steps, "cfg": 5.0, "sampler_name": "dpmpp_3m_sde_gpu", "scheduler": "exponential",
            "positive": ["pos", 0], "negative": ["neg", 0], "latent_image": ["lat", 0], "denoise": 1.0}},
        "dec": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["ks", 0], "vae": ["ckpt", 2]}},
        "save": {"class_type": "SaveAudio", "inputs": {"audio": ["dec", 0], "filename_prefix": prefix}},
    }
