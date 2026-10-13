#!/usr/bin/env python3
"""Build pre-rendered, crawlable HTML pages for TrendPulse."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

CATEGORY_NAMES = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music",
    "15": "Pets & Animals", "17": "Sports", "19": "Travel & Events",
    "20": "Gaming", "22": "People & Blogs", "23": "Comedy",
    "24": "Entertainment", "25": "News & Politics", "26": "Howto & Style",
    "27": "Education", "28": "Science & Technology", "29": "Nonprofits & Activism",
    "30": "Movies", "31": "Anime & Animation", "32": "Action & Adventure",
    "33": "Classics", "34": "Comedy (Film)", "35": "Documentary",
    "36": "Drama", "37": "Family", "38": "Foreign", "39": "Horror",
    "40": "Sci-Fi & Fantasy", "41": "Thriller", "42": "Shorts", "43": "Shows",
    "44": "Trailers"
}

CSS = r"""
:root {
  color-scheme: light dark;
  --bg: light-dark(#f5f7fb, #0b1020);
  --surface: light-dark(#ffffff, #121a2c);
  --surface-2: light-dark(#eef2f8, #1a253a);
  --text: light-dark(#172033, #f4f7ff);
  --muted: light-dark(#647087, #9ca9c4);
  --border: light-dark(#dfe5ef, #29354c);
  --accent: #6b7cff;
  --accent-2: #8a5cff;
  --green: light-dark(#0b805a, #5fe2b1);
  --shadow: 0 12px 35px rgba(14, 24, 47, .09);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--bg); color: var(--text); font: 15px/1.55 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.visually-hidden { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
a { color: inherit; text-decoration: none; }
a:hover { color: var(--accent); }
button, input, select { font: inherit; }
.site-shell { min-height: 100vh; }
.topbar { border-bottom: 1px solid var(--border); background: var(--surface); position: sticky; top: 0; z-index: 10; }
.topbar-inner { max-width: 1240px; margin: 0 auto; padding: 14px 24px; display: flex; align-items: center; gap: 26px; }
.brand { display: inline-flex; align-items: center; gap: 10px; font-weight: 850; letter-spacing: -.04em; font-size: 21px; white-space: nowrap; }
.brand-mark { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 11px; color: white; background: linear-gradient(135deg, var(--accent), var(--accent-2)); box-shadow: 0 6px 16px #6b7cff42; }
.brand-mark svg { width: 17px; height: 17px; }
.nav-links { display: flex; align-items: center; gap: 20px; color: var(--muted); font-size: 13px; font-weight: 700; white-space: nowrap; }
.top-actions { display: flex; align-items: center; gap: 10px; margin-left: auto; }
.region-select, .search-input, .sort-select { border: 1px solid var(--border); background: var(--surface); color: var(--text); border-radius: 12px; padding: 10px 12px; outline: none; }
.region-select { max-width: 180px; font-weight: 650; }
.search-wrap { position: relative; width: min(260px, 24vw); }
.search-wrap svg { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--muted); width: 16px; pointer-events: none; }
.search-input { padding-left: 37px; width: 100%; }
main { max-width: 1240px; margin: 0 auto; padding: 30px 24px 66px; }
.hero { position: relative; overflow: hidden; display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(270px, .7fr); gap: 28px; align-items: center; padding: clamp(26px, 5vw, 52px); border: 1px solid #818dff42; border-radius: 28px; background: radial-gradient(ellipse at 85% 10%, #8d5dff2c, transparent 44%), radial-gradient(ellipse at 8% 105%, #557aff2a, transparent 45%), var(--surface); box-shadow: var(--shadow); }
.eyebrow { display: inline-flex; gap: 8px; align-items: center; color: var(--accent); text-transform: uppercase; letter-spacing: .13em; font-weight: 850; font-size: 11px; }
.pulse-dot { width: 7px; height: 7px; display: inline-block; background: #19ce96; border-radius: 50%; box-shadow: 0 0 0 5px #19ce9624; }
h1 { max-width: 730px; margin: 14px 0 15px; font-size: clamp(36px, 5.6vw, 61px); line-height: 1.02; letter-spacing: -.06em; }
.gradient-text { color: var(--accent); background: linear-gradient(90deg, #7186ff, #b17aff 75%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.hero-copy { color: var(--muted); max-width: 610px; font-size: 16px; margin: 0; }
.hero-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 25px; }
.pill { display: inline-flex; align-items: center; gap: 7px; background: var(--surface-2); border: 1px solid var(--border); border-radius: 999px; padding: 8px 12px; font-size: 12px; color: var(--muted); font-weight: 700; }
.hero-art { min-height: 190px; position: relative; display: flex; justify-content: center; align-items: center; }
.play-orbit { width: min(245px, 80%); aspect-ratio: 1; border-radius: 50%; background: radial-gradient(circle, #7984ff28 0 25%, transparent 26% 39%, #7984ff18 40% 41%, transparent 42% 59%, #a26cff20 60% 61%, transparent 62%), linear-gradient(145deg, #7a8bff22, #ab68ff12); border: 1px solid #8b88ff42; display: grid; place-items: center; transform: rotate(-10deg); }
.play-box { transform: rotate(10deg); width: 94px; height: 70px; display: grid; place-items: center; background: linear-gradient(135deg, #ff4f65, #fb3451); color: white; border-radius: 24px; box-shadow: 0 20px 45px #ff365c44; }
.play-box svg { width: 34px; height: 34px; margin-left: 4px; }
.orbit-chip { position: absolute; display: flex; align-items: center; gap: 7px; padding: 9px 12px; border: 1px solid var(--border); background: var(--surface); box-shadow: var(--shadow); border-radius: 13px; font-size: 12px; font-weight: 800; }
.orbit-chip strong { color: var(--green); }
.chip-one { top: 8%; right: 0; }.chip-two { bottom: 7%; left: 0; }
.ad-slot { min-height: 78px; border: 1px dashed var(--border); background: var(--surface); border-radius: 14px; display: flex; justify-content: center; align-items: center; margin: 22px 0 30px; padding: 8px; overflow: hidden; }
.ad-label { text-transform: uppercase; font-size: 10px; letter-spacing: .16em; color: var(--muted); }
.ad-slot:has(iframe), .ad-slot:has(img), .ad-slot:has(script) { border-style: solid; }
.section-head { display: flex; justify-content: space-between; align-items: end; gap: 18px; margin: 32px 0 16px; }
.section-head h2 { font-size: clamp(23px, 3vw, 31px); line-height: 1.1; letter-spacing: -.04em; margin: 0; }
.section-head p { margin: 6px 0 0; color: var(--muted); font-size: 13px; }
.control-row { display: flex; justify-content: space-between; align-items: center; gap: 15px; margin-bottom: 16px; }
.category-pills { display: flex; flex-wrap: wrap; gap: 8px; }
.category-pill { border: 1px solid var(--border); background: var(--surface); color: var(--muted); border-radius: 999px; padding: 8px 13px; font-size: 12px; font-weight: 750; cursor: pointer; }
.category-pill:hover, .category-pill.active { background: #7186ff17; border-color: #7186ff77; color: var(--accent); }
.sort-select { font-size: 12px; padding: 9px 11px; }
.results-count { color: var(--muted); font-size: 12px; white-space: nowrap; margin: 0 0 12px; }
.video-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 19px; }
.video-card { min-width: 0; overflow: hidden; border-radius: 19px; background: var(--surface); border: 1px solid var(--border); transition: transform .18s ease, box-shadow .18s ease; }
.video-card:hover { transform: translateY(-3px); box-shadow: var(--shadow); }
.thumb-wrap { aspect-ratio: 16/9; position: relative; overflow: hidden; background: var(--surface-2); }
.thumb { width: 100%; height: 100%; display: block; object-fit: cover; }
.thumb-fallback { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #303b78, #6c4aaf 58%, #df537d); color: white; font-size: 34px; font-weight: 900; letter-spacing: -.06em; }
.rank-badge { position: absolute; top: 11px; left: 11px; border-radius: 9px; background: #0b1020df; color: white; padding: 5px 8px; font-size: 11px; font-weight: 850; backdrop-filter: blur(8px); }
.watch-badge { position: absolute; right: 11px; bottom: 11px; display: grid; place-items: center; width: 35px; height: 27px; border-radius: 8px; background: #ff3d55; color: white; }
.watch-badge svg { width: 15px; height: 15px; }
.video-body { padding: 15px 15px 16px; }
.video-category { display: inline-block; color: var(--accent); text-transform: uppercase; font-size: 10px; font-weight: 850; letter-spacing: .1em; margin-bottom: 7px; }
.video-title { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 47px; margin: 0 0 7px; font-size: 16px; font-weight: 820; line-height: 1.45; letter-spacing: -.02em; }
.creator { color: var(--muted); font-size: 12px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.video-stats { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 15px; padding-top: 13px; border-top: 1px solid var(--border); }
.view-total { font-size: 12px; font-weight: 800; }
.growth { display: inline-flex; align-items: center; gap: 4px; color: var(--green); background: light-dark(#eaf9f2, #123327); border-radius: 8px; padding: 5px 7px; font-size: 10px; font-weight: 850; white-space: nowrap; }
.empty { padding: 32px; border: 1px dashed var(--border); border-radius: 18px; background: var(--surface); text-align: center; color: var(--muted); grid-column: 1/-1; }
.empty strong { display: block; color: var(--text); font-size: 17px; margin-bottom: 6px; }
.bottom-ad { margin-top: 34px; }
.info-strip { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 36px; }
.info-card { padding: 19px; border-radius: 16px; border: 1px solid var(--border); background: var(--surface); }
.info-icon { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: #7186ff18; color: var(--accent); margin-bottom: 11px; }
.info-icon svg { width: 18px; height: 18px; }
.info-card h3 { margin: 0 0 5px; font-size: 14px; }
.info-card p { margin: 0; color: var(--muted); font-size: 12px; }
.content-page { max-width: 850px; margin: 0 auto; padding: 35px 0 60px; }
.content-page h1 { font-size: clamp(35px, 5vw, 54px); }
.content-page h2 { margin-top: 35px; letter-spacing: -.03em; }
.content-page p, .content-page li { color: var(--muted); }
.content-page a { color: var(--accent); text-decoration: underline; }
.method-note { border-left: 3px solid var(--accent); padding: 14px 18px; background: var(--surface-2); border-radius: 0 12px 12px 0; }
.footer { border-top: 1px solid var(--border); background: var(--surface); }
.footer-inner { max-width: 1240px; margin: 0 auto; padding: 25px 24px; display: flex; justify-content: space-between; align-items: center; gap: 20px; color: var(--muted); font-size: 12px; }
.footer-links { display: flex; flex-wrap: wrap; gap: 17px; }
.refresh-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); display: inline-block; margin-right: 5px; }
@media (max-width: 980px) { .nav-links { display: none; } .hero { grid-template-columns: minmax(0, 1fr) 260px; } .video-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .search-wrap { width: 220px; } }
@media (max-width: 680px) { .topbar-inner { padding: 12px 15px; gap: 10px; flex-wrap: wrap; } .brand { font-size: 19px; } .top-actions { width: 100%; margin-left: 0; } .region-select { max-width: 44%; flex: 0 0 auto; } .search-wrap { flex: 1; width: auto; } main { padding: 19px 15px 45px; } .hero { grid-template-columns: 1fr; padding: 27px 22px; gap: 2px; border-radius: 22px; } .hero-art { min-height: 165px; } .play-orbit { width: 155px; } .play-box { width: 72px; height: 54px; border-radius: 18px; } .chip-one { right: 2%; }.chip-two { left: 2%; } .section-head { align-items: start; flex-direction: column; } .control-row { align-items: start; flex-direction: column; } .video-grid { gap: 12px; grid-template-columns: repeat(2, minmax(0, 1fr)); } .video-body { padding: 11px; } .video-title { font-size: 13px; min-height: 57px; } .creator { font-size: 11px; } .video-stats { align-items: start; flex-direction: column; margin-top: 11px; padding-top: 10px; } .growth { white-space: normal; } .info-strip { grid-template-columns: 1fr; } .footer-inner { align-items: start; flex-direction: column; padding: 22px 15px; } }
"""


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "other"


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def human_number(number: int | float) -> str:
    number = max(0, int(number))
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}K"
    return f"{number:,}"


def relative_time(value: str | None) -> str:
    dt = parse_date(value)
    if not dt:
        return "Upload date unavailable"
    dt = dt.astimezone(timezone.utc)
    days = max(0, (datetime.now(timezone.utc) - dt).days)
    if days == 0:
        return "Uploaded today"
    if days == 1:
        return "1 day ago"
    if days < 7:
        return f"{days} days ago"
    weeks = days // 7
    if weeks < 5:
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    months = days // 30
    return f"{months} month{'s' if months != 1 else ''} ago"


def site_url() -> str:
    value = (os.environ.get("SITE_URL") or CONFIG.get("site_url") or "").strip().rstrip("/")
    if value:
        return value
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if repo and "/" in repo:
        owner, name = repo.split("/", 1)
        if name.lower() == f"{owner}.github.io".lower():
            return f"https://{owner}.github.io"
        return f"https://{owner}.github.io/{name}"
    return "https://example.com"


def base_path(url: str) -> str:
    return urlparse(url).path.rstrip("/")


def local_url(path: str, base: str) -> str:
    raw = path.strip("/")
    if not raw:
        clean = "/"
    else:
        clean = "/" + raw
        # Directory-style routes should consistently end in a slash; static files should not.
        if path.endswith("/") or "." not in raw.split("/")[-1]:
            clean += "/"
    return (base + clean) if base else clean


def full_url(path: str, origin: str, base: str) -> str:
    return origin.rstrip("/") + local_url(path, base)


def load_ads(name: str) -> str:
    path = ROOT / "ads" / f"{name}.html"
    if not path.exists():
        return ""
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        return ""

    # Strip the starter placeholder comment, but preserve any real ad code
    # pasted below it. Older logic rejected the entire file if it began with
    # this comment, which silently removed valid Adsterra snippets.
    if value.startswith("<!-- Paste the Adsterra"):
        comment_end = value.find("-->")
        if comment_end >= 0:
            value = value[comment_end + 3:].strip()

    return value


def ad_slot(name: str, label: str = "Advertisement") -> str:
    content = load_ads(name)
    if content:
        return f'<aside class="ad-slot" aria-label="{esc(label)}">{content}</aside>'
    return f'<aside class="ad-slot" aria-label="{esc(label)}"><span class="ad-label">{esc(label)} placement</span></aside>'


def icon_svg(name: str) -> str:
    paths = {
        "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
        "chart": '<path d="M4 19V5M4 19h17"/><path d="m7 15 4-4 3 2 6-7"/>',
        "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/>',
        "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "play": '<path d="m9 5 11 7-11 7z"/>',
        "spark": '<path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"/>',
    }
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths.get(name, paths["spark"])}</svg>'


def video_card(video: dict, rank: int) -> str:
    vid = video.get("id", "")
    title = video.get("title", "Untitled YouTube video")
    channel = video.get("channel_title", "YouTube creator")
    category = video.get("category_name", "Trending")
    views = int(video.get("view_count", 0) or 0)
    chart_position = int(video.get("position", rank) or rank)
    thumb = video.get("thumbnail") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    search_text = " ".join([title, channel, category, vid]).lower()
    return f'''<article class="video-card" data-search="{esc(search_text)}" data-rank="{chart_position}" data-views="{views}" data-category="{esc(category.lower())}">
      <a href="https://www.youtube.com/watch?v={esc(vid)}" target="_blank" rel="noopener noreferrer" aria-label="Watch {esc(title)} on YouTube">
        <div class="thumb-wrap"><img class="thumb" src="{esc(thumb)}" alt="Thumbnail for {esc(title)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div class="thumb-fallback" style="display:none">▶</div><span class="rank-badge">#{chart_position:02d}</span><span class="watch-badge"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg></span></div>
      </a>
      <div class="video-body"><span class="video-category">{esc(category)}</span><h3 class="video-title"><a href="https://www.youtube.com/watch?v={esc(vid)}" target="_blank" rel="noopener noreferrer">{esc(title)}</a></h3><div class="creator">{esc(channel)} · {esc(relative_time(video.get('published_at')))}</div>
      <div class="video-stats"><span class="view-total">{human_number(views)} views</span><span class="growth" title="Position from YouTube's current mostPopular chart">YouTube chart · #{chart_position:02d}</span></div></div>
    </article>'''


def header(current_region: str, all_regions: list[dict], base: str) -> str:
    options = '<option value="">Select country</option>'
    for reg in all_regions:
        selected = ' selected' if current_region == reg["code"] else ''
        url = local_url("regions/" + reg["code"].lower(), base)
        options += f'<option value="{esc(url)}"{selected}>{esc(reg["name"])}</option>'
    return f'''<header class="topbar"><div class="topbar-inner"><a class="brand" href="{esc(local_url('', base))}" aria-label="TrendPulse home"><span class="brand-mark">{icon_svg('play')}</span><span>Trend<span class="gradient-text">Pulse</span></span></a>
      <nav class="nav-links" aria-label="Main navigation"><a href="{esc(local_url('', base))}#trending">This week</a><a href="{esc(local_url('', base))}#categories">Categories</a><a href="{esc(local_url('methodology', base))}">How it works</a></nav>
      <div class="top-actions"><label class="region-select-wrap"><span class="visually-hidden">Choose region</span><select class="region-select" id="region-select" aria-label="Choose country">{options}</select></label><label class="search-wrap">{icon_svg('search')}<input class="search-input" type="search" id="video-search" placeholder="Search videos..." aria-label="Search video titles and creators"></label></div>
    </div></header>'''


def footer(base: str) -> str:
    year = datetime.now(timezone.utc).year
    return f'''<footer class="footer"><div class="footer-inner"><div>© {year} TrendPulse. YouTube is a trademark of Google LLC. We are an independent discovery site.</div><nav class="footer-links" aria-label="Footer"><a href="{esc(local_url('about', base))}">About</a><a href="{esc(local_url('methodology', base))}">Methodology</a><a href="{esc(local_url('privacy', base))}">Privacy</a><a href="{esc(local_url('terms', base))}">Terms</a><a href="{esc(local_url('contact', base))}">Contact</a></nav></div></footer>'''


def consent_gate(base: str) -> str:
    privacy = esc(local_url("privacy", base))
    site_terms = esc(local_url("terms", base))
    youtube_terms = "https://www.youtube.com/t/terms"
    google_privacy = "https://policies.google.com/privacy"
    return f'''<div class="consent-backdrop" id="consent-gate" role="dialog" aria-modal="true" aria-labelledby="consent-title"><div class="consent-card"><div class="consent-logo">{icon_svg('play')}</div><h2 id="consent-title">Before you explore</h2><p>TrendPulse uses YouTube API Services to show public video information. Please review the site's policies and YouTube's Terms of Service before continuing.</p><p class="consent-links"><a href="{privacy}" target="_blank" rel="noopener">Privacy Policy</a> · <a href="{site_terms}" target="_blank" rel="noopener">Terms of Use</a> · <a href="{youtube_terms}" target="_blank" rel="noopener">YouTube Terms</a> · <a href="{google_privacy}" target="_blank" rel="noopener">Google Privacy</a></p><label class="consent-check"><input type="checkbox" id="consent-agree"><span>I have read and agree to TrendPulse's Privacy Policy and Terms of Use, including YouTube's Terms of Service.</span></label><button type="button" id="consent-continue" disabled>Agree and continue</button><p class="consent-small">TrendPulse is independent and is not affiliated with or endorsed by YouTube or Google.</p></div></div>'''


def page_document(title: str, description: str, canonical: str, body: str, current_region: str,
                  regions: list[dict], base: str) -> str:
    full_title = esc(title)
    desc = esc(description)
    site_name = esc(CONFIG.get("site_name", "TrendPulse"))
    favicon = esc(local_url("favicon.svg", base))
    consent_js = r'''<script>
(function() {
 const gate = document.getElementById('consent-gate');
 const checkbox = document.getElementById('consent-agree');
 const button = document.getElementById('consent-continue');
 if (!gate || !checkbox || !button) return;
 try { if (localStorage.getItem('trendpulse-consent-v1') === 'accepted') gate.classList.add('hidden'); } catch (error) {}
 checkbox.addEventListener('change', function() { button.disabled = !checkbox.checked; });
 button.addEventListener('click', function() {
   if (!checkbox.checked) return;
   try { localStorage.setItem('trendpulse-consent-v1', 'accepted'); } catch (error) {}
   gate.classList.add('hidden');
 });
})();
</script>'''
    app_js = r'''<script>
(function() {
 const search = document.getElementById('video-search');
 const selector = document.getElementById('region-select');
 const cards = Array.from(document.querySelectorAll('.video-card'));
 const sort = document.getElementById('sort-select');
 const count = document.getElementById('results-count');
 const grid = document.querySelector('.video-grid');
 function update() {
   const query = (search ? search.value : '').trim().toLowerCase();
   let visible = 0;
   for (const card of cards) {
     const matches = !query || (card.dataset.search || '').includes(query);
     card.hidden = !matches;
     if (matches) visible++;
   }
   if (count) count.textContent = visible + (visible === 1 ? ' video' : ' videos');
   if (grid && sort) {
     const mode = sort.value;
     const sorted = cards.slice().sort((a,b) => {
       if (mode === 'views') return Number(b.dataset.views || 0) - Number(a.dataset.views || 0);
       if (mode === 'title') return (a.querySelector('.video-title')?.innerText || '').localeCompare(b.querySelector('.video-title')?.innerText || '');
       return Number(a.dataset.rank || 0) - Number(b.dataset.rank || 0);
     });
     sorted.forEach(card => grid.appendChild(card));
   }
 }
 if (selector) selector.addEventListener('change', () => { if (selector.value) window.location.href = selector.value; });
 if (search) search.addEventListener('input', update);
 if (sort) sort.addEventListener('change', update);
 update();
})();
</script>'''
    page_leaf = urlparse(canonical).path.rstrip('/').split('/')[-1]
    needs_consent = page_leaf not in {'privacy', 'terms'}
    gate_markup = consent_gate(base) if needs_consent else ''
    consent_script = consent_js if needs_consent else ''
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{full_title}</title>
  <meta name="description" content="{desc}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <link rel="icon" href="{favicon}" type="image/svg+xml">
  <meta name="theme-color" content="#10182a">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{site_name}">
  <meta property="og:title" content="{full_title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{html.escape(canonical, quote=True)}">
  <meta name="twitter:card" content="summary_large_image">
  <style>{CSS}
  .visually-hidden {{ position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }}
  .consent-backdrop {{ position:fixed; inset:0; z-index:1000; display:flex; align-items:center; justify-content:center; padding:22px; background:rgba(5,10,24,.78); backdrop-filter:blur(9px); }}
  .consent-backdrop.hidden {{ display:none !important; }}
  .consent-card {{ width:min(100%,490px); padding:28px; border-radius:22px; border:1px solid var(--border); background:var(--surface); color:var(--text); box-shadow:0 30px 100px #0006; }}
  .consent-logo {{ width:38px; height:38px; display:grid; place-items:center; border-radius:12px; color:white; background:linear-gradient(135deg,var(--accent),var(--accent-2)); }}
  .consent-logo svg {{ width:19px; height:19px; fill:currentColor; stroke:none; }}
  .consent-card h2 {{ margin:17px 0 8px; font-size:27px; letter-spacing:-.04em; }}
  .consent-card p {{ color:var(--muted); font-size:13px; }}
  .consent-links a {{ color:var(--accent); text-decoration:underline; }}
  .consent-check {{ display:flex; align-items:flex-start; gap:10px; margin:20px 0; font-size:12px; color:var(--text); }}
  .consent-check input {{ margin-top:3px; accent-color:var(--accent); }}
  #consent-continue {{ width:100%; border:0; border-radius:12px; padding:13px 16px; background:linear-gradient(135deg,var(--accent),var(--accent-2)); color:white; font-weight:800; cursor:pointer; }}
  #consent-continue:disabled {{ opacity:.45; cursor:not-allowed; }}
  .consent-card .consent-small {{ margin-bottom:0; font-size:11px; }}
  .growth {{ white-space:nowrap; }}
  @media(max-width:680px) {{ .consent-card {{ padding:22px; }} }}
  </style>
</head>
<body><div class="site-shell">{header(current_region, regions, base)}<main>{body}</main>{footer(base)}</div>
{gate_markup}
{app_js}
{consent_script}
</body></html>'''


def page_content(videos: list[dict], title: str, subtitle: str, regions: list[dict], current_region: str,
                 updated_text: str, base: str, is_home: bool,
                 category_links: list[tuple[str, str]] | None = None) -> str:
    if is_home:
        hero = f'''<section class="hero"><div><div class="eyebrow"><span class="pulse-dot"></span> Your weekly video radar</div><h1>What's <span class="gradient-text">trending</span><br>on YouTube this week?</h1><p class="hero-copy">Explore the latest country-specific list of popular YouTube videos. TrendPulse automatically refreshes the chart through the week, so you can search creators, browse categories, and jump straight to the original video.</p><div class="hero-tags"><span class="pill">{icon_svg('chart')} Official chart order</span><span class="pill">{icon_svg('globe')} Country-by-country</span><span class="pill">{icon_svg('clock')} Auto-refreshed every 6 hours</span></div></div><div class="hero-art" aria-hidden="true"><div class="play-orbit"><div class="play-box">{icon_svg('play')}</div></div><div class="orbit-chip chip-one">{icon_svg('chart')} <span><strong>This week</strong><br>popular videos</span></div><div class="orbit-chip chip-two">{icon_svg('spark')} <span>Fresh snapshots</span></div></div></section>'''
        intro = f'''<div class="section-head" id="trending"><div><h2>Trending videos this week</h2><p>{esc(subtitle)}</p></div><span class="pill"><span class="refresh-dot"></span> Updated {esc(updated_text)}</span></div>'''
    else:
        hero = f'''<section class="hero"><div><div class="eyebrow"><span class="pulse-dot"></span> TrendPulse country chart</div><h1>{esc(title)}</h1><p class="hero-copy">{esc(subtitle)}</p><div class="hero-tags"><span class="pill">{icon_svg('chart')} YouTube chart order</span><span class="pill">{icon_svg('clock')} Updated every 6 hours</span></div></div><div class="hero-art" aria-hidden="true"><div class="play-orbit"><div class="play-box">{icon_svg('play')}</div></div><div class="orbit-chip chip-one">{icon_svg('globe')} <span>Country chart</span></div><div class="orbit-chip chip-two">{icon_svg('spark')} <span>Latest snapshot</span></div></div></section>'''
        intro = f'''<div class="section-head" id="trending"><div><h2>{esc(title)}</h2><p>{esc(subtitle)}</p></div><span class="pill"><span class="refresh-dot"></span> Updated {esc(updated_text)}</span></div>'''

    category_links = category_links or []
    categories = ''
    if category_links:
        links = ''.join(f'<a class="category-pill" href="{esc(href)}">{esc(name)}</a>' for name, href in category_links)
        categories = f'<section id="categories"><div class="section-head"><div><h2>Explore by category</h2><p>Browse separate category pages based on this country chart.</p></div></div><div class="category-pills">{links}</div></section>'
    controls = '''<div class="control-row"><p class="results-count" id="results-count">Loading videos</p><label><span class="visually-hidden">Sort videos</span><select class="sort-select" id="sort-select"><option value="chart">YouTube chart order</option><option value="views">Total views</option><option value="title">Title A–Z</option></select></label></div>'''
    if videos:
        cards = ''.join(video_card(video, int(video.get("position", i + 1) or i + 1)) for i, video in enumerate(videos))
    else:
        cards = '''<div class="empty"><strong>Your first ranking is being prepared.</strong>Add a YouTube Data API key in GitHub Actions and run the workflow. The site will then populate from YouTube's regional most-popular chart and refresh automatically every six hours.</div>'''
    grid = f'<div class="video-grid">{cards}</div>'
    info = '''<section class="info-strip"><article class="info-card"><div class="info-icon">''' + icon_svg("chart") + '''</div><h3>Direct chart listing</h3><p>Video order is taken from YouTube's current regional most-popular chart, not an invented or official seven-day score.</p></article><article class="info-card"><div class="info-icon">''' + icon_svg("clock") + '''</div><h3>Automated refreshes</h3><p>A scheduled background job updates the chart snapshot, rebuilds pages, and publishes automatically.</p></article><article class="info-card"><div class="info-icon">''' + icon_svg("play") + '''</div><h3>Watch on YouTube</h3><p>We link visitors to original videos and creators; TrendPulse does not download or re-host video files.</p></article></section>'''
    methodology_note = '''<p class="method-note">Data note: This page is a timestamped snapshot of YouTube's official <code>mostPopular</code> chart for one country. YouTube does not expose an official seven-day chart through this API endpoint, so TrendPulse does not present this list as an official weekly ranking or calculate a cross-channel seven-day view-growth score. Chart selection and order may change between refreshes.</p>'''
    return hero + ad_slot("top") + intro + controls + grid + ad_slot("in-feed") + categories + methodology_note + info + ad_slot("sidebar")


def simple_content(name: str) -> tuple[str, str]:
    if name == "about":
        title = "About TrendPulse"
        content = '''<div class="content-page"><div class="eyebrow">About the project</div><h1>Find what's popular on YouTube.</h1><p>TrendPulse is an independent video discovery directory that presents country-specific lists from YouTube's current most-popular chart. It helps viewers find videos by topic, creator, and region and links straight to the original watch page.</p><h2>Independent, not affiliated</h2><p>TrendPulse is not owned by, sponsored by, or officially affiliated with YouTube or Google. Video titles, channel names, thumbnails, and view counts come from YouTube API Services and remain associated with their creators. YouTube and Google are trademarks of Google LLC.</p><h2>How the site stays fresh</h2><p>A scheduled job refreshes the current chart snapshot every six hours, rebuilds static pages, and publishes them automatically. It keeps only the latest chart response rather than building a long-term cross-channel analytics history.</p><p><a href="../methodology/">Read the methodology</a> or review the <a href="../terms/">Terms of Use</a>.</p></div>'''
        return title, content
    if name == "methodology":
        title = "How TrendPulse charts work"
        content = '''<div class="content-page"><div class="eyebrow">Transparent data method</div><h1>How TrendPulse works</h1><p>TrendPulse retrieves YouTube's official <code>videos.list</code> most-popular chart for every configured supported country and for categories assignable in that country. The order displayed on a regional or category page is the order returned by YouTube's current chart.</p><h2>Automatic updates</h2><p>GitHub Actions runs approximately every six hours. It fetches the latest country charts from the YouTube Data API, replaces the prior snapshot, pre-renders the pages, and publishes them automatically.</p><h2>What “this week” means here</h2><p>The site is designed to help visitors browse videos that are popular during the current week, with the chart refreshed throughout the week. The YouTube Data API's <code>mostPopular</code> endpoint does not return an official seven-day ranking. This website does not claim that it does and does not create a cross-channel view-growth score from stored history.</p><h2>Limitations</h2><p>The chart varies by country and can change between refreshes. View counts may be rounded or updated by YouTube. Videos can become private, deleted, region-restricted, or otherwise unavailable.</p><p class="method-note">YouTube and Google are trademarks of Google LLC. TrendPulse is an independent discovery site and is not endorsed by YouTube.</p></div>'''
        return title, content
    if name == "privacy":
        title = "Privacy policy"
        content = '''<div class="content-page"><div class="eyebrow">Site information</div><h1>Privacy policy</h1><p><strong>Owner review required before launch:</strong> add your real operator/contact information and confirm the text below fits the tools and legal requirements for the countries you target.</p><h2>YouTube API Services</h2><p>TrendPulse uses YouTube API Services to display publicly available video titles, channel names, thumbnails, categories, and view counts. It does not ask visitors to sign in to YouTube or access their YouTube account. The backend stores the latest country chart snapshot to publish static pages, refreshes it every six hours, and replaces the previous snapshot. The site does not intentionally maintain a historical archive of API results.</p><p>See the <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google Privacy Policy</a> and the <a href="https://www.youtube.com/t/terms" target="_blank" rel="noopener">YouTube Terms of Service</a>.</p><h2>Advertising and third parties</h2><p>If Adsterra advertising code is enabled, Adsterra and its advertising partners may use cookies, device identifiers, or similar technologies to serve and measure ads, subject to their own policies and applicable law. Review current Adsterra policies and add required consent or disclosure tools for your audience before launch.</p><h2>Local browser storage</h2><p>The website stores a small consent flag in the browser's local storage after a visitor accepts the site's privacy policy and YouTube Terms of Service. Searching and sorting video cards happens in the browser.</p><h2>Contact and effective date</h2><p>Replace this section with the owner's actual contact information and effective date. This starter policy is not legal advice.</p><p><strong>Last updated:</strong> October 2026 (starter text; owner review required).</p></div>'''
        return title, content
    if name == "terms":
        title = "Terms of use"
        content = '''<div class="content-page"><div class="eyebrow">Site terms</div><h1>Terms of use</h1><p>TrendPulse is an independent directory that links to original YouTube videos. By using the site, you agree to these site terms and to the <a href="https://www.youtube.com/t/terms" target="_blank" rel="noopener">YouTube Terms of Service</a>.</p><h2>Third-party content</h2><p>Videos, thumbnails, titles, channel names, and statistics are provided through YouTube API Services. We do not own the videos and do not host or download audiovisual content. Availability and statistics can change on YouTube.</p><h2>No guarantee of ranking or availability</h2><p>The country charts shown here are current snapshots of YouTube's most-popular chart; they are not an official YouTube weekly ranking. TrendPulse does not guarantee a video's availability, order, statistics, Google search ranking, or any monetization outcome.</p><h2>Contact</h2><p>Before launch, replace this section with the site owner's contact details and review the terms for your jurisdiction. These starter terms are not legal advice.</p></div>'''
        return title, content
    title = "Contact TrendPulse"
    content = '''<div class="content-page"><div class="eyebrow">Get in touch</div><h1>Contact</h1><p>This starter project intentionally avoids inventing an owner email address. Before launch, add a working contact address or form for correction requests, advertising questions, and privacy inquiries.</p><p>For video ownership, copyright, or playback issues, visit the original video on YouTube and contact the relevant creator or use YouTube's reporting tools.</p><p><strong>Site owner:</strong> Replace this section before launch with your preferred contact method.</p></div>'''
    return title, content


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="_site")
    args = parser.parse_args()
    output = (ROOT / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    try:
        state = json.loads((ROOT / "data" / "current.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {"last_updated": None, "regions": {}, "categories": {}}
    configured_url = site_url()
    parsed_site = urlparse(configured_url)
    origin = f"{parsed_site.scheme}://{parsed_site.netloc}"
    base = parsed_site.path.rstrip("/")
    regions = CONFIG.get("regions", [])
    default_region = str(CONFIG.get("default_region", "US")).upper()
    updated = parse_date(state.get("last_updated"))
    updated_text = updated.strftime("%b %d, %H:%M UTC") if updated else "awaiting first sync"
    all_region_rows = state.get("regions", {})
    all_category_rows = state.get("categories", {})

    def enrich(rows: list[dict]) -> list[dict]:
        output_rows = []
        for row in rows:
            item = dict(row)
            item["category_name"] = item.get("category_name") or CATEGORY_NAMES.get(str(item.get("category_id", "0")), "Trending")
            output_rows.append(item)
        output_rows.sort(key=lambda x: int(x.get("position", 9999) or 9999))
        return output_rows

    region_rows = {str(reg["code"]).upper(): enrich(all_region_rows.get(str(reg["code"]).upper(), [])) for reg in regions}
    region_category_rows = {}
    for reg in regions:
        code = str(reg["code"]).upper()
        raw_categories = all_category_rows.get(code, {})
        region_category_rows[code] = {
            str(category_id): enrich(rows)
            for category_id, rows in raw_categories.items()
            if isinstance(rows, list) and rows
        } if isinstance(raw_categories, dict) else {}
    default_rows = region_rows.get(default_region, [])

    def save_page(relative: str, html_text: str) -> None:
        filepath = output / relative
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(html_text, encoding="utf-8")

    paths = ["", "about/", "methodology/", "privacy/", "terms/", "contact/"]
    default_name = next((r["name"] for r in regions if str(r["code"]).upper() == default_region), default_region)
    default_category_links = []
    default_category_map = {}
    for category_rows in region_category_rows.get(default_region, {}).values():
        if not category_rows:
            continue
        category_name = category_rows[0].get("category_name") or "Trending"
        slug = slugify(category_name)
        default_category_map[slug] = (category_name, local_url(
            f"regions/{default_region.lower()}/categories/{slug}", base
        ))
    default_category_links = sorted(default_category_map.values(), key=lambda item: item[0].lower())

    home_body = page_content(default_rows, f"YouTube trending videos in {default_name}",
        f"Latest snapshot from YouTube's current most-popular chart for {default_name}.",
        regions, default_region, updated_text, base, True, default_category_links)
    home_desc = f"Browse YouTube trending videos this week in {default_name}. Updated automatically every six hours from YouTube's current most-popular chart, with country and category pages."
    save_page("index.html", page_document(f"YouTube Trending Videos This Week in {default_name} | TrendPulse",
        home_desc, full_url("", origin, base), home_body, default_region, regions, base))

    for region in regions:
        code = str(region["code"]).upper()
        name = region["name"]
        rows = region_rows.get(code, [])
        categories = region_category_rows.get(code, {})
        region_category_map = {}
        for cat_videos in categories.values():
            if not cat_videos:
                continue
            cat_name = cat_videos[0].get("category_name") or "Trending"
            slug = slugify(cat_name)
            region_category_map[slug] = (
                cat_name,
                local_url(f"regions/{code.lower()}/categories/{slug}", base),
            )
        region_category_links = sorted(region_category_map.values(), key=lambda item: item[0].lower())

        desc = f"Explore YouTube trending videos in {name} this week using YouTube's current regional most-popular chart, refreshed every six hours."
        body = page_content(rows, f"YouTube trending videos in {name}",
            f"Latest snapshot from YouTube's current most-popular chart for {name}.",
            regions, code, updated_text, base, False, region_category_links)
        route = f"regions/{code.lower()}/"
        save_page(route + "index.html", page_document(f"YouTube Trending Videos in {name} | TrendPulse",
            desc, full_url(route, origin, base), body, code, regions, base))
        paths.append(route)

        for cat_videos in sorted(categories.values(), key=lambda rows: (rows[0].get("category_name", "").lower() if rows else "")):
            if not cat_videos:
                continue
            cat_name = cat_videos[0].get("category_name") or "Trending"
            slug = slugify(cat_name)
            cat_route = f"regions/{code.lower()}/categories/{slug}/"
            category_desc = f"Browse popular {cat_name.lower()} YouTube videos in {name}, from the latest regional chart refreshed every six hours."
            body = page_content(cat_videos, f"Trending {cat_name} videos in {name}",
                f"The latest {cat_name.lower()} entries in YouTube's current {name} popular chart.",
                regions, code, updated_text, base, False)
            save_page(cat_route + "index.html", page_document(f"Trending {cat_name} YouTube Videos in {name} | TrendPulse",
                category_desc, full_url(cat_route, origin, base), body, code, regions, base))
            paths.append(cat_route)

    for simple in ("about", "methodology", "privacy", "terms", "contact"):
        title, body = simple_content(simple)
        route = f"{simple}/"
        save_page(route + "index.html", page_document(f"{title} | TrendPulse", title,
            full_url(route, origin, base), body, "", regions, base))

    # Preserve Google Search Console HTML verification files added to the repository root.
    # GitHub Pages deploys only the generated output folder, so copy them into it.
    for verification_file in ROOT.glob("google*.html"):
        (output / verification_file.name).write_bytes(verification_file.read_bytes())

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for path in paths:
        sitemap += f"  <url><loc>{html.escape(full_url(path, origin, base))}</loc><lastmod>{datetime.now(timezone.utc).date().isoformat()}</lastmod></url>\n"
    sitemap += "</urlset>\n"
    (output / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {origin}{local_url('sitemap.xml', base)}\n", encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    (output / "favicon.svg").write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#7186ff"/><stop offset="1" stop-color="#a15cff"/></linearGradient></defs><rect width="64" height="64" rx="18" fill="url(#g)"/><path d="M25 17v30l24-15z" fill="white"/></svg>''', encoding="utf-8")
    print(f"Built {len(paths)} indexable pages into {output}; default region={default_region}, rows={len(default_rows)}; updated={updated_text}; site={origin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
