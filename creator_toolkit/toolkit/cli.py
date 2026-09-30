import argparse

from . import analytics, insights, scheduler


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="toolkit", description="Creator Toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("auth", help="authorise an account")
    a.add_argument("service", choices=["tiktok", "youtube"])

    sub.add_parser("sync", help="pull latest account + video stats from TikTok")
    sub.add_parser("report", help="growth report + promotion ROI")

    pr = sub.add_parser("promo", help="record / review paid promotion campaigns")
    ps = pr.add_subparsers(dest="sub", required=True)
    pa = ps.add_parser("add")
    pa.add_argument("--spend", type=float, required=True, help="USD spent")
    pa.add_argument("--goal", choices=["followers", "views", "likes", "profile"], default="followers")
    pa.add_argument("--video", help="TikTok video id")
    pa.add_argument("--views", type=int, default=0)
    pa.add_argument("--followers", type=int, default=0)
    pa.add_argument("--likes", type=int, default=0)
    pa.add_argument("--profile-views", type=int, default=0)
    pa.add_argument("--date", help="YYYY-MM-DD (default today)")
    pa.add_argument("--note")
    ps.add_parser("list")

    h = sub.add_parser("hashtags", help="which hashtags work for you")
    h.add_argument("--min", type=int, default=2)
    sub.add_parser("besttime", help="best hours / weekdays to post")

    q = sub.add_parser("queue", help="scheduled posts")
    qs = q.add_subparsers(dest="sub", required=True)
    qa = qs.add_parser("add")
    qa.add_argument("--file", required=True)
    qa.add_argument("--caption", required=True, help="text with #hashtags")
    qa.add_argument("--at", required=True, help='"YYYY-MM-DD HH:MM" in TOOLKIT_TZ')
    qa.add_argument("--platforms", default="tiktok,youtube,instagram")
    qs.add_parser("list")
    qr = qs.add_parser("retry"); qr.add_argument("id", type=int)
    qc = qs.add_parser("cancel"); qc.add_argument("id", type=int)

    r = sub.add_parser("run", help="run the scheduler")
    r.add_argument("--once", action="store_true", help="process due posts and exit (for cron)")

    args = p.parse_args(argv)

    if args.cmd == "auth":
        if args.service == "tiktok":
            from . import tiktok_api
            print("1) Open this link, log in and approve:\n\n" + tiktok_api.auth_url() + "\n")
            raw = input("2) Paste the full URL you were redirected to (or just the code): ").strip()
            tiktok_api.exchange_code(raw)
            print("TikTok authorised.")
        else:
            from . import youtube_api
            youtube_api.credentials()
            print("YouTube authorised.")
    elif args.cmd == "sync":
        analytics.sync()
    elif args.cmd == "report":
        analytics.report()
    elif args.cmd == "promo":
        if args.sub == "add":
            analytics.add_promo(args.video, args.spend, args.goal, args.views, args.followers,
                                args.likes, args.profile_views, args.date, args.note)
        else:
            analytics.promo_summary()
    elif args.cmd == "hashtags":
        insights.hashtags(args.min)
    elif args.cmd == "besttime":
        insights.besttime()
    elif args.cmd == "queue":
        if args.sub == "add":
            scheduler.add(args.file, args.caption, args.at, args.platforms)
        elif args.sub == "list":
            scheduler.list_queue()
        elif args.sub == "retry":
            scheduler.set_status(args.id, "pending")
        else:
            scheduler.set_status(args.id, "cancelled")
    elif args.cmd == "run":
        scheduler.run_due() if args.once else scheduler.run_forever()
