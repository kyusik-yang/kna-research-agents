#!/usr/bin/env python3
"""Findings-ledger audit: idempotent appends, deduplication, checks, tallies.

knowledge/findings.jsonl grew to 1,257 rows by R30 although the forum had
produced 41 distinct findings. update_findings_tracker appended with no
uniqueness key, and one R3 archive finding was written 1,200 times. The
published Season 1 figures (1,251 verdicts, 31 pursue, "2.5% pursue") were
read off that ledger. This module makes the ledger idempotent and gives a
verdict count that does not depend on it.

A ledger row is identified by (round, source, finding). row_id is the sha1 of
that key, so the same Critic line appended twice is one row.

Usage:
    python3 ledger_audit.py --check            # exit 1 on any duplicate key
    python3 ledger_audit.py --dedupe           # dry run: report what would change
    python3 ledger_audit.py --dedupe --apply   # archive the original, rewrite the ledger
    python3 ledger_audit.py --tally [--out FILE]   # one verdict per Critic post, by season
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
LEDGER = KNOWLEDGE_DIR / "findings.jsonl"
VERDICTS_FILE = KNOWLEDGE_DIR / "verdicts.jsonl"

# Season boundaries, from SEASON2.md: Rounds 1-24 are Season 1, Round 25 on is Season 2.
SEASON2_START_ROUND = 25
LEGACY_AGENTS_PER_ROUND = 3

VERDICT_RE = re.compile(r"verdict:\s*(pursue|revise|archive)")


# ---------------------------------------------------------------------------
# Row identity
# ---------------------------------------------------------------------------

def _round_value(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def row_key(row: dict) -> tuple:
    """Uniqueness key of a ledger row: (round, source, finding)."""
    return (
        _round_value(row.get("round")),
        str(row.get("source") or ""),
        str(row.get("finding") or "").strip(),
    )


def row_id(row: dict) -> str:
    """sha1 of the row key, stable across runs and machines."""
    key = json.dumps(list(row_key(row)), ensure_ascii=False)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def load(path: Path | None = None) -> list[dict]:
    """Read ledger rows in file order. Malformed lines are skipped."""
    path = Path(path) if path else LEDGER
    rows = []
    if not path.exists():
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


# ---------------------------------------------------------------------------
# Idempotent append
# ---------------------------------------------------------------------------

def append_unique(row: dict, *, path: Path | None = None) -> bool:
    """Append row unless a row with the same (round, source, finding) exists.

    Returns True if the row was written, False if it was already present.
    The written row carries row_id. The read and the append happen under an
    exclusive lock so two writers cannot both append the same key.
    """
    path = Path(path) if path else LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    new = dict(row)
    new["row_id"] = row_id(new)
    key = row_key(new)
    with open(path, "a+", encoding="utf-8") as f:
        if fcntl is not None:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.seek(0)
            text = f.read()
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    existing = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if existing.get("row_id") == new["row_id"] or row_key(existing) == key:
                    return False
            if text and not text.endswith("\n"):
                f.write("\n")
            f.write(json.dumps(new, ensure_ascii=False) + "\n")
            f.flush()
            return True
        finally:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# Check and dedupe
# ---------------------------------------------------------------------------

def duplicate_keys(rows: list[dict]) -> dict:
    """Map each duplicated key to its row count."""
    counts = Counter(row_key(r) for r in rows)
    return {k: n for k, n in counts.items() if n > 1}


def check(path: Path | None = None) -> dict:
    rows = load(path)
    dups = duplicate_keys(rows)
    return {
        "ok": not dups,
        "rows": len(rows),
        "unique": len({row_key(r) for r in rows}),
        "duplicate_keys": len(dups),
        "duplicate_rows": sum(n - 1 for n in dups.values()),
    }


def _archive_path(archive_dir: Path) -> Path:
    """knowledge/archive/findings_pre_dedupe_<today>.jsonl, never overwritten."""
    base = archive_dir / f"findings_pre_dedupe_{date.today().isoformat()}.jsonl"
    if not base.exists():
        return base
    k = 2
    while True:
        cand = archive_dir / f"{base.stem}.rev{k}.jsonl"
        if not cand.exists():
            return cand
        k += 1


def dedupe(apply: bool, *, path: Path | None = None, archive_dir: Path | None = None) -> dict:
    """Keep the first row per (round, source, finding), in file order, with row_id.

    With apply=False nothing is written. With apply=True the original file is
    copied byte for byte into archive/ next to the ledger (never overwriting an earlier
    archive) before the ledger is replaced atomically. If the ledger has no
    duplicates and every row already carries its row_id, nothing is written.
    """
    path = Path(path) if path else LEDGER
    # The archive sits next to the ledger (knowledge/archive/ for the live one).
    archive_dir = Path(archive_dir) if archive_dir else path.parent / "archive"
    rows = load(path)
    seen = set()
    kept = []
    for r in rows:
        k = row_key(r)
        if k in seen:
            continue
        seen.add(k)
        out = dict(r)
        out["row_id"] = row_id(r)
        kept.append(out)

    changed = len(kept) != len(rows) or any(
        r.get("row_id") != row_id(r) for r in rows
    )
    report = {
        "rows_before": len(rows),
        "rows_after": len(kept),
        "duplicates_removed": len(rows) - len(kept),
        "verdicts_before": dict(Counter(r.get("verdict") for r in rows)),
        "verdicts_after": dict(Counter(r.get("verdict") for r in kept)),
        "changed": changed,
        "applied": False,
        "archive": None,
    }
    if not apply or not changed:
        return report

    archive_dir.mkdir(parents=True, exist_ok=True)
    archive = _archive_path(archive_dir)
    shutil.copy2(path, archive)
    if archive.read_bytes() != path.read_bytes():
        raise RuntimeError(f"archive copy does not match the ledger: {archive}")
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    report["applied"] = True
    report["archive"] = str(archive)
    return report


# ---------------------------------------------------------------------------
# Tally: one verdict per Critic post
# ---------------------------------------------------------------------------

def _frontmatter_round(text: str):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    m = re.search(r"^round:\s*(\d+)\s*$", text[3:end], re.MULTILINE)
    return int(m.group(1)) if m else None


def _post_round(path: Path, text: str) -> int | None:
    rnd = _frontmatter_round(text)
    if rnd is not None:
        return rnd
    m = re.match(r"^(\d+)_", path.name)
    if not m:
        return None
    return (int(m.group(1)) - 1) // LEGACY_AGENTS_PER_ROUND + 1


def _verdicts_of_record(path: Path) -> dict:
    """round -> verdict from knowledge/verdicts.jsonl (last row per round wins)."""
    out = {}
    for r in load(path):
        rnd = _round_value(r.get("round"))
        if isinstance(rnd, int) and r.get("verdict") in ("pursue", "revise", "archive"):
            out[rnd] = r["verdict"]
    return out


def season_of(round_num: int) -> int:
    return 2 if round_num >= SEASON2_START_ROUND else 1


def tally(forum_dir: Path | None = None, verdicts_file: Path | None = None) -> dict:
    """Count one verdict per Critic post, by season.

    The verdict of a post is the row in knowledge/verdicts.jsonl for its round
    when one exists, otherwise the first 'verdict:' line in the post, which is
    what run_forum._extract_verdict used as the round's verdict. Posts that
    score more than one project (several verdict lines that disagree) are
    listed in 'multi_verdict_posts' so the reader can see the choice.
    """
    forum_dir = Path(forum_dir) if forum_dir else FORUM_DIR
    verdicts_file = Path(verdicts_file) if verdicts_file else VERDICTS_FILE
    of_record = _verdicts_of_record(verdicts_file)
    posts = []
    for p in sorted(forum_dir.glob("*_critic.md")):
        text = p.read_text(encoding="utf-8")
        rnd = _post_round(p, text)
        all_hits = VERDICT_RE.findall(text)
        if rnd in of_record:
            verdict, basis = of_record[rnd], "verdicts.jsonl"
        elif all_hits:
            verdict, basis = all_hits[0], "first_verdict_line"
        else:
            verdict, basis = None, "none"
        posts.append({
            "post": p.name,
            "round": rnd,
            "season": season_of(rnd) if isinstance(rnd, int) else None,
            "verdict": verdict,
            "basis": basis,
            "distinct_verdicts_in_post": sorted(set(all_hits)),
        })

    seasons = {}
    for s in (1, 2):
        sub = [x for x in posts if x["season"] == s]
        c = Counter(x["verdict"] for x in sub)
        seasons[f"season{s}"] = {
            "critic_posts": len(sub),
            "pursue": c.get("pursue", 0),
            "revise": c.get("revise", 0),
            "archive": c.get("archive", 0),
            "no_verdict": c.get(None, 0),
        }
    return {
        "unit": "one verdict per Critic post",
        "seasons": seasons,
        "multi_verdict_posts": [
            x for x in posts if len(x["distinct_verdicts_in_post"]) > 1
        ],
        "posts": posts,
    }


def ledger_by_season(path: Path | None = None) -> dict:
    """Verdict counts of the (deduplicated or not) ledger rows, by season."""
    rows = load(path)
    out = {}
    for s in (1, 2):
        sub = [r for r in rows if isinstance(_round_value(r.get("round")), int)
               and season_of(_round_value(r.get("round"))) == s]
        c = Counter(r.get("verdict") for r in sub)
        out[f"season{s}"] = {
            "rows": len(sub),
            "unique": len({row_key(r) for r in sub}),
            "pursue": c.get("pursue", 0),
            "revise": c.get("revise", 0),
            "archive": c.get("archive", 0),
            "critic_sourced_rows": sum(1 for r in sub if "critic" in str(r.get("source", ""))),
        }
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="Exit 1 if any (round, source, finding) key repeats")
    ap.add_argument("--dedupe", action="store_true", help="Deduplicate the ledger (dry run unless --apply)")
    ap.add_argument("--apply", action="store_true", help="With --dedupe: archive the original and rewrite the ledger")
    ap.add_argument("--tally", action="store_true", help="One verdict per Critic post, by season")
    ap.add_argument("--out", help="With --tally: also write the JSON to this file")
    ap.add_argument("--ledger", help="Ledger path (default knowledge/findings.jsonl)")
    args = ap.parse_args(argv)
    ledger = Path(args.ledger) if args.ledger else None

    if not (args.check or args.dedupe or args.tally):
        ap.print_help()
        return 2

    status = 0
    if args.check:
        r = check(ledger)
        print(json.dumps(r, ensure_ascii=False))
        if not r["ok"]:
            status = 1
    if args.dedupe:
        r = dedupe(apply=args.apply, path=ledger)
        print(json.dumps(r, ensure_ascii=False))
    if args.tally:
        r = tally()
        r["ledger"] = ledger_by_season(ledger)
        text = json.dumps(r, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        summary = {k: v for k, v in r.items() if k not in ("posts",)}
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return status


if __name__ == "__main__":
    sys.exit(main())
