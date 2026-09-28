#!/usr/bin/env python3
"""
Replication packages per arc (v2.1, M18)
========================================
Papers D and E point to a replication archive, but workspace/ and logs/ are
gitignored, so the scripts behind them were never published, and the round
scripts hardcode absolute home paths. This module builds replication/arc_N/
from the arc's round scripts, its prediction cards and the paper's figure
scripts, rewrites paths so the package runs anywhere, and verifies it.

What goes in (D-17 default, "scripts and cards only"):
  rNN/<script>              *.py, *.R, *.sql, *.sh from workspace/rNN/ (5 MB cap)
  figures/<stem>/fig_N.R    the paper's figure scripts
  cards/R<NN>.json          prediction cards (Stage 2), when they exist
  README.md, MANIFEST.json
No data, no results JSON and no derived samples. The README states that
derived data are available on request. Changing that is D-17.

Path rewrites (recorded in MANIFEST.json by kind and line, never with the
original text, which would itself be a private path):
  KNA processed-data prefix  -> os.environ["KBL_DATA"] / Sys.getenv("KBL_DATA")
  forum workspace path       -> package-relative (run from the package root)
  forum repository prefix    -> repository-relative
Any other absolute home path or leak-lint hit fails the build, and the file
is not written.

Command order (MANIFEST.json "order"): a script that writes a file runs
before every script that reads it, as far as the string literals in the
rewritten scripts show (write calls, pathlib writes, continuation lines of a
write call, and variables later used as write targets). A builder can declare
dependencies the scan cannot see ("after" on an extra, or order_hints). Ties,
and scripts whose inputs the scan cannot see, fall back to round, then
build-before-analyze by file name, then path.
Correction scripts added with `extras` run after the round scripts unless a
dependency says otherwise, and figure scripts run last when requested.
verify creates the directories the scripts write into ("workdirs") in its
temporary copy and removes machine-specific paths from the stderr tails it
records.

Usage:
    python3 replicate.py build --arc 5 [--out DIR] [--hash-inputs]
    python3 replicate.py verify --arc 5 [--out DIR] [--timeout 3600]
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR / "workspace"
ARTICLES_DIR = BASE_DIR / "articles"
CARDS_DIR = BASE_DIR / "knowledge" / "prediction_cards"
LOGS_DIR = BASE_DIR / "logs"
REPLICATION_DIR = BASE_DIR / "replication"

SCRIPT_SUFFIXES = {".py", ".R", ".r", ".sql", ".sh"}
OUTSIDE_SOURCE = "intermediate produced outside the package (not shipped)"
MAX_FILE_BYTES = 5 * 1024 * 1024

# Per-arc hand-coding dictionary key maps (M06 part 4): how a dictionary's
# rows join the arc's analysis sample, and which coded field must agree.
# Optional keys: "skip_header" drops dictionary rows that carry "_header":
# true, and "sample_recode" applies [{"when": {col: value}, "set": {col:
# value}}] to the sample rows before the join (values compare as strings).
DICTIONARY_KEY_MAPS = {
    4: {
        "dictionary": "knowledge/hand_coding/round_25.v2.jsonl",
        "skip_header": True,
        "sample": "workspace/r25/analysis_sample_corrected.csv",
        "sample_recode": [{"when": {"cohort": "2", "party": "미래한국당"}, "set": {"opposed": "0"}}],
        "keys": ["cohort", "nominee", "leg_member_uid"],
        "coded_field": "opposed",
        "note": ("Paper D Version 2 (2026-09-26) coding. The stored sample holds the Version 1 coding, "
                 "and the recode moves the six cohort-2 pairs labelled 미래한국당 to the ruling bloc. "
                 "round_25.jsonl is left unchanged and holds the term-snapshot coding."),
    },
}

# Quoted string literal, with an optional Python prefix (f, r, rf ...).
_LIT = r"""(?P<pre>(?<![A-Za-z0-9_])[rRfFbBuU]{1,2})?(?P<q>["'])(?P<body>(?:(?!(?P=q)).)*?)(?P=q)"""
LITERAL_RE = re.compile(_LIT)
KNA_PREFIX_RE = re.compile(r"^/(?:Users|home)/[^/]+/(?:[^\s]*/)?kna/data/processed")
FORUM_ROOT_RE = re.compile(r"^/(?:Users|home)/[^/]+/(?:[^\s]*/)?kna-research-agents")
SETENV_KBL_RE = re.compile(r"^\s*Sys\.setenv\(\s*KBL_DATA\s*=.*\)\s*$")
DATA_NAME_RE = re.compile(r"[A-Za-z0-9_{}\-]+\.(?:parquet|csv|jsonl|json|feather|rds)")


# Arcs published before kna 0.7.0 (2026-09-26). kna 0.7.0 corrected fields
# their papers used (KNA_070_PUBLISHED.md), so their packages run on the kna
# v0.6.0 data named by this environment variable (scripts/setup_kna_v060.sh).
# verify sets KBL_DATA to the same directory.
DATA_PINS = {arc: "KNA_DATA_V060" for arc in (1, 2, 3, 4, 5)}


def kna_data_env(arc) -> str:
    """Name of the environment variable that holds an arc's KNA data."""
    try:
        return DATA_PINS.get(int(arc), "KBL_DATA")
    except (TypeError, ValueError):
        return "KBL_DATA"


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Arc membership
# ---------------------------------------------------------------------------

def arc_rounds(arc) -> list[int]:
    """Rounds of an arc: the static table for Arcs 1-5, else the forum index."""
    import forum_index  # noqa: E402
    try:
        n = int(arc)
    except (TypeError, ValueError):
        n = None
    if n in forum_index.LEGACY_ARCS:
        first, last = forum_index.LEGACY_ARCS[n]
        return list(range(first, last + 1))
    rounds = sorted({m["round"] for m in forum_index.index()
                     if m["round"] and str(m["arc"]) == str(arc)})
    return rounds


def arc_papers(rounds: list[int], articles_dir: Path | None = None) -> list[Path]:
    d = articles_dir or ARTICLES_DIR
    out = []
    for r in rounds:
        out += [p for p in sorted(d.glob(f"*_r{r}.tex")) if "template" not in p.name]
    return out


# ---------------------------------------------------------------------------
# Path rewriting
# ---------------------------------------------------------------------------

def _rewrite_literal(pre: str, q: str, body: str, lang: str) -> tuple[str | None, str | None]:
    """New source text for one string literal, or (None, None) if unchanged."""
    m = KNA_PREFIX_RE.match(body)
    if m:
        rest = body[m.end():].lstrip("/")
        env = 'os.environ["KBL_DATA"]' if lang == "py" else 'Sys.getenv("KBL_DATA")'
        if not rest:
            return env, "kna_data_prefix"
        joiner = "os.path.join" if lang == "py" else "file.path"
        pre_kept = "".join(c for c in pre if c in "fFrR") if lang == "py" else ""
        return f"{joiner}({env}, {pre_kept}{q}{rest}{q})", "kna_data_prefix"
    m = FORUM_ROOT_RE.match(body)
    if m:
        rest = body[m.end():].lstrip("/")
        if rest == "workspace" or rest.startswith("workspace/"):
            rest = rest[len("workspace"):].lstrip("/") or "."
            kind = "forum_workspace"
        elif rest.startswith("articles/figures/"):
            rest = rest[len("articles/"):]
            kind = "forum_figures"
        else:
            kind = "forum_repository"
        return f"{pre}{q}{rest or '.'}{q}", kind
    if body.startswith("workspace/"):
        return f"{pre}{q}{body[len('workspace/'):]}{q}", "repo_relative_workspace"
    return None, None


def rewrite_paths(text: str, lang: str) -> tuple[str, list[dict]]:
    """Rewrite path literals in a script. lang is "py" or "R" (others are
    treated as "R"-like for Sys.getenv, but shell scripts are left as is).
    Returns (new text, [{"line", "kind"}])."""
    rewrites, out_lines = [], []
    needs_os = False
    for n, line in enumerate(text.split("\n"), 1):
        if lang == "R" and SETENV_KBL_RE.match(line):
            out_lines.append("# KBL_DATA is read from the environment (set it before running).")
            rewrites.append({"line": n, "kind": "kbl_data_setenv_removed"})
            continue
        stripped = line.lstrip()
        if stripped.startswith("#"):
            out_lines.append(line)
            continue
        pieces, last = [], 0
        for m in LITERAL_RE.finditer(line):
            new, kind = _rewrite_literal(m.group("pre") or "", m.group("q"), m.group("body"), lang)
            if new is None:
                continue
            pieces.append(line[last:m.start()])
            pieces.append(new)
            last = m.end()
            rewrites.append({"line": n, "kind": kind})
            if lang == "py" and "os." in new:
                needs_os = True
        pieces.append(line[last:])
        out_lines.append("".join(pieces))
    new_text = "\n".join(out_lines)
    if needs_os and not re.search(r"^\s*import\s+os\b|^\s*import\s+[\w, ]*\bos\b", new_text, re.MULTILINE):
        new_text = "import os  # added by replicate.py for KBL_DATA\n" + new_text
    return new_text, rewrites


def _lang(p: Path) -> str | None:
    if p.suffix == ".py":
        return "py"
    if p.suffix in (".R", ".r"):
        return "R"
    return None


def data_inputs(texts: dict) -> dict:
    """Input file names the scripts read (scanned in the original, unrewritten
    text): KNA data (via KBL_DATA or the KNA processed-data prefix), repo
    data/ files (kr-hearings releases) and intermediates produced outside the
    package (workspace files that are not in a round directory)."""
    kna, repo_data, outside = set(), set(), set()
    for text in texts.values():
        for line in text.split("\n"):
            if line.lstrip().startswith("#"):
                continue
            for m in LITERAL_RE.finditer(line):
                body = m.group("body")
                if body.startswith("data/"):
                    repo_data.add(body)
                elif re.match(r"^workspace/[^/]+\.(?:parquet|csv|jsonl)$", body):
                    outside.add(body)
            if re.search(r"KBL_DATA|\bDATA\b|data_dir|kna/data/processed", line):
                for m in LITERAL_RE.finditer(line):
                    name = m.group("body").rsplit("/", 1)[-1]
                    if DATA_NAME_RE.fullmatch(name.replace("%d", "{n}")):
                        kna.add(name.replace("%d", "{n}"))
    return {"kna": sorted(kna), "repo_data": sorted(repo_data), "outside_package": sorted(outside)}


def _describe_inputs(names: dict, hash_inputs: bool, produced: dict | None = None,
                     data_dir: str | None = None) -> list[dict]:
    """produced: {package-relative file: script that writes it}. An outside
    intermediate that a packaged script writes is listed as produced inside."""
    rows = []
    produced = produced or {}
    kbl = data_dir or os.environ.get("KBL_DATA")
    for nm in names["kna"]:
        row = {"source": "KNA (KBL_DATA)", "name": nm, "files": []}
        if kbl and Path(kbl).is_dir():
            pattern = re.sub(r"\{[^}]*\}", "*", nm)
            for f in sorted(Path(kbl).glob(pattern)):
                entry = {"file": f.name, "bytes": f.stat().st_size}
                if hash_inputs:
                    entry["sha256"] = _sha256_file(f)
                row["files"].append(entry)
        rows.append(row)
    for rel in names["repo_data"]:
        f = BASE_DIR / rel
        row = {"source": "kr-hearings release (repository data/)", "name": rel}
        if f.exists():
            row["bytes"] = f.stat().st_size
            if hash_inputs:
                row["sha256"] = _sha256_file(f)
        rows.append(row)
    for rel in names["outside_package"]:
        inner = rel[len("workspace/"):] if rel.startswith("workspace/") else rel
        if inner in produced:
            rows.append({"source": "intermediate produced inside the package", "name": inner,
                         "produced_by": produced[inner]})
        else:
            rows.append({"source": OUTSIDE_SOURCE, "name": rel})
    return rows


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

def _sidecars(rounds: list[int], logs_dir: Path | None = None) -> list[dict]:
    out = []
    d = logs_dir or LOGS_DIR
    for r in rounds:
        for sc in sorted((d / f"r{r:02d}").glob("*.sidecar.json")):
            try:
                out.append(json.loads(sc.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
    return out


def round_provenance(rounds: list[int], logs_dir: Path | None = None) -> dict:
    """Model and CLI per round from the M01 sidecars, else the static
    reconstruction for Arcs 4 and 5."""
    import disclosure  # noqa: E402
    by_round: dict = {}
    for sc in _sidecars(rounds, logs_dir):
        if sc.get("task") != "agent":
            continue
        by_round.setdefault(sc.get("round"), []).append({
            "role": sc.get("role"), "run_id": sc.get("run_id"), "model": sc.get("model"),
            "models_used": sc.get("models_used"), "cli_version": sc.get("cli_version"),
            "effort": sc.get("effort"), "ok": sc.get("ok")})
    out = {}
    for r in rounds:
        if r in by_round:
            out[str(r)] = {"source": "sidecars", "runs": by_round[r]}
        else:
            legacy = disclosure.legacy_provenance(r)
            out[str(r)] = legacy or {"source": "unrecorded"}
    return out


def _analyst_run_id(rnd: int, prov: dict) -> str | None:
    for run in (prov.get(str(rnd)) or {}).get("runs", []) or []:
        if run.get("role") == "data_analyst" and run.get("ok"):
            return run.get("run_id")
    return None


def _versions() -> dict:
    v = {"python": sys.version.split()[0]}
    try:
        from importlib import metadata
        for pkg in ("kna", "pandas", "pyarrow", "statsmodels"):
            try:
                v[pkg] = metadata.version(pkg)
            except metadata.PackageNotFoundError:
                v[pkg] = None
    except ImportError:
        pass
    return v


# ---------------------------------------------------------------------------
# Dictionary join (M06 part 4)
# ---------------------------------------------------------------------------

def validate_dictionary_join(key_map: dict, dict_rows: list[dict], sample_rows: list[dict]) -> dict:
    """Join sample rows to dictionary rows on key_map["keys"] and require the
    coded field to exist and agree. Values compare as strings."""
    keys, field = key_map["keys"], key_map["coded_field"]
    out = {"ok": False, "keys": keys, "coded_field": field, "sample_rows": len(sample_rows),
           "dictionary_rows": len(dict_rows), "unmatched": 0, "mismatches": 0, "problems": []}
    if dict_rows and not any(field in r for r in dict_rows):
        out["problems"].append(f"dictionary rows have no '{field}' field")
        return out
    if sample_rows and field not in sample_rows[0]:
        out["problems"].append(f"sample has no '{field}' column")
        return out

    def norm(v):
        if v is None:
            return ""
        s = str(v).strip()
        return s[:-2] if s.endswith(".0") else s

    index = {}
    for r in dict_rows:
        index.setdefault(tuple(norm(r.get(k)) for k in keys), r)
    for s in sample_rows:
        d = index.get(tuple(norm(s.get(k)) for k in keys))
        if d is None:
            out["unmatched"] += 1
        elif norm(d.get(field)) != norm(s.get(field)):
            out["mismatches"] += 1
    if out["unmatched"]:
        out["problems"].append(f"{out['unmatched']} sample rows have no dictionary row")
    if out["mismatches"]:
        out["problems"].append(f"{out['mismatches']} sample rows disagree with the dictionary on '{field}'")
    out["ok"] = not out["problems"]
    return out


def apply_sample_recode(rows: list[dict], recode: list[dict] | None) -> tuple[list[dict], int]:
    """Apply a key map's sample_recode rules to copies of the sample rows.
    Returns (rows, number of rows a rule matched)."""
    if not recode:
        return rows, 0
    out, hit = [], 0
    for r in rows:
        r = dict(r)
        for rule in recode:
            if all(str(r.get(k, "")).strip() == str(v) for k, v in rule.get("when", {}).items()):
                r.update({k: str(v) for k, v in rule.get("set", {}).items()})
                hit += 1
        out.append(r)
    return out, hit


def check_key_map(key_map: dict, base: Path | None = None) -> dict:
    """validate_dictionary_join on the files a key map names, after dropping
    header rows (skip_header) and recoding the sample (sample_recode)."""
    import csv
    base = base or BASE_DIR
    dpath, spath = base / key_map["dictionary"], base / key_map["sample"]
    if not dpath.exists() or not spath.exists():
        return {"ok": None, "problems": [f"missing {p.name}" for p in (dpath, spath) if not p.exists()]}
    dict_rows = [json.loads(l) for l in dpath.read_text(encoding="utf-8").splitlines() if l.strip()]
    headers = [r for r in dict_rows if isinstance(r, dict) and r.get("_header") is True]
    if key_map.get("skip_header"):
        dict_rows = [r for r in dict_rows if not (isinstance(r, dict) and r.get("_header") is True)]
    with open(spath, encoding="utf-8", newline="") as f:
        sample_rows = list(csv.DictReader(f))
    sample_rows, recoded = apply_sample_recode(sample_rows, key_map.get("sample_recode"))
    res = validate_dictionary_join(key_map, dict_rows, sample_rows)
    res["header_rows_skipped"] = len(headers) if key_map.get("skip_header") else 0
    res["sample_rows_recoded"] = recoded
    return res


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def package_dir(arc, out_root: Path | None = None) -> Path:
    return Path(out_root or REPLICATION_DIR) / f"arc_{arc}"


def _collect(rounds: list[int], workspace_dir: Path, articles_dir: Path, cards_dir: Path) -> list[dict]:
    items = []
    for r in rounds:
        rdir = workspace_dir / f"r{r}"
        if not rdir.is_dir():
            rdir = workspace_dir / f"r{r:02d}"
        if rdir.is_dir():
            for p in sorted(rdir.rglob("*")):
                if p.is_file() and p.suffix in SCRIPT_SUFFIXES:
                    items.append({"src": p, "dest": f"r{r}/{p.relative_to(rdir).as_posix()}",
                                  "round": r, "kind": "script", "role": "data_analyst"})
        card = cards_dir / f"R{r:02d}.json"
        if card.exists():
            items.append({"src": card, "dest": f"cards/{card.name}", "round": r, "kind": "card",
                          "role": "literature_scout"})
    for tex in arc_papers(rounds, articles_dir):
        fig_dir = articles_dir / "figures" / tex.stem
        m = re.search(r"_r(\d+)$", tex.stem)
        for p in sorted(fig_dir.glob("*.R")) if fig_dir.is_dir() else []:
            items.append({"src": p, "dest": f"figures/{tex.stem}/{p.name}",
                          "round": int(m.group(1)) if m else None, "kind": "figure_script",
                          "role": "drafter"})
    return items


SCRIPT_KINDS = ("script", "prep_script", "correction_script")

VERSIONS_NOTE = ("`versions` in MANIFEST.json records the software installed when the package was built. "
                 "Its `kna` entry is the version of the kna software package, not of the data. The data "
                 "inputs are pinned by `data_inputs`, which lists each input file (with its sha256 when the "
                 "package was built with --hash-inputs).")


def needs_kbl_data(manifest: dict) -> bool:
    return any(str(r.get("source", "")).startswith("KNA") for r in manifest.get("data_inputs", []))


def _readme(arc, manifest: dict) -> str:
    scripts = [f for f in manifest["files"] if f["kind"] in SCRIPT_KINDS + ("figure_script",)]
    cmds = manifest.get("commands") or []
    kbl = needs_kbl_data(manifest)
    hearings = any(str(r.get("source", "")).startswith("kr-hearings") for r in manifest.get("data_inputs", []))
    has_cards = any(f["kind"] == "card" for f in manifest["files"])
    if kbl and hearings:
        reads = ("The scripts read the KNA processed data from the directory named by the KBL_DATA "
                 "environment variable and the kr-hearings release files from `data/`.")
    elif kbl:
        reads = ("The scripts read the KNA processed data from the directory named by the KBL_DATA "
                 "environment variable.")
    elif hearings:
        reads = "The scripts read the kr-hearings release files from `data/` and need no KBL_DATA."
    else:
        reads = "The scripts read no KNA data and need no KBL_DATA."
    holds = "the analysis scripts and prediction cards" if has_cards else "the analysis scripts"
    lines = [
        f"# Replication package, Arc {arc}",
        "",
        f"Built {manifest['built']} by replicate.py from the forum's round scripts. Rounds: "
        f"{', '.join('R' + str(r) for r in manifest['rounds'])}.",
        "",
        f"This package holds {holds} only. It contains no data. "
        f"{reads} Derived analysis samples are not included and are available on request.",
        "",
        "## Run",
        "",
        "From this directory" + ((", with KBL_DATA set" if kna_data_env(arc) == "KBL_DATA" else
                                 f", with KBL_DATA and {kna_data_env(arc)} both set to the data/processed "
                                 "folder of kna v0.6.0 (scripts/setup_kna_v060.sh in the forum repository, "
                                 "see KNA_070_PUBLISHED.md)") if kbl else "") + ", in this order:",
        "",
        "```",
    ]
    lines += [c["cmd"] for c in cmds] or ["# no commands declared"]
    lines += ["```", ""]
    workdirs = manifest.get("workdirs") or []
    if workdirs:
        lines += ["The scripts write into these folders, which must exist before the run: "
                  + ", ".join(f"`{d}/`" for d in workdirs) + ".", ""]
    order = manifest.get("order") or {}
    if order.get("edges"):
        declared = any(e["via"] == DECLARED_VIA for e in order["edges"])
        lines += ["The order puts every script that writes a file before the scripts that read it"
                  + (", and follows the dependencies the package builder declared:" if declared else ":"), ""]
        lines += [f"- `{e['before']}` before `{e['after']}` (`{e['via']}`)" for e in order["edges"]]
        lines += [""]
    lines += ["## Files", ""]
    lines += [f"- `{f['path']}` ({'round ' + str(f['round']) if f.get('round') is not None else 'no round'}, "
              f"{f['kind']})" for f in scripts]
    unpackaged = [r["name"] for r in manifest.get("data_inputs", []) if r["source"] == OUTSIDE_SOURCE]
    if unpackaged:
        lines += ["", "## Inputs produced outside this package", ""]
        lines += [f"- `{n}`" for n in unpackaged]
    lines += ["", "## Versions", "", VERSIONS_NOTE]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Command order (dependencies first, then build-before-analyze by name)
# ---------------------------------------------------------------------------

FILE_LITERAL_RE = re.compile(
    r"^[A-Za-z0-9_{}.\-][A-Za-z0-9_{}./\-]*\."
    r"(?:parquet|csv|tsv|jsonl|json|feather|rds|RData|rda|pkl|pickle|npy|npz|txt|xlsx|pdf|png|tex)$")
WRITE_CALL_RE = re.compile(
    r"\.to_(?:csv|parquet|json|excel|feather|pickle)\s*\(|\bwrite_(?:text|bytes|csv|parquet|feather)\s*\("
    r"|\bsavefig\s*\(|\bggsave\s*\(|\bwrite\.csv\s*\(|\bfwrite\s*\(|\bsaveRDS\s*\(|\bsave\s*\("
    r"|\bwriteLines\s*\(|\bnp\.save[z]?\s*\(|\bpq\.write_table\s*\(|\bsink\s*\(")
OPEN_WRITE_RE = re.compile(
    r"""open\(\s*[^,"'()]*?(?P<q>["'])(?P<p>[^"']+)(?P=q)\s*,\s*(?:mode\s*=\s*)?["'][wax]""")
# A literal directly followed by a pathlib write, as in
# (OUTDIR / "key_values.json").write_text(...) or Path("x.csv").open("w").
METHOD_WRITE_AFTER_RE = re.compile(
    r"""^\s*\)*\s*\.\s*(?:write_text|write_bytes)\s*\(|^\s*\)*\s*\.\s*open\(\s*(?:mode\s*=\s*)?["'][wax]""")
ASSIGN_RE = re.compile(r"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_.]*)\s*(?:<-|=(?!=))\s*(?P<rhs>.+)$")
NAME_RANKS = (("prep", "fetch", "download", "extract", "collect", "ingest"),
              ("build", "make", "construct", "create", "assemble"))


def _paren_depth(s: str) -> int:
    """Open minus closed parentheses in s, ignoring string literal bodies."""
    s = LITERAL_RE.sub("''", s)
    return s.count("(") - s.count(")")


def _file_literal(body: str) -> str | None:
    """Normalized relative path of a file literal, or None. A leading f-string
    placeholder directory ({WS}/r28/x.csv) is dropped, because the package
    rewrites such base directories to the package root."""
    body = re.sub(r"^\{[A-Za-z_][A-Za-z0-9_]*\}/", "", body)
    if not FILE_LITERAL_RE.match(body) or body.startswith("/"):
        return None
    p = os.path.normpath(body)
    return None if p.startswith("..") else p


PATH_FIRST_WRITES = (r"\.to_(?:csv|parquet|json|excel|feather|pickle)", r"\bsavefig", r"\bggsave",
                     r"\bnp\.save[z]?", r"\bsink")
PATH_SECOND_WRITES = (r"\bwrite\.csv", r"\bfwrite", r"\bsaveRDS", r"\bwriteLines", r"\bpq\.write_table",
                      r"\bjson\.dump")
READ_RHS_RE = re.compile(r"read|load|open\(")


def _writes_through(name: str, text: str) -> bool:
    """True when a path variable is used as a write target somewhere in the
    text: NAME.write_text(, NAME.open("w"), open(NAME, "w"), NAME as the path
    argument of a write call (first for to_csv, ggsave, ...; second for
    write.csv, saveRDS, ...), or file=/path=/filename=NAME in a write call.
    A variable passed as the content of a write is not a target."""
    n = re.escape(name)
    word = rf"(?<![\w.]){n}(?![\w])"
    first = "|".join(PATH_FIRST_WRITES)
    second = "|".join(PATH_SECOND_WRITES)
    target = re.compile(
        rf"{word}\s*\)*\s*\.\s*(?:write_text|write_bytes)\s*\("
        rf"|{word}\s*\.\s*open\(\s*(?:mode\s*=\s*)?[\"'][wax]"
        rf"|open\(\s*{word}\s*,\s*(?:mode\s*=\s*)?[\"'][wax]"
        rf"|(?:{first})\s*\(\s*(?:filename\s*=\s*)?{word}"
        rf"|(?:{second})\s*\(\s*[^,()]+,\s*(?:file\s*=\s*)?{word}")
    keyword = re.compile(rf"\b(?:file|path|filename|fname|path_or_buf)\s*=\s*{word}")
    for line in text.split("\n"):
        if line.lstrip().startswith("#"):
            continue
        if target.search(line) or (keyword.search(line) and WRITE_CALL_RE.search(line)):
            return True
    return False


def script_io(text: str) -> tuple[set, set]:
    """(reads, writes): normalized relative file paths named by string literals.
    A literal is a write when
      - it is the path argument of open(..., "w"|"a"|"x"),
      - it follows a write call (to_csv, ggsave, write_text, ...) on the same
        line, or sits on a continuation line of such a call,
      - it is directly followed by a pathlib write, as in
        (OUT / "x.json").write_text(...), or
      - it is assigned to a variable (NAME = ... "x.json") that the script
        later uses as a write target.
    Every other file literal is a read. Absolute paths and comment lines are
    ignored. The scan is heuristic, so verify remains the check that the
    resulting order runs."""
    reads, writes = set(), set()
    assigned: dict = {}
    pending = 0                     # open parentheses of a write call continued on later lines
    for line in text.split("\n"):
        if line.lstrip().startswith("#"):
            continue
        open_w = {m.group("p") for m in OPEN_WRITE_RE.finditer(line)}
        wcall = WRITE_CALL_RE.search(line)
        lits = []
        for m in LITERAL_RE.finditer(line):
            p = _file_literal(m.group("body"))
            if p is None:
                continue
            lits.append(p)
            if (pending > 0 or m.group("body") in open_w or (wcall and m.start() > wcall.start())
                    or METHOD_WRITE_AFTER_RE.match(line[m.end():])):
                writes.add(p)
            else:
                reads.add(p)
        if pending > 0:
            pending += _paren_depth(line)
        elif wcall:
            pending = max(_paren_depth(line[wcall.start():]), 0)
        a = ASSIGN_RE.match(line)
        if a and lits and not READ_RHS_RE.search(a.group("rhs")):
            assigned.setdefault(a.group("name"), set()).update(lits)
    for name, lits in assigned.items():
        if _writes_through(name, text):
            writes |= lits
    return reads - writes, writes


def _name_rank(path: str) -> int:
    stem = Path(path).stem.lower()
    for rank, words in enumerate(NAME_RANKS):
        if any(stem.startswith(w) or f"_{w}" in stem for w in words):
            return rank
    return len(NAME_RANKS)


DECLARED_VIA = "declared by the package builder"


def order_commands(entries: list[dict], hints: list[dict] | None = None) -> tuple[list[dict], dict]:
    """entries: [{"path", "text", "round", "kind"}]. hints: further
    dependencies the scan cannot see, [{"before": path, "after": path}].
    Returns (entries in run order, {"method", "edges", "cycle_broken"}).
    Kahn's algorithm: a script runs once every script that writes a file it
    reads, and every script a hint puts before it, has run. Among ready
    scripts the tie-break is (figure scripts last, round with None after all
    rounds, build-before-analyze by name, path). A cycle is broken by the
    tie-break and recorded."""
    io = {e["path"]: script_io(e["text"]) for e in entries}
    writers: dict = {}
    for p, (_, w) in io.items():
        for f in w:
            writers.setdefault(f, []).append(p)
    deps = {p: set() for p in io}
    edges = []
    for p, (r, _) in io.items():
        for f in sorted(r):
            for q in writers.get(f, []):
                if q != p and q not in deps[p]:
                    deps[p].add(q)
                    edges.append({"before": q, "after": p, "via": f})
    for h in hints or []:
        q, p = h.get("before"), h.get("after")
        if q not in io or p not in io or q == p:
            raise ValueError(f"order hint {h!r} names a script that is not in the package")
        if q not in deps[p]:
            deps[p].add(q)
            edges.append({"before": q, "after": p, "via": h.get("via") or DECLARED_VIA})
    by_path = {e["path"]: e for e in entries}

    def key(p):
        e = by_path[p]
        rnd = e.get("round")
        return (1 if e.get("kind") == "figure_script" else 0,
                rnd if isinstance(rnd, int) else 10 ** 6, _name_rank(p), p)

    done, ordered, broken = set(), [], []
    remaining = set(io)
    while remaining:
        ready = [p for p in remaining if deps[p] <= done]
        if not ready:
            p = min(remaining, key=key)
            broken.append(p)
        else:
            p = min(ready, key=key)
        ordered.append(by_path[p])
        done.add(p)
        remaining.discard(p)
    edges.sort(key=lambda e: ([x["path"] for x in ordered].index(e["after"]), e["before"], e["via"]))
    return ordered, {"method": "writers before readers (string literals in the rewritten scripts) and "
                               "dependencies declared by the package builder, then round, then "
                               "build-before-analyze by file name, then path",
                     "edges": edges, "cycle_broken": broken}


def _workdirs(entries: list[dict]) -> list[str]:
    dirs = set()
    for e in entries:
        for f in script_io(e["text"])[1]:
            d = os.path.dirname(f)
            if d and not d.startswith("..") and not os.path.isabs(d):
                dirs.add(d)
    return sorted(dirs)


def build(arc, *, out_root: Path | None = None, workspace_dir: Path | None = None,
          articles_dir: Path | None = None, cards_dir: Path | None = None,
          logs_dir: Path | None = None, rounds: list[int] | None = None,
          hash_inputs: bool = False, extras: list[dict] | None = None,
          outputs: list[dict] | None = None, figure_commands: bool = False,
          notes: dict | None = None, readme_extra: str | None = None,
          order_hints: list[dict] | None = None) -> dict:
    """Build replication/arc_N/ and return its manifest (also written to
    MANIFEST.json). manifest["build"]["ok"] is false when any file still holds
    an absolute path or a leak-lint hit after rewriting. Such a file is not
    written.

    extras: further scripts to ship, [{"src": path, "dest": "v2/x.py",
    "kind": "prep_script" | "correction_script", "role": "...", "after":
    [package paths]}]. They pass through the same rewrite and leak lint and
    get commands like round scripts. "after" lists scripts that must run
    before the extra when the scan cannot see the dependency. outputs:
    declared outputs for verify ({"path", "sha256"} or {"path", "values",
    "tolerance"}). figure_commands: also run the paper's figure scripts,
    after every other script. notes: extra manifest keys. readme_extra: text
    appended to the README. order_hints: further [{"before", "after"}]
    dependencies between package paths, recorded in MANIFEST "order"."""
    import leak_lint  # noqa: E402
    workspace_dir = Path(workspace_dir or WORKSPACE_DIR)
    articles_dir = Path(articles_dir or ARTICLES_DIR)
    cards_dir = Path(cards_dir or CARDS_DIR)
    rounds = rounds if rounds is not None else arc_rounds(arc)
    out = package_dir(arc, out_root)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    private = leak_lint.load_private_patterns()
    prov = round_provenance(rounds, logs_dir)

    items = _collect(rounds, workspace_dir, articles_dir, cards_dir)
    taken = {it["dest"] for it in items}
    hints = [dict(h) for h in order_hints or []]
    for ex in extras or []:
        dest = str(ex["dest"]).lstrip("/")
        if dest in taken or ".." in Path(dest).parts:
            raise ValueError(f"extra destination {dest!r} is taken or leaves the package")
        taken.add(dest)
        hints += [{"before": b, "after": dest} for b in ex.get("after") or []]
        items.append({"src": Path(ex["src"]), "dest": dest, "round": ex.get("round"),
                      "kind": ex.get("kind", "correction_script"), "role": ex.get("role", "unrecorded")})

    files, errors, rewrites, texts, runnable = [], [], [], {}, []
    for it in items:
        src = it["src"]
        if src.stat().st_size > MAX_FILE_BYTES:
            errors.append({"path": it["dest"], "error": "larger than 5 MB, not copied"})
            continue
        raw = src.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            errors.append({"path": it["dest"], "error": "not UTF-8 text"})
            continue
        lang = _lang(src)
        new, rw = rewrite_paths(text, lang) if lang else (text, [])
        hits = leak_lint.scan_text(new, path=it["dest"], private=private)
        if hits:
            errors.append({"path": it["dest"], "error": "absolute path or leak pattern after rewriting",
                           "hits": [{"line": h["line"], "pattern_id": h["pattern_id"]} for h in hits]})
            continue
        dest = out / it["dest"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(new, encoding="utf-8")
        texts[it["dest"]] = text
        rewrites += [{"path": it["dest"], **r} for r in rw]
        files.append({"path": it["dest"], "sha256": _sha256_bytes(new.encode("utf-8")),
                      "source_sha256": _sha256_bytes(raw), "round": it["round"], "kind": it["kind"],
                      "producing_role": it["role"],
                      "run_id": _analyst_run_id(it["round"], prov) if it["kind"] == "script" else None})
        runs = it["kind"] in SCRIPT_KINDS or (figure_commands and it["kind"] == "figure_script")
        if runs and src.suffix in (".py", ".R", ".r"):
            runnable.append({"path": it["dest"], "text": new, "round": it["round"], "kind": it["kind"]})

    ordered, order = order_commands(runnable, hints)
    produced = {}
    for e in ordered:
        for f in sorted(script_io(e["text"])[1]):
            produced.setdefault(f, e["path"])
    commands = [{"cmd": ("python3 " if e["path"].endswith(".py") else "Rscript ") + e["path"],
                 "round": e["round"]} for e in ordered]

    manifest = {
        "arc": arc,
        "rounds": rounds,
        "built": datetime.now().isoformat(timespec="seconds"),
        "publishes": "scripts and cards only (D-17 default); derived data available on request",
        "files": files,
        "path_rewrites": rewrites,
        "data_inputs": _describe_inputs(data_inputs(texts), hash_inputs, produced,
                                      data_dir=os.environ.get(kna_data_env(arc))),
        "versions": _versions(),
        "versions_note": VERSIONS_NOTE.replace("`", ""),
        "provenance": prov,
        "commands": commands,
        "order": order,
        "workdirs": _workdirs(runnable),
        "outputs": list(outputs or []),
        "dictionary_key_map": DICTIONARY_KEY_MAPS.get(int(arc)) if str(arc).isdigit() else None,
        "build": {"ok": not errors, "errors": errors},
        "verify": {"passed": None},
    }
    for k, v in (notes or {}).items():
        if k not in manifest:
            manifest[k] = v
    readme = _readme(arc, manifest)
    if readme_extra:
        readme += "\n" + readme_extra.rstrip("\n") + "\n"
    for name, text in (("README.md", readme), ("MANIFEST.json", json.dumps(manifest, ensure_ascii=False))):
        hits = leak_lint.scan_text(text, path=name, private=private)
        if hits:
            errors.append({"path": name, "error": "absolute path or leak pattern in generated text",
                           "hits": [{"line": h["line"], "pattern_id": h["pattern_id"]} for h in hits]})
    manifest["build"] = {"ok": not errors, "errors": errors}
    (out / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n",
                                       encoding="utf-8")
    (out / "README.md").write_text(readme, encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

def _compare_output(pkg: Path, spec: dict) -> dict:
    """spec: {"path", "sha256"} or {"path", "values": {name: number}, "tolerance"}."""
    p = pkg / spec["path"]
    if not p.exists():
        return {"path": spec["path"], "ok": False, "reason": "missing"}
    if spec.get("sha256"):
        got = _sha256_file(p)
        return {"path": spec["path"], "ok": got == spec["sha256"], "sha256": got}
    if spec.get("values"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"path": spec["path"], "ok": False, "reason": "not JSON"}
        tol = float(spec.get("tolerance", 1e-6))
        diffs = {}
        for k, want in spec["values"].items():
            got = data.get(k)
            if not isinstance(got, (int, float)) or abs(float(got) - float(want)) > tol:
                diffs[k] = {"want": want, "got": got}
        return {"path": spec["path"], "ok": not diffs, "differs": diffs}
    return {"path": spec["path"], "ok": True, "reason": "exists"}


HOME_PATH_RE = re.compile(r"(?:[A-Za-z]:)?[/\\](?:Users|home)[/\\][^/\\\s\"']+")


def scrub_stderr(text: str, tmp: Path) -> str:
    """Remove machine-specific paths from a recorded stderr tail: the
    temporary package copy becomes <package> and any home directory <home>."""
    if not text:
        return text
    for t in sorted({str(Path(tmp).resolve()), str(tmp)}, key=len, reverse=True):
        text = text.replace(t, "<package>")
    return HOME_PATH_RE.sub("<home>", text)


def _safe_rel_dir(d: str) -> bool:
    p = Path(d)
    return bool(d) and not p.is_absolute() and ".." not in p.parts


def verify(arc, *, out_root: Path | None = None, timeout_s: int = 3600) -> dict:
    """Copy the package to a temporary directory, run its commands (with
    KBL_DATA set when the package reads KNA data, from DATA_PINS for a pinned
    arc), compare declared outputs,
    and record verify in MANIFEST.json. Never writes outside the temporary
    copy except the manifest's verify block."""
    pkg = package_dir(arc, out_root)
    mpath = pkg / "MANIFEST.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    result = {"passed": False, "ran": datetime.now().isoformat(timespec="seconds"), "commands": [],
              "outputs": []}
    var = kna_data_env(arc)
    kbl = os.environ.get(var)
    result["kna_data_env"] = var
    if needs_kbl_data(manifest) and (not kbl or not Path(kbl).is_dir()):
        result["error"] = f"{var} is not set to a directory"
        if var != "KBL_DATA":
            result["error"] += (f" (arc {arc} is pinned to the kna v0.6.0 data, see "
                                "KNA_070_PUBLISHED.md and scripts/setup_kna_v060.sh)")
    elif not manifest.get("build", {}).get("ok"):
        result["error"] = "build did not pass"
    else:
        with tempfile.TemporaryDirectory(prefix=f"kna_repl_arc{arc}_") as td:
            tmp = Path(td) / "pkg"
            shutil.copytree(pkg, tmp)
            data_link = BASE_DIR / "data"
            if data_link.is_dir() and not (tmp / "data").exists():
                (tmp / "data").symlink_to(data_link)
            for d in manifest.get("workdirs") or []:
                if _safe_rel_dir(d):
                    (tmp / d).mkdir(parents=True, exist_ok=True)
            env = {**os.environ}
            if kbl:
                env["KBL_DATA"] = kbl
                env[var] = kbl
            ok = True
            for c in manifest.get("commands", []):
                try:
                    r = subprocess.run(c["cmd"].split(), cwd=tmp, env=env, capture_output=True,
                                       text=True, timeout=timeout_s)
                    rec = {"cmd": c["cmd"], "returncode": r.returncode,
                           "stderr_tail": scrub_stderr(r.stderr, tmp)[-800:]}
                except subprocess.TimeoutExpired:
                    rec = {"cmd": c["cmd"], "returncode": None, "stderr_tail": "timeout"}
                result["commands"].append(rec)
                if rec["returncode"] != 0:
                    ok = False
                    break
            if ok:
                result["outputs"] = [_compare_output(tmp, s) for s in manifest.get("outputs", [])]
                ok = all(o["ok"] for o in result["outputs"])
            result["passed"] = ok
    manifest["verify"] = result
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build or verify an arc's replication package.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--arc", required=True)
    b.add_argument("--out", default=None, help="output root (default: replication/)")
    b.add_argument("--hash-inputs", action="store_true", help="sha256 every data input (slow)")
    b.add_argument("--extra", action="append", default=[], metavar="SRC=DEST",
                   help="ship a further script at DEST (repeatable), for example v2/rerun.py")
    b.add_argument("--outputs", default=None, metavar="JSON",
                   help="file with the declared outputs: a list of {path, sha256} or {path, values, tolerance}")
    b.add_argument("--figure-commands", action="store_true", help="also run the paper's figure scripts")
    v = sub.add_parser("verify")
    v.add_argument("--arc", required=True)
    v.add_argument("--out", default=None)
    v.add_argument("--timeout", type=int, default=3600)
    args = ap.parse_args(argv)
    out_root = Path(args.out) if args.out else None
    if args.cmd == "build":
        extras = []
        for spec in args.extra:
            src, sep, dest = spec.partition("=")
            if not sep or not src or not dest:
                ap.error(f"--extra wants SRC=DEST, got {spec!r}")
            extras.append({"src": Path(src), "dest": dest, "kind": "correction_script",
                           "role": "added with --extra"})
        outputs = json.loads(Path(args.outputs).read_text(encoding="utf-8")) if args.outputs else None
        m = build(args.arc, out_root=out_root, hash_inputs=args.hash_inputs, extras=extras,
                  outputs=outputs, figure_commands=args.figure_commands)
        print(f"arc {args.arc}: {len(m['files'])} files, {len(m['path_rewrites'])} path rewrites, "
              f"build {'ok' if m['build']['ok'] else 'FAILED'}")
        for e in m["build"]["errors"]:
            print(f"  - {e['path']}: {e['error']}")
        return 0 if m["build"]["ok"] else 2
    res = verify(args.arc, out_root=out_root, timeout_s=args.timeout)
    print(f"arc {args.arc}: verify {'passed' if res['passed'] else 'FAILED'} {res.get('error', '')}")
    return 0 if res["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
