#!/usr/bin/env python3
"""Controle automatique d'un clip : ressemblance du visage, scintillement, nettete.

    python qc_clip.py --ref master.png clip1.mp4 clip2.webm [--sheet-dir out/] [--json out.json]

Dependances : torch, torchvision, facenet-pytorch (installe avec --no-deps), av, pillow, numpy.
Independant du personnage : la reference est passee en argument.

Mesures par clip
- face_sim_mean / face_sim_min : similarite cosinus (0-1) entre le visage de chaque image
  echantillonnee et celui de la reference. Indicatif : > 0,6 meme personne, < 0,4 derive.
- face_missing : part des images echantillonnees sans visage detecte.
- flicker : energie temporelle haute frequence (plus c'est bas, plus c'est stable).
- sharpness : variance du laplacien (plus c'est haut, plus c'est net).
"""
import argparse
import json
import os
import sys

import av
import numpy as np
import torch
from PIL import Image

_models = {}


def models(device):
    if not _models:
        from facenet_pytorch import MTCNN, InceptionResnetV1
        _models["det"] = MTCNN(image_size=160, margin=20, select_largest=True, post_process=True, device=device)
        _models["emb"] = InceptionResnetV1(pretrained="vggface2").eval().to(device)
    return _models["det"], _models["emb"]


def embed(img, device):
    det, emb = models(device)
    face = det(img)
    if face is None:
        return None
    with torch.no_grad():
        v = emb(face.unsqueeze(0).to(device))[0]
    return torch.nn.functional.normalize(v, dim=0).cpu()


def frames(path):
    with av.open(path) as c:
        return [f.to_image().convert("RGB") for f in c.decode(video=0)]


def laplacian_var(gray):
    g = gray.astype(np.float32)
    lap = -4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]
    return float(lap.var())


def analyse(path, ref_vec, device, samples=16, sheet_dir=None):
    fr = frames(path)
    n = len(fr)
    idx = sorted({round(i * (n - 1) / (samples - 1)) for i in range(samples)})
    sims = []
    missing = 0
    for i in idx:
        v = embed(fr[i], device)
        if v is None:
            missing += 1
        else:
            sims.append(float((v * ref_vec).sum()))
    small = np.stack([np.asarray(f.convert("L").resize((160, 284)), dtype=np.float32) for f in fr])
    flicker = float(np.abs(small[2:] - 2 * small[1:-1] + small[:-2]).mean()) if n > 2 else 0.0
    sharp = float(np.mean([laplacian_var(np.asarray(fr[i].convert("L"))) for i in idx]))
    res = {
        "clip": os.path.basename(path), "frames": n, "size": list(fr[0].size),
        "face_sim_mean": round(float(np.mean(sims)), 3) if sims else None,
        "face_sim_min": round(float(np.min(sims)), 3) if sims else None,
        "face_missing": round(missing / len(idx), 2),
        "flicker": round(flicker, 3), "sharpness": round(sharp, 1),
    }
    if sheet_dir:
        os.makedirs(sheet_dir, exist_ok=True)
        w, h = 270, round(270 * fr[0].height / fr[0].width)
        cols = 8
        rows = (len(idx) + cols - 1) // cols
        sheet = Image.new("RGB", (w * cols, h * rows), "white")
        for k, i in enumerate(idx):
            sheet.paste(fr[i].resize((w, h)), ((k % cols) * w, (k // cols) * h))
        out = os.path.join(sheet_dir, os.path.splitext(os.path.basename(path))[0] + "_qc.jpg")
        sheet.save(out, quality=85)
        res["sheet"] = out
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--ref", required=True, help="image de reference du personnage (visage de face)")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--sheet-dir")
    ap.add_argument("--json")
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ref_vec = embed(Image.open(a.ref).convert("RGB"), device)
    if ref_vec is None:
        sys.exit("aucun visage detecte dans l'image de reference")
    out = [analyse(c, ref_vec, device, a.samples, a.sheet_dir) for c in a.clips]
    for r in out:
        print(json.dumps(r, ensure_ascii=False))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
