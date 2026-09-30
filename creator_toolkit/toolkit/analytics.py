"""Sync account/video stats and turn them into decisions (cost per follower, what to promote)."""
import time
from datetime import date

from . import db, tiktok_api
from .util import short, table

LATEST = """
SELECT v.id, v.title, v.created_at, s.views, s.likes, s.comments, s.shares
FROM videos v JOIN snapshots s ON s.video_id = v.id
WHERE s.taken_at = (SELECT MAX(taken_at) FROM snapshots WHERE video_id = v.id)
"""


def latest_videos() -> list:
    with db.conn() as c:
        return [dict(r) for r in c.execute(LATEST)]


def eng_rate(v: dict) -> float:
    return (v["likes"] + v["comments"] + v["shares"]) / v["views"] if v["views"] else 0.0


def sync() -> None:
    now = int(time.time())
    user = tiktok_api.user_info()
    videos = tiktok_api.list_videos(200)
    with db.conn() as c:
        c.execute("INSERT INTO account_snapshots VALUES (?,?,?,?,?)", (
            now, user.get("follower_count") or 0, user.get("following_count") or 0,
            user.get("likes_count") or 0, user.get("video_count") or 0))
        for v in videos:
            text = v.get("video_description") or v.get("title") or ""
            c.execute("INSERT OR REPLACE INTO videos VALUES (?,?,?,?)",
                      (v["id"], text, v.get("create_time") or 0, v.get("cover_image_url")))
            c.execute("INSERT INTO snapshots VALUES (?,?,?,?,?,?)", (
                v["id"], now, v.get("view_count") or 0, v.get("like_count") or 0,
                v.get("comment_count") or 0, v.get("share_count") or 0))
    print(f"Synced {len(videos)} videos. Followers now: {user.get('follower_count')}")


# ------------------------------------------------------------ promotions
def add_promo(video_id, spend, goal, views, followers, likes, profile_views, started, note) -> None:
    with db.conn() as c:
        c.execute("""INSERT INTO promotions(video_id, started, goal, spend, views, followers,
                     likes, profile_views, note) VALUES (?,?,?,?,?,?,?,?,?)""",
                  (video_id, started or date.today().isoformat(), goal, spend,
                   views, followers, likes, profile_views, note))
    print("Campaign saved.")


def promo_summary() -> None:
    with db.conn() as c:
        rows = c.execute("SELECT * FROM promotions ORDER BY id").fetchall()
    if not rows:
        print("No campaigns yet. Add one: python -m toolkit promo add --spend 1.8 --goal followers ...")
        return
    out = []
    for r in rows:
        cpf = f"{r['spend'] / r['followers']:.3f}" if r["followers"] else "-"
        cpm = f"{r['spend'] / r['views'] * 1000:.3f}" if r["views"] else "-"
        out.append([r["id"], r["started"], r["goal"], f"{r['spend']:.2f}", r["views"],
                    r["followers"], r["likes"], cpf, cpm])
    table(["id", "date", "goal", "spend$", "views", "followers", "likes", "$/follower", "$/1K views"], out)
    spend = sum(r["spend"] for r in rows)
    fol = sum(r["followers"] for r in rows)
    views = sum(r["views"] for r in rows)
    print(f"\nTotal spend ${spend:.2f} | followers {fol} | views {views}")
    if fol:
        print(f"Blended cost per follower: ${spend / fol:.3f}")


# ------------------------------------------------------------ report
def report() -> None:
    now = int(time.time())
    with db.conn() as c:
        last = c.execute("SELECT * FROM account_snapshots ORDER BY taken_at DESC LIMIT 1").fetchone()
        week = c.execute("SELECT * FROM account_snapshots WHERE taken_at <= ? "
                         "ORDER BY taken_at DESC LIMIT 1", (now - 7 * 86400,)).fetchone()
        promoted = {r[0] for r in c.execute("SELECT video_id FROM promotions WHERE video_id IS NOT NULL")}
    if not last:
        print("No data yet. Run: python -m toolkit sync")
        return

    print(f"Followers: {last['followers']} | Total likes: {last['likes']} | Videos: {last['videos']}")
    if week:
        print(f"Change vs 7 days ago: {last['followers'] - week['followers']:+d} followers")

    vids = [v for v in latest_videos() if v["views"] >= 50]
    vids.sort(key=eng_rate, reverse=True)
    print("\nTop videos by engagement rate (views >= 50):")
    table(["id", "title", "views", "eng%"],
          [[v["id"][-6:], short(v["title"]), v["views"], f"{eng_rate(v) * 100:.1f}"] for v in vids[:10]])

    cand = [v for v in vids if v["id"] not in promoted][:5]
    print("\nBest candidates if you decide to promote (strong organic engagement, never promoted):")
    table(["id", "title", "views", "eng%"],
          [[v["id"], short(v["title"]), v["views"], f"{eng_rate(v) * 100:.1f}"] for v in cand])

    print("\nPromotion history:")
    promo_summary()
