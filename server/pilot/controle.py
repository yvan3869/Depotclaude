"""Controle des images : ce qui tourne sur le pod, hors ComfyUI (lance comme le son d'apres l'image, voir sonimage.py).

Deux outils notent chaque image avant qu'un clip en soit tire :
- un mesureur de visage (facenet-pytorch, code MIT) : nombre de visages et ressemblance avec les autres images du
  personnage (mediane des ressemblances deux a deux, de -1 a 1) ;
- un modele de vision ouvert (Qwen2.5-VL 7B, Apache 2.0) : il compare l'image a sa description et repond par des
  cases fermees (decor, tenue, pose, objet, cadrage, anatomie, chose en trop, note sur 10), une question par point.
Seules des valeurs prises dans une liste fermee reviennent du pod : aucun texte libre sur l'image.
Tout vit sur le volume, dans /workspace/girls-ai-controle : venv enfant de celui de ComfyUI, poids (16 Go).
"""

DOSSIER = "girls-ai-controle"
MODELE = "Qwen/Qwen2.5-VL-7B-Instruct"
CASES = {"setting": ("ok", "wrong", "na"), "outfit": ("ok", "wrong", "na"), "pose": ("ok", "wrong", "na"),
         "object": ("ok", "wrong", "na"), "framing": ("ok", "wrong", "na"), "anatomy": ("ok", "minor", "major")}

SYSTEME = ("You are a strict quality controller for AI-generated photographs. You compare one image with the description "
           "it was generated from and you answer only with a JSON object, no other text.")
QUESTION = """Intended description of the image:
---
{desc}
---
Compare the image with this description and answer with this JSON object only:
{{"people": <number of people visible>,
 "setting": "ok" | "wrong" | "na",
 "outfit": "ok" | "wrong" | "na",
 "pose": "ok" | "wrong" | "na",
 "object": "ok" | "wrong" | "na",
 "framing": "ok" | "wrong" | "na",
 "anatomy": "ok" | "minor" | "major",
 "score": <0 to 10, how faithful the image is to the description>}}
Rules: "wrong" when the image clearly contradicts the description on that point (setting = place and background, outfit =
clothing, pose = body position and action, object = the objects the description mentions, framing = shot size and camera
angle). "na" when the description says nothing about that point. "anatomy" judges the image alone: "major" for an extra or
missing limb or finger, a fused or deformed hand, a distorted face; "minor" for a small flaw; otherwise "ok"."""

# Questions fermees : on ne lit pas le mot repondu (le modele dit "ok" a tout quand on l'interroge point par point) mais
# la probabilite du "yes" contre le "no" au premier mot. "desc" : la question porte sur la description.
OUINON = {
    "fidele": ("desc", "Does this image show exactly what the description says?"),
    "decor": ("desc", "Considering only the place and the background, does the image match the description?"),
    "tenue": ("desc", "Considering only the clothing, does the image match the description?"),
    "geste": ("desc", "Considering only the body position and the action, does the image match the description?"),
    "objet": ("desc", "Are all the objects the description mentions visible and used as described?"),
    "cadrage": ("desc", "Considering only the shot size (close-up, medium shot, wide shot) and the camera angle, does the image match the description?"),
    "en_trop": ("", "Is there a phone, a camera, a tripod, a second person or written text visible in this image?"),
    "anatomie": ("", "Does a hand, a finger, a limb or the face look deformed or anatomically wrong in this image?"),
}
OUINON_DESC = """Intended description of the image:
---
{desc}
---
{question} Answer yes or no."""

RUN = f"""cd /workspace/{DOSSIER} || exit 2
export HF_HOME=/workspace/{DOSSIER}/hf
PY=/workspace/runpod-slim/ComfyUI/.venv/bin/python; [ -x $PY ] || PY=$(which python3)
if [ ! -d venv ]; then
  $PY -m venv venv || exit 3
  $PY -c "import site; print(site.getsitepackages()[0])" > $(venv/bin/python -c "import site; print(site.getsitepackages()[0])")/parent.pth
fi
. venv/bin/activate
python -c "from transformers import Qwen2_5_VLForConditionalGeneration" 2>/dev/null || pip install -q -U "transformers>=4.49" || exit 3
for m in PIL:pillow accelerate:accelerate torchvision:torchvision; do
  python -c "import ${{m%%:*}}" 2>/dev/null || pip install -q ${{m##*:}} || exit 3
done
python -c "import requests" 2>/dev/null || pip install -q requests
python -c "import facenet_pytorch" 2>/dev/null || pip install -q --no-deps facenet-pytorch
python -c "import torch, transformers, PIL; print('PYTHON', '$PY', torch.__version__, transformers.__version__); assert torch.cuda.is_available()" || exit 4
python lot.py /workspace/{DOSSIER}
"""

