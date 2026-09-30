"""Official TikTok APIs: Login Kit (OAuth), Display API (stats), Content Posting API."""
import os
import time
import urllib.parse

import requests

from . import config

API = "https://open.tiktokapis.com"
MB = 1024 * 1024


def scopes() -> str:
    publish = "video.upload" if config.TIKTOK_MODE == "inbox" else "video.publish"
    return f"user.info.basic,user.info.stats,video.list,{publish}"


# ---------------------------------------------------------------- OAuth
def auth_url() -> str:
    params = {
        "client_key": config.TIKTOK_CLIENT_KEY,
        "scope": scopes(),
        "response_type": "code",
        "redirect_uri": config.TIKTOK_REDIRECT_URI,
        "state": "toolkit",
    }
    return "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(params)


def _save(token: dict) -> None:
    if "access_token" not in token:
        raise RuntimeError(f"TikTok auth failed: {token}")
    token["obtained_at"] = int(time.time())
    tokens = config.load_tokens()
    tokens["tiktok"] = token
    config.save_tokens(tokens)


def _token_request(data: dict) -> None:
    data.update(client_key=config.TIKTOK_CLIENT_KEY, client_secret=config.TIKTOK_CLIENT_SECRET)
    r = requests.post(f"{API}/v2/oauth/token/", data=data, timeout=30)
    _save(r.json())


def exchange_code(raw: str) -> None:
    """Accepts either the bare code or the full redirect URL."""
    if "code=" in raw:
        code = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)["code"][0]
    else:
        code = urllib.parse.unquote(raw)
    _token_request({"grant_type": "authorization_code", "code": code,
                    "redirect_uri": config.TIKTOK_REDIRECT_URI})


def _access_token() -> str:
    tok = config.load_tokens().get("tiktok")
    if not tok:
        raise RuntimeError("Not authorised. Run: python -m toolkit auth tiktok")
    if time.time() > tok["obtained_at"] + tok["expires_in"] - 300:
        _token_request({"grant_type": "refresh_token", "refresh_token": tok["refresh_token"]})
        tok = config.load_tokens()["tiktok"]
    return tok["access_token"]


def _call(method: str, path: str, **kw) -> dict:
    headers = {"Authorization": f"Bearer {_access_token()}",
               "Content-Type": "application/json; charset=UTF-8"}
    r = requests.request(method, API + path, headers=headers, timeout=60, **kw)
    body = r.json()
    err = body.get("error", {})
    if err.get("code", "ok") != "ok":
        raise RuntimeError(f"TikTok {path}: {err.get('code')} - {err.get('message')}")
    return body.get("data", {})


# ---------------------------------------------------------------- stats
def user_info() -> dict:
    fields = "open_id,display_name,follower_count,following_count,likes_count,video_count"
    return _call("GET", "/v2/user/info/", params={"fields": fields}).get("user", {})


def list_videos(limit: int = 200) -> list:
    fields = ("id,title,video_description,create_time,cover_image_url,"
              "view_count,like_count,comment_count,share_count")
    out, cursor = [], None
    while len(out) < limit:
        body = {"max_count": 20}
        if cursor:
            body["cursor"] = cursor
        data = _call("POST", "/v2/video/list/", params={"fields": fields}, json=body)
        out += data.get("videos", [])
        if not data.get("has_more"):
            break
        cursor = data.get("cursor")
    return out[:limit]


# ---------------------------------------------------------------- posting
def post_video(path: str, caption: str) -> str:
    size = os.path.getsize(path)
    if size <= 64 * MB:
        chunk, total = size, 1
    else:  # last chunk absorbs the remainder (allowed up to 128 MB)
        chunk = 10 * MB
        total = size // chunk

    source = {"source": "FILE_UPLOAD", "video_size": size,
              "chunk_size": chunk, "total_chunk_count": total}
    if config.TIKTOK_MODE == "inbox":
        init_path, body = "/v2/post/publish/inbox/video/init/", {"source_info": source}
    else:
        init_path = "/v2/post/publish/video/init/"
        body = {"post_info": {"title": caption[:2200],
                              "privacy_level": config.TIKTOK_PRIVACY,
                              "disable_duet": False, "disable_comment": False,
                              "disable_stitch": False},
                "source_info": source}

    data = _call("POST", init_path, json=body)
    upload_url, publish_id = data["upload_url"], data["publish_id"]

    with open(path, "rb") as f:
        for i in range(total):
            start = i * chunk
            end = size - 1 if i == total - 1 else start + chunk - 1
            blob = f.read(end - start + 1)
            r = requests.put(upload_url, data=blob, timeout=600, headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(len(blob)),
                "Content-Range": f"bytes {start}-{end}/{size}"})
            if r.status_code not in (200, 201, 206):
                raise RuntimeError(f"TikTok upload chunk {i + 1}/{total}: {r.status_code} {r.text[:200]}")
    return publish_id


def wait_publish(publish_id: str, timeout: int = 600) -> str:
    end = time.time() + timeout
    while time.time() < end:
        d = _call("POST", "/v2/post/publish/status/fetch/", json={"publish_id": publish_id})
        status = d.get("status")
        if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            return status
        if status == "FAILED":
            raise RuntimeError(f"TikTok publish failed: {d.get('fail_reason')}")
        time.sleep(5)
    raise TimeoutError("TikTok publish status timed out")
