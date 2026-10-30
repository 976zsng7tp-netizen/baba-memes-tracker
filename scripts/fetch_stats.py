#!/usr/bin/env python3
"""Read Baba Memes numbers from the Facebook Graph API and write data.json + history.json.

Needs two environment variables (set as GitHub Actions secrets, never committed):
  FB_PAGE_ID     numeric Page id (100085147324156)
  FB_PAGE_TOKEN  long-lived Page access token

It never crashes on a single failed metric: whatever could be read is written, and the
reasons for anything that could not are listed under "errors" so the site can show them.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

GRAPH = "https://graph.facebook.com/v23.0"
PAGE_ID = os.environ.get("FB_PAGE_ID", "").strip()
TOKEN = os.environ.get("FB_PAGE_TOKEN", "").strip()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def call(path, **params):
    params["access_token"] = TOKEN
    url = f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        raise RuntimeError(msg.replace(TOKEN, "***"))


def total(resp):
    """Sum an insights response, whether it is a time series or a total_value."""
    s = 0
    for item in resp.get("data", []):
        if "total_value" in item:
            s += item["total_value"].get("value", 0) or 0
        for v in item.get("values", []):
            val = v.get("value", 0)
            s += val if isinstance(val, (int, float)) else 0
    return s


def insight(metric, since, until):
    last = None
    for extra in ({"period": "day", "metric_type": "total_value"}, {"period": "day"}):
        try:
            return total(call(f"{PAGE_ID}/insights", metric=metric, since=since, until=until, **extra))
        except RuntimeError as e:
            last = e
    raise last


def load(name, default):
    try:
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    if not PAGE_ID or not TOKEN:
        print("FB_PAGE_ID and FB_PAGE_TOKEN must be set", file=sys.stderr)
        return 1
    now = datetime.now(timezone.utc)
    prev = load("data.json", {})
    out = {
        "page_name": prev.get("page_name", "Baba Memes"),
        "captured_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Facebook Graph API",
        "followers": prev.get("followers"),
        "views": prev.get("views"),
        "views_window": "Last 28 days",
        "three_second_views": prev.get("three_second_views"),
        "one_minute_views": prev.get("one_minute_views"),
        "watch_time_seconds": prev.get("watch_time_seconds"),
        "errors": [],
    }
    try:
        info = call(PAGE_ID, fields="name,followers_count,fan_count")
        out["page_name"] = info.get("name", out["page_name"])
        out["followers"] = info.get("followers_count", info.get("fan_count"))
    except RuntimeError as e:
        out["errors"].append(f"followers: {e}")

    since = int((now - timedelta(days=28)).timestamp())
    until = int(now.timestamp())
    for key, metrics in (
        ("views", ["page_media_view", "page_views_total"]),
        ("three_second_views", ["page_video_views_3s", "page_video_views"]),
        ("watch_time_seconds", ["page_video_view_time"]),
    ):
        done = False
        errs = []
        for m in metrics:
            try:
                val = insight(m, since, until)
                out[key] = round(val / 1000) if key == "watch_time_seconds" and m == "page_video_view_time" else val
                done = True
                break
            except RuntimeError as e:
                errs.append(f"{m}: {e}")
        if not done:
            out["errors"].append(f"{key}: " + " | ".join(errs)[:240])

    with open(os.path.join(ROOT, "data.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    hist = load("history.json", [])
    hist.append({"t": out["captured_at"], "followers": out["followers"], "views": out["views"]})
    with open(os.path.join(ROOT, "history.json"), "w", encoding="utf-8") as f:
        json.dump(hist[-1000:], f)
    print("ok", {k: out[k] for k in ("followers", "views")}, "errors:", len(out["errors"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
