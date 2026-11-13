#!/usr/bin/env python3
"""Assemble plusieurs clips en une video verticale prete a publier.

    python montage.py --out sortie.mp4 clip1.mp4 clip2.mp4 clip3.mp4
                      [--label "Personnage IA"] [--size 1080x1920] [--fps 32]
                      [--caption "Texte affiche en bas"] [--audio musique.mp3]

Chaque clip est mis a l'echelle et recadre au format cible, puis les clips sont enchaines
en coupe franche. La mention IA est incrustee en haut a gauche (obligation de divulgation) ;
--label "" la retire. Sans --audio, la video est muette. Depend uniquement de ffmpeg.
"""
import argparse
import os
import shutil
import subprocess
import sys

FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def esc(text):
    """Echappe un texte pour le filtre drawtext de ffmpeg."""
    for a, b in (("\\", "\\\\"), (":", "\\:"), ("'", "’"), ("%", "\\%"), (",", "\\,")):
        text = text.replace(a, b)
    return text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--fps", type=int, default=32)
    ap.add_argument("--label", default="Personnage IA")
    ap.add_argument("--caption", default="")
    ap.add_argument("--audio", default="")
    ap.add_argument("--font", default="")
    a = ap.parse_args()

    ff = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
    if not ff:
        sys.exit("ffmpeg introuvable")
    w, h = (int(x) for x in a.size.lower().split("x"))
    font = a.font or next((f for f in FONTS if os.path.exists(f)), "")
    if (a.label or a.caption) and not font:
        sys.exit("aucune police trouvee : installer fonts-dejavu-core ou passer --font")

    cmd = [ff, "-y", "-loglevel", "error"]
    for c in a.clips:
        if not os.path.exists(c):
            sys.exit(f"clip introuvable : {c}")
        cmd += ["-i", c]
    if a.audio:
        cmd += ["-i", a.audio]
    n = len(a.clips)
    parts = []
    for i in range(n):
        parts.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
                     f"crop={w}:{h},fps={a.fps},setsar=1,format=yuv420p[v{i}]")
    chain = "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[cat]"
    parts.append(chain)
    last = "cat"
    if a.label:
        fs = round(h * 0.022)
        parts.append(f"[{last}]drawtext=fontfile={font}:text='{esc(a.label)}':fontsize={fs}:fontcolor=white@0.85:"
                     f"box=1:boxcolor=black@0.35:boxborderw={round(fs * 0.4)}:x={round(w * 0.04)}:y={round(h * 0.05)}[lab]")
        last = "lab"
    if a.caption:
        fs = round(h * 0.03)
        parts.append(f"[{last}]drawtext=fontfile={font}:text='{esc(a.caption)}':fontsize={fs}:fontcolor=white:"
                     f"borderw={max(2, fs // 12)}:bordercolor=black@0.8:x=(w-text_w)/2:y=h*0.80[cap]")
        last = "cap"
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{last}]"]
    if a.audio:
        cmd += ["-map", f"{n}:a", "-c:a", "aac", "-b:a", "160k", "-shortest"]
    cmd += ["-c:v", "libx264", "-crf", "19", "-preset", "medium", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print(f"{a.out} ecrit ({n} clips, {w}x{h}, {a.fps} i/s)")


if __name__ == "__main__":
    main()
