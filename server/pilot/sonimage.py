"""Son d'apres l'image (MMAudio) : ce qui tourne sur le pod, hors ComfyUI, et de quoi le lancer.

MMAudio (hkchengrex/MMAudio, variante large_44k_v2) ecoute un clip muet et fabrique le son qui va avec ce qu'on y
voit. Licence CC BY-NC 4.0 (non commerciale) : decision du proprietaire, voir docs/journal-projet.md.
Tout vit sur le volume, dans /workspace/girls-ai-mmaudio : le depot, un venv enfant de celui de ComfyUI (torch
n'est pas reinstalle), les poids. Le premier lancement installe (dix minutes), les suivants reprennent l'existant.
"""
import base64
import os
import socket
import struct
import time

DOSSIER = "girls-ai-mmaudio"
NEG = "music, speech, voice, talking, singing"

# Installation (une seule fois) puis calcul du lot. Les codes de sortie 3 et 4 disent une installation ratee.
RUN = f"""cd /workspace/{DOSSIER} || exit 2
export HF_HOME=/workspace/{DOSSIER}/hf
[ -d MMAudio ] || git clone --depth 1 https://github.com/hkchengrex/MMAudio || exit 3
PY=/workspace/runpod-slim/ComfyUI/.venv/bin/python; [ -x $PY ] || PY=$(which python3)
if [ ! -d venv ]; then
  $PY -m venv venv || exit 3
  $PY -c "import site; print(site.getsitepackages()[0])" > $(venv/bin/python -c "import site; print(site.getsitepackages()[0])")/parent.pth
fi
. venv/bin/activate
python -c "import mmaudio" 2>/dev/null || pip install -q -e MMAudio || exit 3
python -c "import torchaudio" 2>/dev/null || pip install -q torchaudio || exit 3
python -c "import soundfile" 2>/dev/null || pip install -q soundfile || exit 3
python -c "import torch, mmaudio, soundfile; assert torch.cuda.is_available()" || exit 4
cd MMAudio
python ../lot.py /workspace/{DOSSIER}
"""

# Le modele est charge une fois pour tout le lot. torchaudio.save ne marche pas dans ce venv (torchcodec) : soundfile.
LOT = '''import json, sys, traceback
from pathlib import Path
import soundfile, torch
from mmaudio.eval_utils import all_model_cfg, generate, load_video
from mmaudio.model.flow_matching import FlowMatching
from mmaudio.model.networks import get_my_mmaudio
from mmaudio.model.utils.features_utils import FeaturesUtils


@torch.inference_mode()
def main():
    racine = Path(sys.argv[1])
    lot = json.loads((racine / "lot.json").read_text())
    model = all_model_cfg["large_44k_v2"]
    model.download_if_needed()
    seq = model.seq_cfg
    net = get_my_mmaudio(model.model_name).to("cuda", torch.bfloat16).eval()
    net.load_weights(torch.load(model.model_path, map_location="cuda", weights_only=True))
    fu = FeaturesUtils(tod_vae_ckpt=model.vae_path, synchformer_ckpt=model.synchformer_ckpt, enable_conditions=True,
                       mode=model.mode, bigvgan_vocoder_ckpt=model.bigvgan_16k_path, need_vae_encoder=False)
    fu = fu.to("cuda", torch.bfloat16).eval()
    print("MODELE charge", flush=True)
    for x in lot:
        try:
            rng = torch.Generator(device="cuda")
            rng.manual_seed(int(x["seed"]))
            v = load_video(racine / "in" / x["clip"], float(x["duree"]))
            seq.duration = v.duration_sec
            net.update_seq_lengths(seq.latent_seq_len, seq.clip_seq_len, seq.sync_seq_len)
            audios = generate(v.clip_frames.unsqueeze(0), v.sync_frames.unsqueeze(0), [x.get("texte") or ""], negative_text=[x["neg"]],
                              feature_utils=fu, net=net, fm=FlowMatching(min_sigma=0, inference_mode="euler", num_steps=25),
                              rng=rng, cfg_strength=4.5)
            soundfile.write(str(racine / "out" / (Path(x["clip"]).stem + ".flac")), audios.float().cpu()[0].numpy().T, seq.sampling_rate)
            print("FAIT", x["clip"], flush=True)
        except Exception:
            traceback.print_exc()
            print("RATE", x["clip"], flush=True)


main()
'''


def ws_envoyer(hote, chemin, entetes, texte, ctx):
    """Ouvre une websocket et y envoie une trame de texte (client minimal, bibliotheque standard : l'interface qui
    lance le pilote n'a pas de module websocket). Sert a taper une commande dans un terminal de Jupyter."""
    cle = base64.b64encode(os.urandom(16)).decode()
    s = ctx.wrap_socket(socket.create_connection((hote, 443), timeout=30), server_hostname=hote)
    try:
        tete = [f"GET {chemin} HTTP/1.1", f"Host: {hote}", "Upgrade: websocket", "Connection: Upgrade", f"Sec-WebSocket-Key: {cle}",
                "Sec-WebSocket-Version: 13", f"Origin: https://{hote}"] + [f"{k}: {v}" for k, v in entetes.items()]
        s.sendall(("\r\n".join(tete) + "\r\n\r\n").encode())
        rep = b""
        while b"\r\n\r\n" not in rep:
            ch = s.recv(4096)
            if not ch:
                break
            rep += ch
        if b" 101" not in rep.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"terminal refuse : {rep.split(bytes([13, 10]), 1)[0][:80].decode(errors='replace')}")
        time.sleep(2)
        d, masque = texte.encode(), os.urandom(4)
        if len(d) > 65535:
            raise RuntimeError("trame trop longue")
        long = bytes([0x80 | len(d)]) if len(d) < 126 else bytes([0x80 | 126]) + struct.pack(">H", len(d))
        s.sendall(bytes([0x81]) + long + masque + bytes(b ^ masque[i % 4] for i, b in enumerate(d)))
        time.sleep(4)
    finally:
        s.close()
