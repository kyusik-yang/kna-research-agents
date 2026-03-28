#!/usr/bin/env python3
"""
Weekly Literature Scan
======================
Runs Scout to check for new Korean politics publications on OpenAlex
and Crossref, then saves results to a persistent knowledge base.

Designed to run weekly via cron/launchd. Each scan appends to
knowledge/literature_log.jsonl - a cumulative record of everything
Scout has found. Forum agents read this log to stay current.

Usage:
    python3 weekly_scan.py                          # Run scan now
    python3 weekly_scan.py --days 14                # Look back 14 days
    python3 weekly_scan.py --query "정당 분극화"     # Custom query

Cron example (every Sunday at 9am):
    0 9 * * 0 cd /path/to/kna-research-agents && python3 weekly_scan.py
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
LOG_FILE = KNOWLEDGE_DIR / "literature_log.jsonl"
DIGEST_DIR = KNOWLEDGE_DIR / "digests"

MAILTO = "kyusik.yang@nyu.edu"


TOPIC_FILTER = (
    "primary_topic.subfield.id:"
    "https://openalex.org/subfields/3320"   # Political Science and International Relations
    "|https://openalex.org/subfields/3312"  # Sociology and Political Science
    "|https://openalex.org/subfields/2002"  # Economics and Econometrics
    "|https://openalex.org/subfields/3308"  # Law
)


def search_openalex(query, from_date, per_page=50):
    """Search OpenAlex for recent works, filtered to political science and economics."""
    encoded = quote(query)
    url = (
        f"https://api.openalex.org/works"
        f"?search={encoded}"
        f"&filter=publication_year:{from_date.year}-{datetime.now().year},{TOPIC_FILTER}"
        f"&per_page={per_page}"
        f"&sort=publication_year:desc"
        f"&select=id,title,publication_year,authorships,cited_by_count,doi,primary_topic"
        f"&mailto={MAILTO}"
    )
    result = subprocess.run(
        ["curl", "-s", url], capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("results", [])
    except json.JSONDecodeError:
        return []


def search_crossref(query, from_date, rows=50):
    """Search Crossref for recent Korean journal articles."""
    encoded = quote(query)
    date_str = from_date.strftime("%Y-%m-%d")
    url = (
        f"https://api.crossref.org/works"
        f"?query={encoded}"
        f"&rows={rows}"
        f"&sort=published"
        f"&order=desc"
        f"&filter=from-pub-date:{date_str}"
        f"&mailto={MAILTO}"
    )
    result = subprocess.run(
        ["curl", "-s", url], capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("message", {}).get("items", [])
    except json.JSONDecodeError:
        return []


def normalize_openalex(work):
    """Normalize an OpenAlex work to a common format."""
    authors = [a["author"]["display_name"] for a in work.get("authorships", [])[:5]]
    topic = work.get("primary_topic", {})
    return {
        "source": "openalex",
        "id": work.get("id", ""),
        "title": work.get("title", ""),
        "year": work.get("publication_year"),
        "authors": authors,
        "doi": work.get("doi"),
        "cited_by": work.get("cited_by_count", 0),
        "topic": topic.get("display_name", "") if topic else "",
        "scanned_at": datetime.now().isoformat(),
    }


def normalize_crossref(item):
    """Normalize a Crossref item to a common format."""
    authors = []
    for a in item.get("author", [])[:5]:
        name = f"{a.get('given', '')} {a.get('family', '')}".strip()
        if name:
            authors.append(name)
    year = None
    pub = item.get("published", {}).get("date-parts", [[]])
    if pub and pub[0]:
        year = pub[0][0]
    return {
        "source": "crossref",
        "id": item.get("DOI", ""),
        "title": item.get("title", [""])[0] if item.get("title") else "",
        "year": year,
        "authors": authors,
        "doi": item.get("DOI"),
        "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
        "scanned_at": datetime.now().isoformat(),
    }


# Search queries strictly about Korean politics
# Every query must include "Korea" or Korean-language terms
# to avoid pulling in unrelated political science
DEFAULT_QUERIES = {
    "openalex_en": [
        "Korean National Assembly legislation",
        "South Korea parliament party politics",
        "Korean legislative polarization committee",
        "Korean election voting behavior representation",
        "South Korea political party ideology",
    ],
    "openalex_ko": [
        "국회 입법",
        "국회 위원회 법안",
        "한국 정당 분극화",
        "한국 선거 투표",
        "대한민국 정치",
    ],
    "crossref_ko": [
        "국회 입법 법안",
        "정당 분극화 한국",
        "국회 위원회",
        "의원 표결 국회",
        "한국 선거 정치",
    ],
}


def run_scan(days=7, custom_query=None):
    """Run the weekly literature scan."""
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    DIGEST_DIR.mkdir(exist_ok=True)

    from_date = datetime.now() - timedelta(days=days)
    all_results = []
    seen_titles = set()

    # Load existing titles to avoid duplicates
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    seen_titles.add(entry.get("title", "").lower().strip())
                except json.JSONDecodeError:
                    pass

    queries = DEFAULT_QUERIES
    if custom_query:
        queries = {
            "openalex_en": [custom_query],
            "openalex_ko": [custom_query],
            "crossref_ko": [custom_query],
        }

    print(f"  Scanning literature from {from_date.strftime('%Y-%m-%d')} to now...")

    # OpenAlex English
    for q in queries["openalex_en"]:
        print(f"  OpenAlex (EN): {q}")
        works = search_openalex(q, from_date)
        for w in works:
            n = normalize_openalex(w)
            if n["title"].lower().strip() not in seen_titles and n["title"]:
                all_results.append(n)
                seen_titles.add(n["title"].lower().strip())

    # OpenAlex Korean
    for q in queries["openalex_ko"]:
        print(f"  OpenAlex (KO): {q}")
        works = search_openalex(q, from_date)
        for w in works:
            n = normalize_openalex(w)
            if n["title"].lower().strip() not in seen_titles and n["title"]:
                all_results.append(n)
                seen_titles.add(n["title"].lower().strip())

    # Crossref Korean
    for q in queries["crossref_ko"]:
        print(f"  Crossref (KO): {q}")
        items = search_crossref(q, from_date)
        for item in items:
            n = normalize_crossref(item)
            if n["title"].lower().strip() not in seen_titles and n["title"]:
                all_results.append(n)
                seen_titles.add(n["title"].lower().strip())

    # Append new results to log
    new_count = 0
    with open(LOG_FILE, "a") as f:
        for r in all_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            new_count += 1

    # Write weekly digest
    today = datetime.now().strftime("%Y-%m-%d")
    digest_file = DIGEST_DIR / f"{today}.md"
    with open(digest_file, "w") as f:
        f.write(f"# Literature Digest - {today}\n\n")
        f.write(f"Scanned: {from_date.strftime('%Y-%m-%d')} to {today}\n")
        f.write(f"New entries: {new_count}\n\n")

        if all_results:
            f.write("## New Publications\n\n")
            for r in sorted(all_results, key=lambda x: x.get("year") or 0, reverse=True):
                authors = ", ".join(r.get("authors", [])[:3])
                doi_str = f" | doi:{r['doi']}" if r.get("doi") else ""
                journal_str = f" | {r['journal']}" if r.get("journal") else ""
                f.write(f"- **{r['title']}** ({r.get('year', '?')})\n")
                f.write(f"  {authors}{journal_str}{doi_str}\n\n")
        else:
            f.write("No new publications found.\n")

    # Summary
    total = 0
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            total = sum(1 for _ in f)

    print(f"\n  Results:")
    print(f"    New entries:   {new_count}")
    print(f"    Total in log:  {total}")
    print(f"    Digest:        {digest_file}")
    print(f"    Full log:      {LOG_FILE}")

    return new_count


def main():
    parser = argparse.ArgumentParser(description="Weekly literature scan")
    parser.add_argument("--days", type=int, default=7, help="Look-back period in days (default: 7)")
    parser.add_argument("--query", type=str, default=None, help="Custom search query")
    args = parser.parse_args()

    print(f"\n  Weekly Literature Scan")
    print(f"  Period: last {args.days} days")
    print()

    run_scan(days=args.days, custom_query=args.query)


if __name__ == "__main__":
    main()
