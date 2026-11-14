import os
import time

from .http import request

API = "https://rest.runpod.io/v1"


def _h():
    key = os.environ.get("RUNPOD_API_KEY")
    if not key:
        raise SystemExit("RUNPOD_API_KEY manquante (server/.env)")
    return {"Authorization": f"Bearer {key}"}


def list_pods():
    return request("GET", f"{API}/pods", headers=_h())


def delete_pod(pod_id):
    request("DELETE", f"{API}/pods/{pod_id}", headers=_h())


def create_pod(cfg, name, env=None):
    body = {
        "name": name, "templateId": cfg["template_id"], "imageName": cfg["image"],
        "cloudType": "SECURE", "computeType": "GPU", "gpuCount": 1,
        "gpuTypeIds": cfg["gpu_types"], "gpuTypePriority": "custom",
        "dataCenterIds": [cfg["data_center"]], "networkVolumeId": cfg["volume_id"],
        "containerDiskInGb": cfg.get("container_disk_gb", 60),
        "ports": ["8188/http", "8888/http"], "interruptible": False,
    }
    if env:
        body["env"] = env
    last = None
    for attempt in range(cfg.get("create_attempts", 6)):
        try:
            pod = request("POST", f"{API}/pods", data=body, headers=_h())
            return pod["id"], pod.get("costPerHr"), (pod.get("machine") or {}).get("gpuTypeId")
        except RuntimeError as e:  # le plus souvent : aucune machine disponible
            last = e
            time.sleep(cfg.get("create_retry_s", 45))
    raise RuntimeError(f"creation du pod impossible : {last}")


def reap(prefix, max_age_min):
    """Supprime les pods du projet plus vieux que max_age_min. Filet de securite."""
    from datetime import datetime, timezone
    killed = []
    for p in list_pods():
        if not p.get("name", "").startswith(prefix):
            continue
        try:
            t = datetime.strptime(p["createdAt"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - t).total_seconds() / 60
        except Exception:
            age = max_age_min + 1
        if age > max_age_min:
            delete_pod(p["id"])
            killed.append(p["id"])
    return killed
