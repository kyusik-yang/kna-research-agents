#!/usr/bin/env python3
"""
KCI Monthly Literature Scan (reflection commitment C7).
=======================================================

Pulls recent KCI-indexed articles in a configured set of Korean political
science and communication journals into knowledge/kci_new.jsonl as a
standing Scout task.

KCI has no public JSON API; we use Crossref as the DOI-indexed proxy for
Korean journals that register DOIs, and fall back to the journal name
being present in Crossref's container-title field. This is partial but
the output is inspectable.

Scheduled externally (cron or launchd); not invoked by run_forum.py.

Usage:
    python3 scripts/kci_monthly_scan.py
    python3 scripts/kci_monthly_scan.py --since 2026-01-01
    python3 scripts/kci_monthly_scan.py --dry-run
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT_FILE = BASE / "knowledge" / "kci_new.jsonl"
SEEN_FILE = BASE / "knowledge" / "kci_scan_cursor.json"

TARGET_JOURNALS = [
    "한국정치학회보",          # Korean Political Science Review
    "의정연구",                # Journal of Parliamentary Research
    "한국정당학회보",          # Korean Party Studies Review
    "한국행정학보",            # Korean Public Administration Review
    "입법학연구",              # Korean Journal of Legislative Studies
    "한국과 국제정치",          # Korea and World Politics
    "언론정보연구",            # Journal of Communication Research
    "미디어 경제와 문화",      # Journal of Media Economics and Culture
    "한국언론학보",            # Korean Journal of Journalism
]


def fetch_crossref(journal_name: str, since_iso: str) -> list[dict]:
    """Crossref query for the journal; filter by from-pub-date."""
    query = urllib.parse.quote(journal_name)
    url = (
        f"https://api.crossref.org/works?"
        f"query.container-title={query}&"
        f"filter=from-pub-date:{since_iso}&"
        f"rows=20&sort=published&order=desc&"
        f"mailto=kyusik.yang@nyu.edu"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "kna-research-agents kci-monthly-scan (mailto:kyusik.yang@nyu.edu)",
    })
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"  [KCI · {journal_name}] fetch failed: {e}", file=sys.stderr)
        return []
    results = []
    for item in data.get("message", {}).get("items", []):
        container = (item.get("container-title") or [""])[0]
        if journal_name not in container:
            continue  # Crossref fuzzy matches; require exact substring
        results.append({
            "doi": item.get("DOI", ""),
            "title": (item.get("title") or [""])[0],
            "authors": [
                f"{a.get('family','')}, {a.get('given','')}".strip(", ")
                for a in item.get("author", []) or []
            ][:5],
            "container": container,
            "published": "-".join(
                str(p) for p in (item.get("issued", {}).get("date-parts") or [[None]])[0] if p
            ),
            "url": item.get("URL", ""),
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="KCI monthly scan (C7)")
    parser.add_argument("--since", type=str, help="ISO date (YYYY-MM-DD); default = 30 days ago")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but don't write to knowledge/")
    args = parser.parse_args()

    since = args.since or (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    print(f"Scanning KCI-indexed journals since {since}...")

    # De-dupe against seen DOIs
    seen = set()
    if SEEN_FILE.exists():
        try:
            seen = set(json.loads(SEEN_FILE.read_text()).get("seen_dois", []))
        except Exception:
            seen = set()

    new_items = []
    for jname in TARGET_JOURNALS:
        hits = fetch_crossref(jname, since)
        print(f"  {jname}: {len(hits)} hit(s)")
        for h in hits:
            if h["doi"] and h["doi"] not in seen:
                new_items.append(h)
                seen.add(h["doi"])
        time.sleep(0.6)  # Crossref polite pool

    if not new_items:
        print("No new items since last scan.")
        return

    if args.dry_run:
        print(f"[dry-run] {len(new_items)} new items:")
        for it in new_items[:10]:
            print(f"  - {it['published']} {it['container']}: {it['title'][:80]}")
        return

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "a", encoding="utf-8") as f:
        for it in new_items:
            f.write(json.dumps({**it, "fetched_at": datetime.utcnow().isoformat()},
                               ensure_ascii=False) + "\n")
    SEEN_FILE.write_text(json.dumps({"seen_dois": sorted(seen),
                                     "last_scan": datetime.utcnow().isoformat()},
                                    ensure_ascii=False, indent=2))
    print(f"Wrote {len(new_items)} new items to {OUT_FILE}")


if __name__ == "__main__":
    main()
