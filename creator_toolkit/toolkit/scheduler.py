"""Post queue: schedule a video to TikTok / YouTube Shorts / Instagram Reels."""
import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config, db
from .util import short, split_caption, table


def _tiktok(path, caption):
    from . import tiktok_api
    pid = tiktok_api.post_video(path, caption)
    return f"{pid} ({tiktok_api.wait_publish(pid)})"


def _youtube(path, caption):
    from . import youtube_api
    title, tags = split_caption(caption)
    return youtube_api.upload_short(path, title, caption, tags)


def _instagram(path, caption):
    from . import instagram_api
    return instagram_api.publish_reel(path, caption)


PUBLISHERS = {"tiktok": _tiktok, "youtube": _youtube, "instagram": _instagram}


def parse_when(text: str) -> int:
    dt = datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(config.TZ))
    return int(dt.timestamp())


def add(file, caption, at, platforms) -> None:
    path = os.path.abspath(file)
    if not os.path.isfile(path):
        raise SystemExit(f"File not found: {path}")
    plats = [p.strip() for p in platforms.split(",") if p.strip()]
    bad = [p for p in plats if p not in PUBLISHERS]
    if bad:
        raise SystemExit(f"Unknown platform(s): {bad}. Choose from {list(PUBLISHERS)}")
    with db.conn() as c:
        cur = c.execute("INSERT INTO queue(file, caption, platforms, run_at) VALUES (?,?,?,?)",
                        (path, caption, json.dumps(plats), parse_when(at)))
    print(f"Queued #{cur.lastrowid} for {at} ({config.TZ}) -> {', '.join(plats)}")


def list_queue() -> None:
    with db.conn() as c:
        rows = c.execute("SELECT * FROM queue ORDER BY run_at").fetchall()
    tz = ZoneInfo(config.TZ)
    table(["id", "when", "status", "platforms", "caption", "results"], [[
        r["id"], datetime.fromtimestamp(r["run_at"], tz).strftime("%Y-%m-%d %H:%M"),
        r["status"], ",".join(json.loads(r["platforms"])), short(r["caption"], 30),
        short(json.dumps(json.loads(r["results"]), ensure_ascii=False), 60)] for r in rows])


def set_status(qid: int, status: str) -> None:
    with db.conn() as c:
        c.execute("UPDATE queue SET status=? WHERE id=?", (status, qid))
    print(f"#{qid} -> {status}")


def _process(row) -> None:
    results = json.loads(row["results"] or "{}")
    for plat in json.loads(row["platforms"]):
        if results.get(plat, {}).get("status") == "ok":
            continue  # already posted, never double-post on retry
        try:
            results[plat] = {"status": "ok", "id": PUBLISHERS[plat](row["file"], row["caption"])}
            print(f"[#{row['id']}] {plat}: posted")
        except Exception as exc:  # keep going with the other platforms
            results[plat] = {"status": "error", "error": str(exc)[:300]}
            print(f"[#{row['id']}] {plat}: FAILED - {exc}")
    oks = [r["status"] == "ok" for r in results.values()]
    status = "done" if all(oks) else ("partial" if any(oks) else "failed")
    with db.conn() as c:
        c.execute("UPDATE queue SET status=?, results=? WHERE id=?",
                  (status, json.dumps(results), row["id"]))


def run_due() -> None:
    with db.conn() as c:
        rows = c.execute("SELECT * FROM queue WHERE status='pending' AND run_at<=?",
                         (int(time.time()),)).fetchall()
    for row in rows:
        _process(row)


def run_forever(interval: int = 30) -> None:
    print(f"Scheduler running (checking every {interval}s). Ctrl+C to stop.")
    while True:
        run_due()
        time.sleep(interval)
