#!/usr/bin/env python3
"""Fetch YouTube's current mostPopular charts by country and assignable category.

Only the newest regional/category chart snapshot is written. The script does not
retain a time series or calculate historical cross-channel growth scores.
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
VIDEO_API_BASE = "https://www.googleapis.com/youtube/v3/videos"
CATEGORY_API_BASE = "https://www.googleapis.com/youtube/v3/videoCategories"


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


def api_get(base_url: str, params: dict[str, str], api_key: str) -> dict:
    query = urllib.parse.urlencode({**params, "key": api_key})
    request = urllib.request.Request(
        f"{base_url}?{query}",
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


def records_from(payload: dict, category_name: str = "") -> list[dict]:
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
            "category_name": category_name,
            "thumbnail": thumb(snippet),
            "view_count": int(stats.get("viewCount", 0) or 0),
        })
    return records


def main() -> int:
    now = utc_now()
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print("YOUTUBE_API_KEY is not configured; keeping the latest chart snapshot if it is still fresh.")
        try:
            current = json.loads(CURRENT_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            current = {"last_updated": None, "regions": {}, "categories": {}}
        stamp = parse_iso(current.get("last_updated"))
        if not stamp or now - stamp > timedelta(days=25):
            current = {"last_updated": None, "regions": {}, "categories": {}}
            CURRENT_PATH.parent.mkdir(parents=True, exist_ok=True)
            CURRENT_PATH.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
            print("Cleared stale chart data because no API key is configured.")
        return 0

    limit = min(50, max(1, int(CONFIG.get("max_videos_per_region", 50))))
    category_limit = min(50, max(1, int(CONFIG.get("max_videos_per_category", limit))))
    regions: dict[str, list[dict]] = {}
    categories: dict[str, dict[str, list[dict]]] = {}
    stamp = as_iso(now)

    for region in CONFIG.get("regions", []):
        code = str(region["code"]).upper()
        print(f"Fetching {region['name']} ({code})")

        # The all-category country chart powers the region homepage.
        try:
            regional_payload = api_get(VIDEO_API_BASE, {
                "part": "snippet,statistics,contentDetails",
                "chart": "mostPopular",
                "regionCode": code,
                "maxResults": str(limit),
            }, api_key)
        except RuntimeError as exc:
            raise RuntimeError(f"Overall chart failed for {code}: {exc}") from exc
        regions[code] = records_from(regional_payload)

        # Request the categories actually assignable in this country instead of
        # hard-coding category IDs that may not be available in every region.
        try:
            category_payload = api_get(CATEGORY_API_BASE, {
                "part": "snippet",
                "regionCode": code,
            }, api_key)
        except RuntimeError as exc:
            raise RuntimeError(f"Category list failed for {code}: {exc}") from exc

        country_categories: dict[str, list[dict]] = {}
        for category in category_payload.get("items", []):
            category_id = str(category.get("id", ""))
            snippet = category.get("snippet") or {}
            category_name = str(snippet.get("title", "")).strip()
            if not category_id or not category_name or not snippet.get("assignable", False):
                continue

            try:
                category_payload_for_videos = api_get(VIDEO_API_BASE, {
                    "part": "snippet,statistics,contentDetails",
                    "chart": "mostPopular",
                    "regionCode": code,
                    "videoCategoryId": category_id,
                    "maxResults": str(category_limit),
                }, api_key)
            except RuntimeError as exc:
                # A category can be assignable for uploads but have no chart
                # entity for this region. Skip not-found categories, but fail
                # loudly on quota, credentials, and other operational errors.
                if "returned HTTP 404" in str(exc):
                    print(
                        f"Skipping unavailable chart: {code} / {category_name} "
                        f"(category ID {category_id}; HTTP 404)",
                        flush=True,
                    )
                    continue
                raise RuntimeError(
                    f"Category chart failed for {code} / {category_name} "
                    f"(category ID {category_id}): {exc}"
                ) from exc

            records = records_from(category_payload_for_videos, category_name)
            if records:
                country_categories[category_id] = records

        categories[code] = country_categories
        print(
            f"{code}: {len(regions[code])} overall videos; "
            f"{sum(len(rows) for rows in country_categories.values())} category-chart videos "
            f"across {len(country_categories)} categories"
        )

    result = {"last_updated": stamp, "regions": regions, "categories": categories}
    CURRENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Saved latest snapshot at {stamp}: {len(regions)} countries, "
        f"{sum(len(value) for value in categories.values())} category charts"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
