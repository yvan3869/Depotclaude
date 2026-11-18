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


def accorder(g, image=("ls", 0)):
    """Couleurs de l'image finale accordees a celles d'une image du graphe (par defaut celle dont lieu_depart est parti :
    le brouillon ou la photo du lieu) : la lumiere reste celle des scenes d'avant. A appeler en dernier (noeud ColorMatch)."""
    g["cm"] = {"class_type": "ColorMatch", "inputs": {"image_ref": list(image), "image_target": g["save"]["inputs"]["images"], "method": "mkl"}}
    g["save"]["inputs"]["images"] = ["cm", 0]
    return g


def finition(g, w, h, facteur=1.5, denoise=0.3, steps=6):
    """Seconde passe d'un graphe de still_zimage : l'image finie est agrandie, puis redessinee legerement a cette taille
    (meme texte, memes LoRA, sans pose imposee : la composition ne bouge plus). La peau, les yeux et les mains gagnent en
    detail, surtout quand le personnage est petit dans le cadre. A appeler en dernier, apres la pose ou le decor."""
    W, H = round(w * facteur / 16) * 16, round(h * facteur / 16) * 16
    g["fs"] = {"class_type": "ImageScale", "inputs": {"image": g["save"]["inputs"]["images"], "upscale_method": "lanczos",
                                                      "width": W, "height": H, "crop": "center"}}
    g["fe"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["fs", 0], "vae": ["vae", 0]}}
    g["fk"] = {"class_type": "KSampler", "inputs": {
        "model": ["shift", 0], "seed": g["ks"]["inputs"]["seed"], "steps": steps, "cfg": 1.0, "sampler_name": "res_multistep",
        "scheduler": "simple", "positive": ["pos", 0], "negative": ["neg", 0], "latent_image": ["fe", 0], "denoise": denoise}}
    g["fd"] = {"class_type": "VAEDecode", "inputs": {"samples": ["fk", 0], "vae": ["vae", 0]}}
    g["save"]["inputs"]["images"] = ["fd", 0]
    return g


def reprise_visage(m, char, image_name, prompt, W, H, boite, seed, prefix, cote=768, denoise=0.45, steps=8):
    """Reprise d'un visage petit dans le cadre (plan large, en pied) : un carre autour du visage est agrandi, redessine
    legerement avec la seule LoRA du personnage, puis recolle a sa place, bord adouci. Le reste de l'image ne change pas.
    `boite` : (x0, y0, x1, y1) du visage en fractions de l'image (rendue par le controleur) ; W, H : taille de l'image."""
    x0, y0, x1, y1 = boite[0] * W, boite[1] * H, boite[2] * W, boite[3] * H
    c = int(max(64, min(2.2 * max(x1 - x0, y1 - y0), W, H))) // 8 * 8
    x = int(max(0, min((x0 + x1) / 2 - c / 2, W - c)))
    y = int(max(0, min((y0 + y1) / 2 - c / 2, H - c)))
    g = still_zimage(m, char, prompt, cote, cote, seed, prefix, steps=steps, loras=[])
    del g["lat"]
    g["vi"] = {"class_type": "LoadImage", "inputs": {"image": image_name}}
    g["vc"] = {"class_type": "ImageCrop", "inputs": {"image": ["vi", 0], "width": c, "height": c, "x": x, "y": y}}
    g["vs"] = {"class_type": "ImageScale", "inputs": {"image": ["vc", 0], "upscale_method": "lanczos", "width": cote, "height": cote, "crop": "disabled"}}
    g["ve"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["vs", 0], "vae": ["vae", 0]}}
    g["ks"]["inputs"].update(latent_image=["ve", 0], denoise=denoise)
    g["vr"] = {"class_type": "ImageScale", "inputs": {"image": ["dec", 0], "upscale_method": "lanczos", "width": c, "height": c, "crop": "disabled"}}
    g["vm"] = {"class_type": "SolidMask", "inputs": {"value": 1.0, "width": c, "height": c}}
    b = max(4, c // 6)
    g["vf"] = {"class_type": "FeatherMask", "inputs": {"mask": ["vm", 0], "left": b, "top": b, "right": b, "bottom": b}}
    g["vk"] = {"class_type": "ImageCompositeMasked", "inputs": {"destination": ["vi", 0], "source": ["vr", 0], "x": x, "y": y,
                                                                "resize_source": False, "mask": ["vf", 0]}}
    g["save"]["inputs"]["images"] = ["vk", 0]
    return g


def finir_planche(m, char, image_name, prompt, w, h, seed, prefix, loras=None, denoise=0.5, steps=9):
    """Finition d'une planche faite par retouche : l'image (deja deposee) est redessinee en partie par Z-Image, avec le texte de
    la fiche et les LoRA choisies, sauf le visage, garde au pixel. La retouche tient l'identite (visage du portrait, corps de
    reference) ; Z-Image rend la peau, le tissu, les cheveux, et les LoRA jouent sur le corps. Le visage est repere par les points
    du squelette ; sans visage visible (de dos), toute l'image est redessinee. Plus `denoise` est haut, plus le corps bouge."""
    g = still_zimage(m, char, prompt, w, h, seed, prefix, steps=steps, loras=loras or [])
    del g["lat"]
    g["pi"] = {"class_type": "LoadImage", "inputs": {"image": image_name}}
    g["ps"] = {"class_type": "ImageScale", "inputs": {"image": ["pi", 0], "upscale_method": "lanczos", "width": w, "height": h, "crop": "center"}}
    g["pck"] = {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": m["sdpose"]}}
    g["pkp"] = {"class_type": "SDPoseKeypointExtractor", "inputs": {"model": ["pck", 0], "vae": ["pck", 2], "image": ["ps", 0], "batch_size": 1}}
    g["pdr"] = {"class_type": "SDPoseDrawKeypoints", "inputs": {
        "keypoints": ["pkp", 0], "draw_body": False, "draw_hands": False, "draw_face": True, "draw_feet": False,
        "stick_width": 4, "face_point_size": 10, "score_threshold": 0.3, "draw_head": False}}
    g["pdx"] = {"class_type": "ImageScale", "inputs": {"image": ["pdr", 0], "upscale_method": "bilinear", "width": w, "height": h, "crop": "disabled"}}
    for ch in ("red", "green", "blue"):
        g["m" + ch[0]] = {"class_type": "ImageToMask", "inputs": {"image": ["pdx", 0], "channel": ch}}
    g["m1"] = {"class_type": "MaskComposite", "inputs": {"destination": ["mr", 0], "source": ["mg", 0], "x": 0, "y": 0, "operation": "add"}}
    g["m2"] = {"class_type": "MaskComposite", "inputs": {"destination": ["m1", 0], "source": ["mb", 0], "x": 0, "y": 0, "operation": "add"}}
    g["mt"] = {"class_type": "ThresholdMask", "inputs": {"mask": ["m2", 0], "value": 0.04}}
    # les points sont elargis jusqu'a se toucher (aucun trou dans la joue), puis la zone est resserree : le front et le menton y sont
    g["mg1"] = {"class_type": "GrowMask", "inputs": {"mask": ["mt", 0], "expand": 72, "tapered_corners": True}}
    g["mw"] = {"class_type": "GrowMask", "inputs": {"mask": ["mg1", 0], "expand": -36, "tapered_corners": True}}
    g["mim"] = {"class_type": "MaskToImage", "inputs": {"mask": ["mw", 0]}}
    g["mbl"] = {"class_type": "ImageBlur", "inputs": {"image": ["mim", 0], "blur_radius": 10, "sigma": 5.0}}
    g["mz"] = {"class_type": "ImageToMask", "inputs": {"image": ["mbl", 0], "channel": "red"}}
    g["minv"] = {"class_type": "InvertMask", "inputs": {"mask": ["mw", 0]}}
    g["enc"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["ps", 0], "vae": ["vae", 0]}}
    g["lat"] = {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["enc", 0], "mask": ["minv", 0]}}
    g["ks"]["inputs"].update(latent_image=["lat", 0], denoise=denoise)
    g["comp"] = {"class_type": "ImageCompositeMasked", "inputs": {"destination": ["dec", 0], "source": ["ps", 0], "x": 0, "y": 0,
                                                                  "resize_source": False, "mask": ["mz", 0]}}
    g["save"]["inputs"]["images"] = ["comp", 0]
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


