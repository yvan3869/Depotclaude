import time
from urllib.parse import urlencode

from .http import multipart, request


class Comfy:
    def __init__(self, pod_id):
        self.base = f"https://{pod_id}-8188.proxy.runpod.net"

    def wait_ready(self, timeout=600):
        t = time.time()
        while time.time() - t < timeout:
            try:
                request("GET", self.base + "/system_stats", timeout=15)
                return
            except Exception:
                time.sleep(10)
        raise RuntimeError("ComfyUI n'a pas demarre a temps")

    def models(self, folder):
        """Fichiers d'un dossier de modeles du volume, tels que ComfyUI les liste."""
        # Juste apres le demarrage, le relais RunPod repond parfois 404 quelques secondes : reessayer.
        for k in range(6):
            try:
                return list(request("GET", f"{self.base}/models/{folder}"))
            except Exception:
                if k == 5:
                    raise
                time.sleep(10)

    def has_model(self, folder, name):
        return name in self.models(folder)

    def upload(self, name, content):
        body, h = multipart({"overwrite": "true"}, "image", name, content)
        return request("POST", self.base + "/upload/image", data=body, headers=h)["name"]

    def run(self, graph, timeout=1800):
        """Lance un workflow et renvoie la liste des fichiers produits (dicts filename/subfolder/type)."""
        r = request("POST", self.base + "/prompt", data={"prompt": graph})
        pid = r["prompt_id"]
        t = time.time()
        while time.time() - t < timeout:
            try:
                h = request("GET", f"{self.base}/history/{pid}", timeout=30) or {}
            except Exception:
                h = {}
            if pid in h:
                for m in h[pid]["status"].get("messages", []):
                    if m[0] == "execution_error":
                        raise RuntimeError(f"erreur ComfyUI : {m[1].get('exception_message', '')[:300]}")
                files = []
                for o in h[pid].get("outputs", {}).values():
                    for lst in o.values():
                        if isinstance(lst, list):
                            files += [f for f in lst if isinstance(f, dict) and "filename" in f]
                return files
            time.sleep(4)
        raise RuntimeError("delai depasse pour le workflow")

    def fetch(self, f):
        q = urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")})
        return request("GET", f"{self.base}/view?{q}", raw=True, timeout=300)
