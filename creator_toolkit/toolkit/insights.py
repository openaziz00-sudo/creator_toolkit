"""Hashtag performance and best posting times from your own history."""
from collections import defaultdict
from datetime import datetime
from statistics import mean, median
from zoneinfo import ZoneInfo

from . import config
from .analytics import eng_rate, latest_videos
from .util import TAG_RE, table


def hashtags(min_count: int = 2) -> None:
    vids = latest_videos()
    if not vids:
        print("No data. Run sync first.")
        return
    agg = defaultdict(list)
    for v in vids:
        for tag in {t.lower() for t in TAG_RE.findall(v["title"])}:
            agg[tag].append(v)
    rows = []
    for tag, vs in agg.items():
        if len(vs) >= min_count:
            rows.append((tag, len(vs), int(median(x["views"] for x in vs)),
                         mean(eng_rate(x) for x in vs) * 100))
    rows.sort(key=lambda r: (r[3], r[1]), reverse=True)
    if not rows:
        print(f"No hashtag used in >= {min_count} videos yet.")
        return
    table(["hashtag", "videos", "median views", "avg eng%"],
          [[f"#{t}", n, mv, f"{e:.1f}"] for t, n, mv, e in rows[:20]])
    print("\nTip: keep the top tags, drop the ones with many uses but low engagement.")


def besttime() -> None:
    vids = latest_videos()
    if len(vids) < 5:
        print("Need more videos (ideally 30+) for meaningful results.")
        return
    tz = ZoneInfo(config.TZ)
    by_hour, by_day = defaultdict(list), defaultdict(list)
    for v in vids:
        dt = datetime.fromtimestamp(v["created_at"], tz)
        by_hour[dt.hour].append(v["views"])
        by_day[dt.strftime("%A")].append(v["views"])

    def show(title, data, fmt):
        rows = sorted(data.items(), key=lambda kv: median(kv[1]), reverse=True)
        print(title)
        table(["slot", "videos", "median views"], [[fmt(k), len(v), int(median(v))] for k, v in rows[:5]])
        print()

    show(f"Best hours (timezone {config.TZ}):", by_hour, lambda h: f"{h:02d}:00")
    show("Best weekdays:", by_day, str)
    print("Median is used so one viral video doesn't skew the result. Slots with 1-2 videos are noise.")