def edit_image(m, image_name, prompt, w, h, seed, prefix, steps=8, loras=None):
    """Variante d'une image par edition (Qwen-Image-Edit + LoRA rapide) : meme personnage, meme decor,
    pose ou etat different. Sert a fabriquer l'image de fin d'un clip debut/fin.
    `loras` : LoRA de la famille du modele de retouche, {"name": fichier, "strength"}, chargees avant la LoRA rapide."""
    g = {"unet": {"class_type": "UNETLoader", "inputs": {"unet_name": m["edit"], "weight_dtype": "default"}}}
    src = "unet"
    for i, x in enumerate(loras or []):
        g[f"ex{i}"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": [src, 0], "lora_name": x["name"], "strength_model": float(x.get("strength", 1.0))}}
        src = f"ex{i}"
    return g | {
        "fast": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": [src, 0], "lora_name": m["edit_fast_lora"], "strength_model": 1.0}},
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


def poser_tete(m, image_name, portrait_name, prompt, w, h, seed, prefix, part=0.375, fondu=96):
    """Pose la tete d'un portrait (image 2) sur une image en pied (image 1) sans toucher au corps : seul le haut de l'image
    (tete et epaules) passe par la retouche, agrandi deux fois (en pied, la tete est trop petite pour ressembler au portrait),
    puis il est remis a sa place, fondu vers le bas dans l'image d'origine. Le reste de l'image n'est pas recalcule."""
    hc = int(h * part) // 16 * 16
    g = edit_image(m, image_name, prompt, 2 * w, 2 * hc, seed, prefix)
    g |= {"haut": {"class_type": "ImageCrop", "inputs": {"image": ["img", 0], "width": w, "height": hc, "x": 0, "y": 0}},
          "grand": {"class_type": "ImageScale", "inputs": {"image": ["haut", 0], "upscale_method": "lanczos", "width": 2 * w, "height": 2 * hc, "crop": "disabled"}},
          "img2": {"class_type": "LoadImage", "inputs": {"image": portrait_name}},
          "petit": {"class_type": "ImageScale", "inputs": {"image": ["dec", 0], "upscale_method": "lanczos", "width": w, "height": hc, "crop": "disabled"}},
          "plein": {"class_type": "SolidMask", "inputs": {"value": 1.0, "width": w, "height": hc}},
          "masque": {"class_type": "FeatherMask", "inputs": {"mask": ["plein", 0], "left": 0, "top": 0, "right": 0, "bottom": fondu}},
          "pose": {"class_type": "ImageCompositeMasked", "inputs": {"destination": ["img", 0], "source": ["petit", 0], "x": 0, "y": 0, "resize_source": False, "mask": ["masque", 0]}}}
    for k in ("pos", "neg"):
        g[k]["inputs"] |= {"image1": ["grand", 0], "image2": ["img2", 0]}
    g["save"]["inputs"]["images"] = ["pose", 0]
    return g


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
