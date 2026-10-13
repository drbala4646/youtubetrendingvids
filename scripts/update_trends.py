#!/usr/bin/env python3
"""Fetch the current YouTube mostPopular chart for each configured region.

This deliberately stores only the latest regional chart snapshot. It does not
calculate historical cross-channel view-growth scores or retain a time series.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
CURRENT_PATH = ROOT / "data" / "current.json"
API_BASE = "https://www.googleapis.com/youtube/v3/videos"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def as_iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def api_get(params: dict[str, str], api_key: str) -> dict:
    query = urllib.parse.urlencode({**params, "key": api_key})
    request = urllib.request.Request(
        f"{API_BASE}?{query}",
        headers={"User-Agent": "TrendPulse/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"YouTube Data API returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not reach YouTube Data API: {exc}") from exc


def thumb(snippet: dict) -> str:
    thumbnails = snippet.get("thumbnails", {})
    for key in ("maxres", "standard", "high", "medium", "default"):
        value = thumbnails.get(key, {}).get("url")
        if value:
            return value
    return ""


def main() -> int:
    now = utc_now()
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print("YOUTUBE_API_KEY is not configured; keeping the latest chart snapshot if it is still fresh.")
        try:
            current = json.loads(CURRENT_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            current = {"last_updated": None, "regions": {}}
        stamp = parse_iso(current.get("last_updated"))
        # Don't keep stale public YouTube API data around indefinitely if updating is disabled.
        if not stamp or now - stamp > timedelta(days=25):
            current = {"last_updated": None, "regions": {}}
            CURRENT_PATH.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
            print("Cleared stale chart data because no API key is configured.")
        return 0

    stamp = as_iso(now)
    regions: dict[str, list[dict]] = {}
    for region in CONFIG.get("regions", []):
        code = str(region["code"]).upper()
        limit = min(50, max(1, int(CONFIG.get("max_videos_per_region", 50))))
        payload = api_get({
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": code,
            "maxResults": str(limit),
        }, api_key)
        records = []
        for position, item in enumerate(payload.get("items", []), start=1):
            video_id = item.get("id")
            snippet = item.get("snippet") or {}
            stats = item.get("statistics") or {}
            if not video_id:
                continue
            records.append({
                "id": video_id,
                "position": position,
                "title": snippet.get("title", "Untitled YouTube video"),
                "channel_title": snippet.get("channelTitle", "YouTube creator"),
                "description": (snippet.get("description") or "")[:500],
                "published_at": snippet.get("publishedAt", ""),
                "category_id": str(snippet.get("categoryId", "0")),
                "thumbnail": thumb(snippet),
                "view_count": int(stats.get("viewCount", 0) or 0),
            })
        regions[code] = records
        print(f"{code}: fetched {len(records)} videos from YouTube's mostPopular chart")

    result = {"last_updated": stamp, "regions": regions}
    CURRENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved current chart snapshot at {stamp}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
