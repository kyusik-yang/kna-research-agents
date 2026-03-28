#!/usr/bin/env python3
"""
collect_abstracts.py - Collect abstracts from Korean political science papers.

Searches OpenAlex and Crossref for Korean political science papers,
reconstructs abstracts from inverted indices (OpenAlex), and saves
results to knowledge/abstracts.jsonl.

Usage:
    python3 collect_abstracts.py                      # Collect from all default queries
    python3 collect_abstracts.py --query "정당 분극화"  # Custom query
    python3 collect_abstracts.py --stats              # Show collection statistics
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

MAILTO = "kyusik.yang@nyu.edu"
OUTPUT_PATH = Path(__file__).parent / "knowledge" / "abstracts.jsonl"

# OpenAlex subfield filter for political science only
OPENALEX_SUBFIELD_FILTER = (
    "primary_topic.subfield.id:"
    "https://openalex.org/subfields/3320"  # Political Science
    "|https://openalex.org/subfields/3312"  # Sociology and Political Science
)

from utils.relevance import is_relevant_paper

# Default search queries
KOREAN_KEYWORDS = [
    "국회",
    "정당",
    "선거",
    "입법",
    "위원회",
    "한국정치",
]

ENGLISH_KEYWORDS = [
    "Korean National Assembly",
    "Korean party politics",
    "Korean elections",
    "Korean legislature",
]

DEFAULT_QUERIES = KOREAN_KEYWORDS + ENGLISH_KEYWORDS


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def load_existing_dois() -> set:
    """Load DOIs already collected to avoid duplicates."""
    dois = set()
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    doi = record.get("doi")
                    if doi:
                        dois.add(doi.lower())
                except json.JSONDecodeError:
                    continue
    return dois


def load_existing_titles() -> set:
    """Load titles already collected (fallback dedup when DOI is missing)."""
    titles = set()
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    title = record.get("title")
                    if title:
                        titles.add(title.strip().lower())
                except json.JSONDecodeError:
                    continue
    return titles


def append_record(record: dict) -> None:
    """Append a single record to the JSONL file."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def api_get(url: str, max_retries: int = 3):
    """GET a JSON endpoint with retries and backoff."""
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": f"CollectAbstracts/1.0 (mailto:{MAILTO})"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** (attempt + 1)
                print(f"  Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                continue
            elif e.code in (500, 502, 503, 504):
                wait = 2 ** (attempt + 1)
                print(f"  Server error ({e.code}). Retrying in {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f"  HTTP error {e.code} for {url}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  Request error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Failed after {max_retries} retries: {e}")
                return None
    return None


def reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract text from OpenAlex inverted index format.

    The inverted_index maps each word to a list of integer positions.
    We invert this to get the ordered word list.
    """
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join(w for _, w in word_positions)


# ---------------------------------------------------------------------------
# OpenAlex collection
# ---------------------------------------------------------------------------


def collect_openalex(query: str, existing_dois: set, existing_titles: set) -> list[dict]:
    """Search OpenAlex for papers matching the query and return new records."""
    records = []
    per_page = 100
    max_pages = 5  # up to 500 results per query

    encoded_query = urllib.parse.quote(query)
    base_url = (
        f"https://api.openalex.org/works?"
        f"search={encoded_query}"
        f"&filter={urllib.parse.quote(OPENALEX_SUBFIELD_FILTER)}"
        f"&per_page={per_page}"
        f"&mailto={MAILTO}"
    )

    for page in range(1, max_pages + 1):
        url = f"{base_url}&page={page}"
        data = api_get(url)
        if not data:
            break

        results = data.get("results", [])
        if not results:
            break

        for work in results:
            doi = (work.get("doi") or "").replace("https://doi.org/", "")
            title = (work.get("title") or "").strip()

            # Skip if already collected
            if doi and doi.lower() in existing_dois:
                continue
            if title and title.lower() in existing_titles:
                continue

            # Extract journal early for relevance check
            primary_location = work.get("primary_location") or {}
            source_info = primary_location.get("source") or {}
            journal = source_info.get("display_name", "")

            # Relevance filter: skip non-Korean-politics papers
            if not is_relevant_paper(title, journal):
                continue

            # Reconstruct abstract
            abstract_inverted = work.get("abstract_inverted_index")
            abstract = reconstruct_abstract(abstract_inverted) if abstract_inverted else ""
            if not abstract:
                continue  # skip papers without abstracts

            # Extract authors
            authors = []
            for authorship in work.get("authorships", []):
                author_obj = authorship.get("author", {})
                name = author_obj.get("display_name", "")
                if name:
                    authors.append(name)

            # Extract year
            year = work.get("publication_year")

            record = {
                "title": title,
                "authors": authors,
                "year": year,
                "doi": doi if doi else None,
                "journal": journal,
                "abstract": abstract,
                "source": "openalex",
            }

            records.append(record)

            # Track for dedup within this run
            if doi:
                existing_dois.add(doi.lower())
            if title:
                existing_titles.add(title.lower())

        # Be polite
        time.sleep(0.5)

        total_count = data.get("meta", {}).get("count", 0)
        fetched_so_far = page * per_page
        if fetched_so_far >= total_count:
            break

    return records


# ---------------------------------------------------------------------------
# Crossref collection
# ---------------------------------------------------------------------------


def collect_crossref(query: str, existing_dois: set, existing_titles: set) -> list[dict]:
    """Search Crossref for papers matching the query and return new records."""
    records = []
    rows = 100
    max_offsets = 5  # up to 500 results per query

    for offset_idx in range(max_offsets):
        offset = offset_idx * rows
        encoded_query = urllib.parse.quote(query)
        url = (
            f"https://api.crossref.org/works?"
            f"query={encoded_query}"
            f"&filter=has-abstract:true"
            f"&rows={rows}"
            f"&offset={offset}"
            f"&mailto={MAILTO}"
        )

        data = api_get(url)
        if not data:
            break

        message = data.get("message", {})
        items = message.get("items", [])
        if not items:
            break

        for item in items:
            doi = (item.get("DOI") or "").strip()
            titles = item.get("title", [])
            title = titles[0].strip() if titles else ""

            # Skip if already collected
            if doi and doi.lower() in existing_dois:
                continue
            if title and title.lower() in existing_titles:
                continue

            abstract = (item.get("abstract") or "").strip()
            if not abstract:
                continue

            # Extract journal early for relevance check
            containers = item.get("container-title", [])
            journal = containers[0] if containers else ""

            # Relevance filter: skip non-political-science papers
            if not is_relevant_paper(title, journal):
                continue

            # Strip JATS XML tags from Crossref abstracts
            import re
            abstract = re.sub(r"<[^>]+>", "", abstract).strip()

            # Extract authors
            authors = []
            for author in item.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

            # Extract year
            date_parts = (
                item.get("published-print", {}).get("date-parts")
                or item.get("published-online", {}).get("date-parts")
                or item.get("issued", {}).get("date-parts")
            )
            year = None
            if date_parts and date_parts[0]:
                year = date_parts[0][0]

            record = {
                "title": title,
                "authors": authors,
                "year": year,
                "doi": doi if doi else None,
                "journal": journal,
                "abstract": abstract,
                "source": "crossref",
            }

            records.append(record)

            if doi:
                existing_dois.add(doi.lower())
            if title:
                existing_titles.add(title.lower())

        # Be polite
        time.sleep(0.5)

        total_results = message.get("total-results", 0)
        if offset + rows >= total_results:
            break

    return records


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def print_stats() -> None:
    """Print collection statistics."""
    if not OUTPUT_PATH.exists():
        print("No data collected yet.")
        print(f"  Expected file: {OUTPUT_PATH}")
        return

    records = []
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not records:
        print("No records found in the output file.")
        return

    print(f"Collection statistics for {OUTPUT_PATH}")
    print(f"{'=' * 60}")
    print(f"Total abstracts collected: {len(records)}")

    # By source
    source_counts = Counter(r.get("source", "unknown") for r in records)
    print(f"\nBy source:")
    for src, count in source_counts.most_common():
        print(f"  {src}: {count}")

    # By year range
    years = [r.get("year") for r in records if r.get("year")]
    if years:
        print(f"\nYear range: {min(years)} - {max(years)}")
        year_counts = Counter(years)
        print(f"Top 10 years:")
        for yr, count in year_counts.most_common(10):
            print(f"  {yr}: {count}")
    else:
        print("\nNo year data available.")

    # By journal (top 15)
    journals = [r.get("journal", "") for r in records if r.get("journal")]
    if journals:
        journal_counts = Counter(journals)
        print(f"\nTop 15 journals:")
        for jrnl, count in journal_counts.most_common(15):
            print(f"  {jrnl}: {count}")

    # DOI coverage
    with_doi = sum(1 for r in records if r.get("doi"))
    print(f"\nDOI coverage: {with_doi}/{len(records)} ({100*with_doi/len(records):.1f}%)")

    # Abstract length stats
    lengths = [len(r.get("abstract", "")) for r in records]
    if lengths:
        avg_len = sum(lengths) / len(lengths)
        print(f"Abstract length (chars): avg={avg_len:.0f}, min={min(lengths)}, max={max(lengths)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_collection(queries: list[str]) -> None:
    """Run the collection pipeline for a list of queries."""
    existing_dois = load_existing_dois()
    existing_titles = load_existing_titles()
    initial_count = len(existing_dois) + len(existing_titles - existing_dois)

    print(f"Output: {OUTPUT_PATH}")
    print(f"Already collected: {len(existing_dois)} unique DOIs, {len(existing_titles)} unique titles")
    print(f"{'=' * 60}")

    total_new = 0

    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Query: \"{query}\"")

        # OpenAlex
        print(f"  Searching OpenAlex...")
        oa_records = collect_openalex(query, existing_dois, existing_titles)
        for rec in oa_records:
            append_record(rec)
        print(f"  OpenAlex: {len(oa_records)} new abstracts")

        # Crossref
        print(f"  Searching Crossref...")
        cr_records = collect_crossref(query, existing_dois, existing_titles)
        for rec in cr_records:
            append_record(rec)
        print(f"  Crossref: {len(cr_records)} new abstracts")

        total_new += len(oa_records) + len(cr_records)

    print(f"\n{'=' * 60}")
    print(f"New abstracts collected this run: {total_new}")
    print(f"Total DOIs tracked: {len(existing_dois)}")
    print()
    print_stats()


def main():
    parser = argparse.ArgumentParser(
        description="Collect abstracts from Korean political science papers."
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Custom search query (overrides defaults)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show collection statistics and exit",
    )
    args = parser.parse_args()

    if args.stats:
        print_stats()
        return

    if args.query:
        queries = [args.query]
    else:
        queries = DEFAULT_QUERIES

    run_collection(queries)


if __name__ == "__main__":
    main()
