import json
import os
import ssl
import urllib.error
import urllib.request
import uuid

UA = "curl/8.5.0"  # le proxy RunPod refuse l'agent par defaut de urllib
_ctx = ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE") or None)


def request(method, url, data=None, headers=None, timeout=120, raw=False):
    h = {"User-Agent": UA}
    h.update(headers or {})
    body = None
    if data is not None and not isinstance(data, (bytes, bytearray)):
        body = json.dumps(data).encode()
        h.setdefault("Content-Type", "application/json")
    elif data is not None:
        body = data
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r:
            out = r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url.split('?')[0]} -> HTTP {e.code}: {e.read()[:300]!r}") from None
    if raw:
        return out
    return json.loads(out) if out else None


def multipart(fields, file_field, filename, content):
    b = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
                 f'Content-Type: application/octet-stream\r\n\r\n'.encode() + content + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    return b"".join(parts), {"Content-Type": f"multipart/form-data; boundary={b}"}