LOT = '''import json, re, statistics, sys, traceback
from pathlib import Path
import torch
from PIL import Image

racine = Path(sys.argv[1])
lot = json.loads((racine / "lot.json").read_text())
cases = json.loads((racine / "cases.json").read_text())
ouinon = json.loads((racine / "ouinon.json").read_text())
res = {x["image"]: {} for x in lot}


def ouvrir(x, cote):
    im = Image.open(racine / "in" / x["image"]).convert("RGB")
    im.thumbnail((cote, cote))
    return im


@torch.inference_mode()
def visages():
    from facenet_pytorch import MTCNN, InceptionResnetV1
    mt = MTCNN(image_size=160, margin=20, keep_all=True, device="cuda")
    rn = InceptionResnetV1(pretrained="vggface2").eval().to("cuda")
    emb = {}
    for x in lot:
        try:
            im = ouvrir(x, 1280)
            boites, probas = mt.detect(im)
            bons = [b for b, p in zip(boites if boites is not None else [], probas if probas is not None else []) if p and p > 0.9]
            res[x["image"]]["visages"] = len(bons)
            if bons:
                b = max(bons, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
                res[x["image"]]["taille_visage"] = round(float(b[3] - b[1]) / im.height, 3)
                t = mt.extract(im, [b], None)
                emb[x["image"]] = (rn(t.reshape(-1, 3, 160, 160)[:1].to("cuda"))[0], x.get("perso") or "")
        except Exception:
            traceback.print_exc()
    for n, (e, perso) in emb.items():
        autres = [float(e @ f) for m, (f, q) in emb.items() if m != n and q == perso]
        if len(autres) >= 3:
            res[n]["ressemblance"] = round(statistics.median(autres), 3)
    print("VISAGES", len(emb), flush=True)


@torch.inference_mode()
def vision():
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
    nom = (racine / "modele.txt").read_text().strip()
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(nom, torch_dtype=torch.bfloat16, device_map="cuda").eval()
    proc = AutoProcessor.from_pretrained(nom, min_pixels=256 * 28 * 28, max_pixels=1280 * 28 * 28)
    systeme, question, qdesc = [(racine / f).read_text() for f in ("systeme.txt", "question.txt", "ouinon_desc.txt")]
    tok = proc.tokenizer
    oui, non = [[tok.encode(m, add_special_tokens=False)[0] for m in l] for l in (("Yes", "yes"), ("No", "no"))]
    print("MODELE charge", flush=True)

    def entree(im, sysm, q):
        msgs = [{"role": "system", "content": [{"type": "text", "text": sysm}]},
                {"role": "user", "content": [{"type": "image", "image": im}, {"type": "text", "text": q}]}]
        return proc(text=[proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)], images=[im], return_tensors="pt").to("cuda")

    for x in lot:
        try:
            im, r = ouvrir(x, 1280), res[x["image"]]
            r["p"] = {}
            for k, (mode, q) in ouinon.items():
                ent = entree(im, "You answer with a single word: yes or no.", qdesc.format(desc=x["desc"], question=q) if mode else q + " Answer yes or no.")
                lg = model(**ent).logits[0, -1].float()
                r["p"][k] = round(float(torch.sigmoid(lg[oui].max() - lg[non].max())), 2)
            ent = entree(im, systeme, question.format(desc=x["desc"]))
            out = model.generate(**ent, max_new_tokens=160, do_sample=False)
            rep = proc.batch_decode(out[:, ent.input_ids.shape[1]:], skip_special_tokens=True)[0]
            m = re.search(r"[{].*[}]", rep, re.S)
            j = json.loads(m.group(0)) if m else {}
            for k, admis in cases.items():
                r[k] = j.get(k) if j.get(k) in admis else "?"
            r["people"] = int(j["people"]) if str(j.get("people")).isdigit() else -1
            r["score"] = max(0, min(10, int(float(j["score"])))) if re.fullmatch(r"[0-9.]+", str(j.get("score"))) else -1
            print("FAIT", x["image"], flush=True)
        except Exception as e:
            res[x["image"]]["illisible"] = True
            traceback.print_exc()
            print("RATE", x["image"], type(e).__name__, flush=True)


for f in (visages, vision):
    try:
        f()
    except Exception:
        traceback.print_exc()
    (racine / "out.json").write_text(json.dumps(res))
    torch.cuda.empty_cache()
'''
