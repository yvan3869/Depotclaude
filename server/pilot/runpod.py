import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from .http import request

API = "https://rest.runpod.io/v1"
PREFIX = "girls-ai-"
# Plafond de depense GPU par jour (heure de Paris), commun a tous les lanceurs : pilote, page Test,
# "lora add", agents. Reglable par infra.daily_cap_usd (persona/production.yaml) ou GPU_DAILY_CAP_USD.
DEFAULT_CAP = 7.5
REAP_MIN = 105  # age maximal d'un pod (girls-ai-pod-reaper) : borne d'un pod dont la fin n'est pas connue


def _h():
    key = os.environ.get("RUNPOD_API_KEY")
    if not key:
        raise SystemExit("RUNPOD_API_KEY manquante (server/.env)")
    return {"Authorization": f"Bearer {key}"}


def list_pods():
    return request("GET", f"{API}/pods", headers=_h())


def _ledger():
    return Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[1] / "data")) / "depenses.jsonl"


def _record(**e):
    try:
        with open(_ledger(), "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.time(), **e}) + "\n")
    except OSError:
        pass  # le registre ne doit jamais empecher de supprimer un pod


def _day(ts):
    try:
        from zoneinfo import ZoneInfo
        return datetime.fromtimestamp(ts, ZoneInfo("Europe/Paris")).date()
    except Exception:
        return datetime.fromtimestamp(ts, timezone.utc).date()


def _created(p):
    try:
        return datetime.strptime(p["createdAt"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return None


def spent_today():
    """Depense GPU du jour : pods du registre demarres aujourd'hui, plus les pods du projet
    en cours qui n'y figurent pas (crees depuis une autre machine). Estimation : tarif x duree."""
    now, today = time.time(), _day(time.time())
    pods, ends, manual = {}, {}, []
    if _ledger().exists():
        for line in _ledger().read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("ev") == "create":
                pods[e["id"]] = e
            elif e.get("ev") == "delete":
                ends[e["id"]] = e["t"]
            elif e.get("ev") == "manual" and _day(e["t"]) == today:  # depense notee a la main
                manual.append(e.get("usd", 0))
    live = {p["id"]: p for p in list_pods() if p.get("name", "").startswith(PREFIX)}
    total = float(sum(manual))
    for pid, e in pods.items():
        if _day(e["t"]) != today:
            continue
        end = ends.get(pid) or (now if pid in live else min(now, e["t"] + REAP_MIN * 60))
        total += (e.get("rate") or 0) * max(0, end - e["t"]) / 3600
    for pid, p in live.items():
        t = _created(p)
        if pid not in pods and t:
            total += (p.get("costPerHr") or 0) * max(0, now - max(t, now - REAP_MIN * 60)) / 3600
    return round(total, 2)


def daily_cap(cfg=None):
    v = os.environ.get("GPU_DAILY_CAP_USD") or (cfg or {}).get("daily_cap_usd") or DEFAULT_CAP
    return float(v)


def delete_pod(pod_id):
    request("DELETE", f"{API}/pods/{pod_id}", headers=_h())
    _record(ev="delete", id=pod_id)


def create_pod(cfg, name, env=None):
    cap, spent = daily_cap(cfg), spent_today()
    if spent >= cap:
        raise RuntimeError(f"plafond GPU du jour atteint : {spent} $ depenses sur {cap} $ (reglage : "
                           f"infra.daily_cap_usd ou GPU_DAILY_CAP_USD). Aucun pod cree.")
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
            _record(ev="create", id=pod["id"], name=name, rate=pod.get("costPerHr"))
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
