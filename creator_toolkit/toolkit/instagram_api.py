"""Instagram Graph API – publish Reels via resumable upload (no public URL needed)."""
import os
import time

import requests

from . import config


def _graph() -> str:
    return f"https://graph.facebook.com/{config.IG_API_VERSION}"


def publish_reel(path: str, caption: str) -> str:
    if not (config.IG_USER_ID and config.IG_ACCESS_TOKEN):
        raise RuntimeError("Set IG_USER_ID and IG_ACCESS_TOKEN in .env")
    token, size = config.IG_ACCESS_TOKEN, os.path.getsize(path)

    r = requests.post(f"{_graph()}/{config.IG_USER_ID}/media", timeout=60, data={
        "media_type": "REELS", "upload_type": "resumable",
        "caption": caption, "access_token": token}).json()
    if "id" not in r:
        raise RuntimeError(f"Instagram container: {r}")
    container = r["id"]
    upload_uri = r.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{config.IG_API_VERSION}/{container}"

    with open(path, "rb") as f:
        up = requests.post(upload_uri, data=f, timeout=900, headers={
            "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)})
    if not up.ok:
        raise RuntimeError(f"Instagram upload: {up.status_code} {up.text[:200]}")

    for _ in range(90):  # up to ~7.5 min of processing
        s = requests.get(f"{_graph()}/{container}", timeout=30, params={
            "fields": "status_code,status", "access_token": token}).json()
        code = s.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram processing failed: {s}")
        time.sleep(5)
    else:
        raise TimeoutError("Instagram processing timed out")

    pub = requests.post(f"{_graph()}/{config.IG_USER_ID}/media_publish", timeout=60, data={
        "creation_id": container, "access_token": token}).json()
    if "id" not in pub:
        raise RuntimeError(f"Instagram publish: {pub}")
    return pub["id"]
