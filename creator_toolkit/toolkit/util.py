import re

TAG_RE = re.compile(r"#(\w+)", re.UNICODE)


def table(headers, rows):
    rows = [[("" if x is None else str(x)) for x in r] for r in rows]
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(v.ljust(w) for v, w in zip(r, widths)))


def short(text, n=40):
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


def split_caption(caption):
    """Return (title_without_hashtags, [tags])."""
    tags = TAG_RE.findall(caption)
    first_line = TAG_RE.sub("", caption).strip().split("\n")[0].strip()
    return (first_line[:90] or "Video"), tags
