#!/usr/bin/env python3
"""Scripted precheck rulebook run after each post (M14, M19).

Stage 1 uses extract_dois(), the fixed DOI extractor behind
run_forum.verify_citations (R-05 regex fix), and the data pitfall scan
(load_pitfall_registry, pitfall_hits, pitfall_flags_block), which run_forum
applies to every Analyst post's code blocks and injects into the Critic's
prompt as FLAG-only 'Data pitfall flags'. Everything else is Stage 2
(forum_config.stage2.prechecks, and stage2.gap_c_quotes for R-11) and runs in
FLAG mode, where rules report and never block. R-01, R-02, R-06, R-07 and R-09
may be promoted to FAIL later, and only after a false-positive audit below 10
percent on arcs that have execution traces. R-10 stays FLAG-only for good.
The caller decides whether to run the rulebook. run_all() itself does not
read the stage flag, so it can be used for audits and replays.

Rules (see FORUM_RULES.md for the public wording):
  R-01 card conformance       every committed spec has a results file, every other result is x_
  R-02 number trace           numbers in result tables match a results file or a traced Bash output
  R-04 cross-post quotes      a quoted span attributed to a post occurs in that post
  R-05 citations              DOIs resolve (Crossref, then OpenAlex) with matching author and year
  R-06 falsifier executed     the gate's decisive spec has a results file whose script and output exist
  R-07 null claims            a reported null carries a computed MDE or a TOST against the gate's sesoi
  R-08 status upgrades        an upgrade toward confirmed cites an output file from this round
  R-09 rerun claims           'I reran <file>' matches a Bash command in the same run's trace
  R-10 vocabulary             'pre-registered', 'signed' and 'set by the researcher' used accurately
  R-11 gap quotes             quoted predictions located in an abstract match the abstract

Results go to knowledge/prechecks/R<NN>.json, keyed by post, with flag
counts per rule so flag rates can be followed round by round.

Usage:
    python3 prechecks.py dois <post.md>                  # print extracted DOIs
    python3 prechecks.py run <post.md> --role critic --round N [--offline]
    python3 prechecks.py rates                           # flag rates per rule and round
"""

import argparse
import gzip
import json
import os
import re
import time
import unicodedata
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
LOGS_DIR = BASE_DIR / "logs"
PRECHECKS_DIR = KNOWLEDGE_DIR / "prechecks"
ABSTRACTS_FILE = KNOWLEDGE_DIR / "abstracts.jsonl"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
AGENTS_FILE = BASE_DIR / "agents.json"
DOI_CACHE_FILE = LOGS_DIR / "doi_cache.json"

RULES = {
    "R-01": "card conformance",
    "R-02": "number trace",
    "R-04": "cross-post quotes",
    "R-05": "citations",
    "R-06": "falsifier executed",
    "R-07": "null claims",
    "R-08": "status upgrades",
    "R-09": "rerun claims",
    "R-10": "vocabulary",
    "R-11": "gap quotes",
}
PROMOTABLE = ("R-01", "R-02", "R-06", "R-07", "R-09")
ROLE_RULES = {
    "literature_scout": ("R-04", "R-05", "R-10", "R-11"),
    "data_analyst": ("R-01", "R-02", "R-04", "R-05", "R-06", "R-07", "R-09", "R-10"),
    "critic": ("R-04", "R-05", "R-08", "R-09", "R-10"),
}
GAP_QUOTE_MIN_RATIO = 0.90

# Stops at whitespace, ')', ']', quotes, '*', '`', '<', '>' and non-ASCII text.
DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s)\]\"'*`<>\u0080-￿]+")
DOI_TRAILING = ".,;)]}*`"
FAILED_CONTEXT_RE = re.compile(
    r"\bFAILED\b|\bfailed\b|initial guess|wrong DOI|incorrect DOI|did not resolve|"
    r"does not resolve|could not resolve", re.IGNORECASE)
POST_REF_RE = re.compile(
    r"\b(?:Critic|Analyst|Scout)(?:'s|’s)?\s+(?P<n1>\d{3})\b"
    r"|\b(?P<n2>\d{3})_(?:critic|data_analyst|literature_scout)(?:\.md)?"
    r"|\b(?:[Mm]y|[Oo]ur)\s+(?P<n3>0\d{2})\b")
QUOTE_RE = re.compile(r"\"([^\"\n]{2,400})\"|“([^”\n]{2,400})”")
RERUN_ACTIVE_RE = re.compile(
    r"\b(?:I|we)\s+(?:(?:independently|myself|also)\s+)?re-?ran\b(?P<span>(?:[^.;\n]|\.(?=\w)){0,220})",
    re.IGNORECASE)
RERUN_PASSIVE_RE = re.compile(
    r"(?P<span>(?:[\w./-]+\.(?:py|R|sh|do)\b[,\s]*(?:and\s+)?){1,4})\s*(?:re-?run|re-?executed|reran)\b")
SCRIPT_RE = re.compile(r"[\w./-]+\.(?:py|R|sh|do|ipynb)\b")
EXEC_RE = re.compile(r"\b(?:python3?|Rscript|bash|sh|uv run|ipython)\b|(?:^|\s)\./")
PREREG_RE = re.compile(r"\bpre-?regist(?:ered|ration|er)\b", re.IGNORECASE)
REGISTRY_RE = re.compile(r"\bcard R\d+\b|\bcommit [0-9a-f]{7,40}\b|osf\.io/\w+|aspredicted|"
                         r"AEARCTR-\d+|\bEGAP\b|\bregistry\b", re.IGNORECASE)
SIGNED_AGENT_RE = re.compile(
    r"\bsigned\s+(?:failure condition|condition|threshold|margin|bar|criterion|criteria|"
    r"decision rule|pre-?commitment)", re.IGNORECASE)
RESEARCHER_SET_RE = re.compile(
    r"set by the researcher|the researcher's (?:signed )?(?:gate|prior|falsifier|entry)[^.]{0,40}"
    r"\b(?:chose|set|wrote|specified|picked)\b|the researcher (?:chose|set|wrote|specified|picked)\b",
    re.IGNORECASE)
TABLE_SECTION_RE = re.compile(r"card vs observed|survival table|baseline vs observed", re.IGNORECASE)
NUM_RE = re.compile(r"(?<![\w.])([-+−]?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d+)?)(?![\w])")
STATUS_RANK = {"new": 0, "prior": 0, "preliminary": 1, "refined": 2, "unchanged": None,
               "confirmed": 3, "contested": -1, "overturned": -2, "retracted": -2, "withdrawn": -2}
OUTPUT_EXT_RE = re.compile(r"[\w./-]+\.(?:json|csv|log|txt|md|png|pdf|parquet|tex)\b")


# --------------------------------------------------------------------------
# DOIs (R-05, Stage 1 extractor)
# --------------------------------------------------------------------------

def extract_dois(text: str) -> list[str]:
    """DOIs in a post, in order of first appearance, de-duplicated without
    regard to case. Markdown emphasis, backticks and trailing punctuation
    are not part of the DOI."""
    seen, out = set(), []
    for m in DOI_RE.finditer(text or ""):
        d = m.group(0)
        prev = None
        while prev != d:
            prev, d = d, d.rstrip(DOI_TRAILING)
        if "/" not in d or d.endswith("/"):
            continue
        key = d.lower()
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


# --------------------------------------------------------------------------
# Data pitfall flags (Stage 1, FLAG only)
# --------------------------------------------------------------------------

PITFALLS_FILE = KNOWLEDGE_DIR / "data_pitfalls.md"
PITFALL_REGISTRY_NAME = "kna_data_pitfalls"
PITFALL_FIELDS = ("id", "description", "regex", "alternative")
JSON_FENCE_RE = re.compile(r"^```json[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
CODE_FENCE_RE = re.compile(r"^(?P<fence>`{3,}|~{3,})(?P<lang>[^\n`]*)\n(?P<body>.*?)^(?P=fence)[ \t]*$",
                           re.MULTILINE | re.DOTALL)


def load_pitfall_registry(path: Path | None = None) -> list[dict]:
    """The machine-readable pitfall list in knowledge/data_pitfalls.md: the
    ```json block whose "registry" is "kna_data_pitfalls". Each entry has id,
    description, regex (a Python regular expression that detects misuse in
    analysis code), alternative (the correct way) and optional flags ("i").
    An entry with a missing field or a regex that does not compile is left
    out with a warning. A missing or unreadable file gives an empty list, so
    the scan never blocks a round (tests/test_kna_seniority.py checks that
    the shipped registry parses in full)."""
    p = Path(path) if path else PITFALLS_FILE
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return []
    for m in JSON_FENCE_RE.finditer(text):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or data.get("registry") != PITFALL_REGISTRY_NAME:
            continue
        out = []
        for entry in data.get("pitfalls") or []:
            if not isinstance(entry, dict) or any(not str(entry.get(k) or "").strip() for k in PITFALL_FIELDS):
                print(f"  [Pitfalls] registry entry skipped (missing field): {str(entry)[:80]}")
                continue
            flags = re.IGNORECASE if "i" in str(entry.get("flags") or "") else 0
            try:
                rx = re.compile(entry["regex"], flags | re.MULTILINE)
            except re.error as e:
                print(f"  [Pitfalls] registry entry {entry['id']} skipped (regex error: {e})")
                continue
            out.append({**entry, "_rx": rx})
        return out
    return []


def code_blocks(text: str) -> list[dict]:
    """Fenced code blocks of a post: {"lang", "code", "line"} with line the
    post line of the block's first code line."""
    out = []
    for m in CODE_FENCE_RE.finditer(text or ""):
        first = (text or "").count("\n", 0, m.start("body")) + 1
        out.append({"lang": m.group("lang").strip().lower(), "code": m.group("body"), "line": first})
    return out


def pitfall_hits(text: str, registry: list[dict] | None = None) -> list[dict]:
    """Registry pattern matches inside the post's code blocks, in post order:
    {"id", "line", "match", "lang", "description", "alternative"}. A match is
    a flag for the Critic, never a verdict. Text outside code blocks is not
    scanned."""
    registry = load_pitfall_registry() if registry is None else registry
    hits, seen = [], set()
    for block in code_blocks(text):
        if block["lang"] == "card":
            continue
        for entry in registry:
            rx = entry.get("_rx")
            if rx is None:
                continue
            for m in rx.finditer(block["code"]):
                line = block["line"] + block["code"].count("\n", 0, m.start())
                if (entry["id"], line) in seen:
                    continue
                seen.add((entry["id"], line))
                src = block["code"].splitlines()[line - block["line"]].strip() \
                    if line - block["line"] < len(block["code"].splitlines()) else m.group(0)
                hits.append({"id": entry["id"], "line": line, "match": src[:160], "lang": block["lang"],
                             "description": entry["description"], "alternative": entry["alternative"]})
    hits.sort(key=lambda h: (h["line"], h["id"]))
    return hits


PITFALL_LINES_SHOWN = 6   # matched lines listed per pitfall in the Critic prompt


def pitfall_flags_block(hits: list[dict], post_name: str) -> str:
    """The 'Data pitfall flags' prompt block for the Critic, one item per
    pitfall (its description and alternative once, then up to
    PITFALL_LINES_SHOWN matched lines). Empty without hits."""
    if not hits:
        return ""
    lines = ["\n## Data pitfall flags\n",
             f"The orchestrator scanned the code blocks of {post_name} against the pitfall registry in "
             "knowledge/data_pitfalls.md. A flag is a pattern match, not a finding. Check whether the code "
             "misuses the field. If it does, the numbers that depend on it are unverified until the Analyst "
             "reruns them with the correct alternative.\n"]
    by_id: dict = {}
    for h in hits:
        by_id.setdefault(h["id"], []).append(h)
    for pid, group in by_id.items():
        first = group[0]
        n = len(group)
        lines.append(f"- `{pid}` ({n} matched line{'s' if n != 1 else ''}). {first['description']} "
                     f"Correct alternative: {first['alternative']}")
        for h in group[:PITFALL_LINES_SHOWN]:
            shown = str(h["match"]).replace("`", "'")
            lines.append(f"  - line {h['line']} of {post_name}: `{shown}`")
        if n > PITFALL_LINES_SHOWN:
            lines.append(f"  - and {n - PITFALL_LINES_SHOWN} more line(s)")
    return "\n".join(lines) + "\n"


def doi_variants(doi: str) -> list[str]:
    """Forms to try when resolving. A few registered DOIs end in a dot that
    extract_dois strips (Noh 2019, 10.18808/jopr.2019.2.5.)."""
    return [doi, doi + "."]


def _mailto() -> str | None:
    return os.environ.get("KNA_MAILTO") or None


def _http_get(url: str, timeout: int = 12):
    import requests  # noqa: E402  (requests bundles its own CA bundle)
    headers = {"User-Agent": "kna-research-agents/2.1" + (f" (mailto:{_mailto()})" if _mailto() else "")}
    return requests.get(url, headers=headers, timeout=timeout)


def _strip_tags(s: str | None) -> str | None:
    if not s:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def _inverted_to_text(inv: dict | None) -> str | None:
    if not inv:
        return None
    pos = []
    for word, idxs in inv.items():
        for i in idxs:
            pos.append((i, word))
    return " ".join(w for _, w in sorted(pos))


def _crossref(doi: str) -> dict | None:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}"
    if _mailto():
        url += f"?mailto={urllib.parse.quote(_mailto())}"
    r = _http_get(url)
    if r.status_code != 200:
        return None
    msg = r.json().get("message", {})
    years = set()
    for k in ("issued", "published-print", "published-online", "published"):
        parts = (msg.get(k) or {}).get("date-parts") or [[None]]
        if parts and parts[0] and parts[0][0]:
            years.add(int(parts[0][0]))
    authors = msg.get("author") or []
    return {
        "found": True, "source": "crossref", "resolved_as": doi,
        "first_author": (authors[0].get("family") or authors[0].get("name")) if authors else None,
        "years": sorted(years),
        "title": (msg.get("title") or [None])[0],
        "abstract": _strip_tags(msg.get("abstract")),
    }


def _openalex(doi: str) -> dict | None:
    url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi, safe='/')}"
    if _mailto():
        url += f"?mailto={urllib.parse.quote(_mailto())}"
    r = _http_get(url)
    if r.status_code != 200:
        return None
    w = r.json()
    auth = (w.get("authorships") or [{}])[0].get("author", {}).get("display_name")
    return {
        "found": True, "source": "openalex", "resolved_as": doi,
        "first_author": auth.split()[-1] if auth else None,
        "years": [w["publication_year"]] if w.get("publication_year") else [],
        "title": w.get("title"),
        "abstract": _inverted_to_text(w.get("abstract_inverted_index")),
    }


def load_doi_cache(path: Path | None = None) -> dict:
    p = path or DOI_CACHE_FILE
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_doi_cache(cache: dict, path: Path | None = None) -> None:
    p = Path(path or DOI_CACHE_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def resolve_doi(doi: str, cache: dict, *, offline: bool = False, delay_s: float = 0.2) -> dict:
    """Crossref first, OpenAlex on a miss, both on the trailing-dot variant
    too. Answers are cached by lower-cased DOI. A network error is returned
    as found None and is not cached. offline=True answers from the cache only."""
    key = doi.lower()
    if key in cache:
        return cache[key]
    if offline:
        return {"found": None, "source": "offline", "resolved_as": None}
    try:
        rec = None
        for lookup in (_crossref, _openalex):
            for v in doi_variants(doi):
                rec = lookup(v)
                time.sleep(delay_s)
                if rec:
                    break
            if rec:
                break
    except Exception as e:  # network trouble is not evidence against the DOI
        return {"found": None, "source": f"error: {type(e).__name__}", "resolved_as": None}
    rec = rec or {"found": False, "source": "crossref+openalex", "resolved_as": None}
    cache[key] = rec
    return rec


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return re.sub(r"[^a-z]", "", "".join(c for c in s if not unicodedata.combining(c)).lower())


_SURNAME = r"[A-Z][^\s,()]*(?:\s(?:i|de|van|von|der|den|da|del|di|du|dos|le|la)\s[A-Z][^\s,()]*)*"
INSTITUTION_RE = re.compile(r"univ|service|institut|center|centre|office|ministry|research|"
                            r"대학|교수|과정|연구|학과", re.IGNORECASE)


def _claimed_author_year(text: str, doi: str) -> tuple[str | None, int | None]:
    """First-author surname and year the post attaches to a DOI. A
    reference-list line wins over an inline 'Name (YYYY, doi:...)' citation."""
    lines = [ln for ln in (text or "").splitlines() if doi.lower() in ln.lower()]
    for line in lines:
        m = re.match(r"^\s*(?:[-*]\s+)?(" + _SURNAME + r"),[^\n]*?\.\s(\d{4})[a-z]?\.\s", line)
        if m:
            return m.group(1), int(m.group(2))
    for line in lines:
        pos = line.lower().find(doi.lower())
        m = re.search(r"\((\d{4})[a-z]?,\s*(?:doi:\s*)?$", line[:pos])
        if m:
            seg = re.split(r"[:;.!?*()\[\]]", line[:m.start()])[-1]
            tok = re.search(_SURNAME, seg)
            if tok:
                return tok.group(0), int(m.group(1))
    return None, None


def _is_surname_field(fam: str) -> bool:
    """False for record author fields that hold an affiliation or a
    corporate name (common in Korean Crossref deposits)."""
    return bool(re.search(r"[A-Za-z]", fam)) and len(fam.split()) <= 3 \
        and "," not in fam and not INSTITUTION_RE.search(fam)


def _reported_failed(text: str, doi: str) -> bool:
    """True when every occurrence of the DOI sits next to words reporting it
    as a failed or wrong DOI (a Scout reporting its own corrected guess)."""
    low, d = (text or "").lower(), doi.lower()
    hits = [m.start() for m in re.finditer(re.escape(d), low)]
    if not hits:
        return False
    return all(FAILED_CONTEXT_RE.search(text[max(0, i - 120): i + len(d) + 60]) for i in hits)


def rule_r05(text: str, cache: dict, *, offline: bool = False) -> dict:
    details, flagged = [], 0
    for d in extract_dois(text):
        if _reported_failed(text, d):
            details.append({"doi": d, "result": "reported_failed", "flag": False})
            continue
        rec = resolve_doi(d, cache, offline=offline)
        item = {"doi": d, "result": "resolved", "flag": False, "source": rec.get("source")}
        if rec.get("found") is None:
            item.update(result="unchecked", flag=True)
        elif not rec.get("found"):
            item.update(result="does not resolve on Crossref or OpenAlex", flag=True)
        else:
            if rec.get("resolved_as") and rec["resolved_as"] != d:
                item["resolved_as"] = rec["resolved_as"]
            surname, year = _claimed_author_year(text, d)
            fam = rec.get("first_author") or ""
            if surname and fam and not _is_surname_field(fam):
                item["author_check"] = "skipped: record author field is not a surname"
            elif surname and fam:
                a, b = _fold(surname), _fold(fam)
                if a and b and not (a in b or b in a):
                    item.update(result=f"first author mismatch: post {surname}, record {fam}", flag=True)
            if year and rec.get("years") and year not in rec["years"]:
                item.update(result=f"year mismatch: post {year}, record {rec['years']}", flag=True)
        flagged += item["flag"]
        details.append(item)
    return _rule("R-05", "FLAG" if flagged else "PASS", details)


# --------------------------------------------------------------------------
# Traces
# --------------------------------------------------------------------------

def load_trace(source) -> list[dict]:
    """Events from stream-json JSONL, a verbose JSON array, or an archived
    transcript (.jsonl.gz). Accepts a list of event dicts, one path, or a
    list of paths (attempts are concatenated in order)."""
    if not source:
        return []
    if isinstance(source, list) and all(isinstance(x, dict) for x in source):
        return source
    paths = source if isinstance(source, (list, tuple)) else [source]
    events = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        raw = gzip.open(p, "rt", encoding="utf-8").read() if p.suffix == ".gz" \
            else p.read_text(encoding="utf-8", errors="replace")
        s = raw.strip()
        if s.startswith("["):
            try:
                events += [e for e in json.loads(s) if isinstance(e, dict)]
                continue
            except json.JSONDecodeError:
                pass
        for line in raw.splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(e, dict):
                events.append(e)
    return events


def tool_calls(events: list[dict]) -> list[dict]:
    """[{"idx", "name", "input", "id"}] for every tool_use, in order."""
    out = []
    for e in events or []:
        msg = e.get("message") if isinstance(e.get("message"), dict) else {}
        for item in msg.get("content") or []:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                out.append({"idx": len(out), "name": item.get("name"),
                            "input": item.get("input") or {}, "id": item.get("id")})
    return out


def tool_outputs(events: list[dict]) -> list[str]:
    """Text of every tool_result, in order."""
    out = []
    for e in events or []:
        msg = e.get("message") if isinstance(e.get("message"), dict) else {}
        for item in msg.get("content") or []:
            if not (isinstance(item, dict) and item.get("type") == "tool_result"):
                continue
            c = item.get("content")
            if isinstance(c, str):
                out.append(c)
            elif isinstance(c, list):
                out.append(" ".join(x.get("text", "") for x in c if isinstance(x, dict)))
    return out


def bash_commands(events: list[dict]) -> list[str]:
    return [str(c["input"].get("command", "")) for c in tool_calls(events) if c["name"] == "Bash"]


# --------------------------------------------------------------------------
# Text rules
# --------------------------------------------------------------------------

def _rule(rid: str, status: str, details: list, blocking: bool = False, note: str = "") -> dict:
    out = {"id": rid, "name": RULES[rid], "status": status, "blocking": blocking, "details": details}
    if note:
        out["note"] = note
    return out


def _norm_quote(s: str) -> str:
    s = s.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[*_`]", "", s)
    return re.sub(r"\s+", " ", s).strip().casefold()


def _post_file(num: int, forum_dir: Path) -> Path | None:
    hits = sorted(forum_dir.glob(f"{num:03d}_*.md"))
    return hits[0] if hits else None


def rule_r04(text: str, post_name: str, forum_dir: Path | None = None) -> dict:
    """A quoted span attributed to another post (a post reference earlier in
    the same clause, within 200 characters) must occur in that post."""
    forum_dir = forum_dir or FORUM_DIR
    own = re.match(r"^(\d+)_", post_name or "")
    own_num = int(own.group(1)) if own else None
    refs = [(m.start(), m.end(), int(m.group("n1") or m.group("n2") or m.group("n3")))
            for m in POST_REF_RE.finditer(text)]
    details, flagged, cache = [], 0, {}
    for q in QUOTE_RE.finditer(text):
        span = q.group(1) or q.group(2)
        before = [r for r in refs if r[1] <= q.start() and q.start() - r[1] <= 200]
        if not before:
            continue
        _, end, num = before[-1]
        gap = text[end:q.start()]
        if re.search(r"[.;!?]\s|\n", gap) or QUOTE_RE.search(gap):
            continue
        if num == own_num:
            continue
        if num not in cache:
            p = _post_file(num, forum_dir)
            cache[num] = _norm_quote(p.read_text(encoding="utf-8")) if p else None
        body = cache[num]
        line = text.count("\n", 0, q.start()) + 1
        if body is None:
            details.append({"line": line, "post": f"{num:03d}", "quote": span, "result": "post not found",
                            "flag": False})
            continue
        frags = [f for f in re.split(r"…|\.\.\.", _norm_quote(span)) if len(f.strip()) >= 3]
        missing = [f.strip() for f in frags if f.strip() not in body]
        item = {"line": line, "post": f"{num:03d}", "quote": span,
                "result": "found" if not missing else "not found in the attributed post",
                "flag": bool(missing)}
        flagged += bool(missing)
        details.append(item)
    return _rule("R-04", "FLAG" if flagged else ("PASS" if details else "SKIP"), details)


def _gate_provenance(gate: dict | None) -> tuple[str, str]:
    g = gate or {}
    return (str(g.get("drafted_by") or "unrecorded"), str(g.get("signed_by") or "unrecorded"))


def rule_r10(text: str, gate: dict | None = None) -> dict:
    """Vocabulary. FLAG-only permanently."""
    details = []
    for i, line in enumerate(text.splitlines(), 1):
        for sent in re.split(r"(?<=[.!?])\s+", line):
            if PREREG_RE.search(sent) and not REGISTRY_RE.search(sent):
                details.append({"line": i, "term": "pre-registered", "text": sent.strip()[:160],
                                "why": "no registry id or committed card in the sentence"})
            m = SIGNED_AGENT_RE.search(sent)
            if m:
                details.append({"line": i, "term": m.group(0), "text": sent.strip()[:160],
                                "why": "'signed' applied to an agent-written condition"})
    drafted, signed = _gate_provenance(gate)
    # D-10: "set by the researcher" is allowed only when signed_by names the
    # researcher. A substring test would also match the delegation signer
    # ("... under the researcher's standing delegation ...").
    researcher_signed = re.sub(r"\s+", " ", signed).strip().lower().startswith("researcher")
    if not researcher_signed:
        for i, line in enumerate(text.splitlines(), 1):
            m = RESEARCHER_SET_RE.search(line)
            if m:
                details.append({"line": i, "term": m.group(0)[:80], "text": line.strip()[:160],
                                "why": f"gate provenance is drafted_by {drafted}, signed_by {signed}"})
    return _rule("R-10", "FLAG" if details else "PASS", details,
                 note="FLAG-only permanently")


def _findings_rows(text: str) -> list[tuple[int, list[str]]]:
    rows, inside = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"^#{1,6}\s", line):
            inside = bool(re.search(r"findings status", line, re.IGNORECASE))
            continue
        if inside and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and not all(re.fullmatch(r":?-{2,}:?", c or "--") for c in cells):
                rows.append((i, cells))
    return rows


def _status_word(s: str) -> str:
    return re.sub(r"[^a-z]", " ", s.lower()).split()[0] if re.search(r"[a-z]", s.lower()) else ""


def rule_r08(text: str, round_num: int) -> dict:
    """An upgrade toward confirmed must cite an output file (not a script)
    from this round. A downgrade needs a stated reason."""
    details, flagged = [], 0
    for line, cells in _findings_rows(text):
        row = " | ".join(cells)
        m = re.search(r"([A-Za-z*]+)[^|]*?(?:→|->)\s*\**([A-Za-z]+)", row)
        if not m:
            continue
        a, b = _status_word(m.group(1)), _status_word(m.group(2))
        ra, rb = STATUS_RANK.get(a), STATUS_RANK.get(b)
        if ra is None or rb is None or ra == rb:
            continue
        reason = cells[-1] if len(cells) > 1 else ""
        if rb > ra:
            outputs = [p for p in OUTPUT_EXT_RE.findall(row)
                       if re.search(rf"\br{int(round_num)}\b|results/", p) or "/" not in p]
            ok = bool(outputs)
            details.append({"line": line, "change": f"{a} -> {b}", "flag": not ok,
                            "result": "cites " + ", ".join(outputs) if ok
                            else "upgrade cites no output file from this round"})
            flagged += not ok
        else:
            ok = len(re.findall(r"\w+", reason)) >= 3
            details.append({"line": line, "change": f"{a} -> {b}", "flag": not ok,
                            "result": "reason stated" if ok else "downgrade without a stated reason"})
            flagged += not ok
    return _rule("R-08", "FLAG" if flagged else ("PASS" if details else "SKIP"), details)


def rerun_claims(text: str) -> list[dict]:
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for rx in (RERUN_ACTIVE_RE, RERUN_PASSIVE_RE):
            for m in rx.finditer(line):
                for f in SCRIPT_RE.findall(m.group("span")):
                    out.append({"line": i, "file": f})
    seen, uniq = set(), []
    for c in out:
        if Path(c["file"]).name not in seen:
            seen.add(Path(c["file"]).name)
            uniq.append(c)
    return uniq


def rule_r09(text: str, events: list[dict] | None) -> dict:
    claims = rerun_claims(text)
    if not claims:
        return _rule("R-09", "SKIP", [], note="no rerun claims")
    if not events:
        return _rule("R-09", "SKIP", [{"file": c["file"], "line": c["line"]} for c in claims],
                     note="no trace for this run")
    cmds = bash_commands(events)
    details, flagged = [], 0
    for c in claims:
        base = Path(c["file"]).name
        ran = any(base in cmd and EXEC_RE.search(cmd) for cmd in cmds)
        details.append({**c, "flag": not ran,
                        "result": "executed in trace" if ran else "no Bash command in the trace executes it"})
        flagged += not ran
    return _rule("R-09", "FLAG" if flagged else "PASS", details)


# --------------------------------------------------------------------------
# Card and results rules
# --------------------------------------------------------------------------

def _numbers_in(value) -> list[float]:
    out = []
    if isinstance(value, bool):
        return out
    if isinstance(value, (int, float)):
        out.append(float(value))
    elif isinstance(value, dict):
        for k, v in value.items():
            if not str(k).startswith("_"):
                out += _numbers_in(v)
    elif isinstance(value, list):
        for v in value:
            out += _numbers_in(v)
    return out


def _parse_num(tok: str) -> tuple[float, int] | None:
    t = tok.replace("−", "-").replace(",", "")
    if not re.search(r"\d", t):
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    dec = len(t.split(".")[1]) if "." in t else 0
    return v, dec


def _matches(x: float, dec: int, candidates: list[float]) -> bool:
    for v in candidates:
        for c in (v, v * 100, abs(v), abs(v) * 100):
            if round(c, dec) == round(abs(x) if c >= 0 and x < 0 and c == abs(v) else x, dec):
                return True
            if dec == 0 and abs(c - x) < 0.5 and float(x).is_integer() and c == round(c):
                return True
    return False


def result_tables(text: str) -> list[dict]:
    """Rows of the Card vs Observed, Survival and Baseline vs Observed tables,
    restricted to observed or result columns."""
    out, inside, header = [], False, None
    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"^#{1,6}\s", line):
            inside, header = bool(TABLE_SECTION_RE.search(line)), None
            continue
        if not inside or not line.strip().startswith("|"):
            if inside and header and not line.strip():
                header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c or "--") for c in cells):
            continue
        if header is None:
            header = cells
            continue
        cols = [j for j, h in enumerate(header) if re.search(r"observed|result|estimate", h, re.I)]
        cols = cols or list(range(1, len(cells)))
        out.append({"line": i, "cells": [cells[j] for j in cols if j < len(cells)]})
    return out


def rule_r02(text: str, results: dict | None, events: list[dict] | None) -> dict:
    cands: list[float] = []
    for res in (results or {}).values():
        cands += _numbers_in(res)
    for out in tool_outputs(events or []):
        for tok in NUM_RE.findall(out):
            p = _parse_num(tok)
            if p:
                cands.append(p[0])
    if not cands:
        return _rule("R-02", "SKIP", [], note="no results files and no trace to trace numbers to")
    details, flagged = [], 0
    for row in result_tables(text):
        for cell in row["cells"]:
            clean = re.sub(r"\b(?:R|A)\d+\b|\b(?:95|90|80)%\s*(?:CI|interval|power)", " ", cell)
            for tok in NUM_RE.findall(clean):
                p = _parse_num(tok)
                if p is None:
                    continue
                x, dec = p
                if not _matches(x, dec, cands):
                    details.append({"line": row["line"], "number": tok, "flag": True,
                                    "result": "no results value or traced output at this precision"})
                    flagged += 1
    return _rule("R-02", "FLAG" if flagged else "PASS", details)


def _decisive_spec(gate_card: dict | None) -> dict | None:
    specs = (gate_card or {}).get("spec_plan") or []
    return next((s for s in specs if s.get("decisive")), None) \
        or next((s for s in specs if s.get("role") == "primary"), None)


def rule_r01(card: dict | None, results: dict | None) -> dict:
    if not card:
        return _rule("R-01", "SKIP", [], note="no committed card for this round")
    results = results or {}
    details, flagged = [], 0
    planned = {s.get("spec_id") for s in card.get("spec_plan") or []}
    for sid in sorted(planned):
        ok = sid in results
        details.append({"spec_id": sid, "flag": not ok, "result": "results file present" if ok
                        else "no results file (NOT COMPUTABLE must still be written as a result)"})
        flagged += not ok
    for sid in sorted(set(results) - planned):
        ok = sid.startswith("x_")
        details.append({"spec_id": sid, "flag": not ok,
                        "result": "exploratory" if ok else "result for a spec not on the card without x_ prefix"})
        flagged += not ok
    return _rule("R-01", "FLAG" if flagged else "PASS", details)


def rule_r06(gate_card: dict | None, results_by_round: dict, exists=None) -> dict:
    exists = exists or (lambda p: bool(p) and (BASE_DIR / str(p)).exists())
    spec = _decisive_spec(gate_card)
    if spec is None:
        return _rule("R-06", "SKIP", [], note="no committed opening card with a decisive spec")
    sid = spec.get("spec_id")
    for r in sorted(results_by_round):
        res = (results_by_round[r] or {}).get(sid)
        if res and str(res.get("status", "")).lower() != "not_computable":
            missing = [k for k in ("script", "output") if not exists(res.get(k))]
            if missing:
                return _rule("R-06", "FLAG", [{"spec_id": sid, "round": r, "flag": True,
                                               "result": "missing " + " and ".join(missing)}])
            return _rule("R-06", "PASS", [{"spec_id": sid, "round": r, "flag": False,
                                           "result": "results, script and output present"}])
    return _rule("R-06", "FLAG", [{"spec_id": sid, "flag": True,
                                   "result": "the gate's decisive spec has no results file yet"}])


def rule_r07(results: dict | None, card: dict | None, gate: dict | None) -> dict:
    import prediction_card as pc
    sesoi = pc._first_number((gate or {}).get("sesoi"))
    specs = {s.get("spec_id"): s for s in (card or {}).get("spec_plan") or []}
    details, flagged = [], 0
    for sid, res in sorted((results or {}).items()):
        lo, hi = res.get("ci_low"), res.get("ci_high")
        if "reported_null" in res:
            is_null = bool(res["reported_null"])
        else:
            spec = specs.get(sid)
            is_null = bool(spec) and spec.get("role") in pc.KILL_ROLES and lo is not None \
                and hi is not None and lo <= 0 <= hi
        if not is_null:
            continue
        has_mde = res.get("mde") is not None
        has_tost = res.get("tost_p") is not None and res.get("equivalence_margin") is not None
        problem = None
        if not (has_mde or has_tost):
            problem = "null without a computed MDE (80 percent power, alpha .05) or a TOST"
        elif has_tost and sesoi is not None:
            margins = res["equivalence_margin"]
            margins = margins if isinstance(margins, list) else [margins]
            if any(abs(float(m)) > abs(float(sesoi)) for m in margins if m is not None) and not has_mde:
                problem = f"TOST margin wider than the gate's sesoi ({sesoi})"
        details.append({"spec_id": sid, "flag": bool(problem), "result": problem or "bounded"})
        flagged += bool(problem)
    return _rule("R-07", "FLAG" if flagged else ("PASS" if details else "SKIP"), details)


def _abstract_for(doi: str, cache: dict, abstracts: dict | None, offline: bool) -> str | None:
    key = doi.lower()
    if abstracts and abstracts.get(key):
        return abstracts[key]
    rec = cache.get(key) or (None if offline else resolve_doi(doi, cache))
    return (rec or {}).get("abstract")


def load_abstracts(path: Path | None = None) -> dict:
    out = {}
    p = path or ABSTRACTS_FILE
    if not Path(p).exists():
        return out
    for line in Path(p).read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("doi") and r.get("abstract"):
            out[str(r["doi"]).lower().replace("https://doi.org/", "")] = r["abstract"]
    return out


def quote_ratio(quote: str, abstract: str) -> float:
    """Best token-set ratio (0-1) of the quote against any sentence or pair
    of adjacent sentences of the abstract."""
    from rapidfuzz import fuzz
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", abstract or "") if s.strip()]
    spans = sents + [" ".join(sents[i:i + 2]) for i in range(len(sents) - 1)]
    return max((fuzz.token_set_ratio(quote, s) / 100.0 for s in spans), default=0.0)


def rule_r11(card: dict | None, cache: dict, *, abstracts: dict | None = None,
             offline: bool = False) -> dict:
    """Quoted gap predictions located in an abstract must match it at a
    token-set ratio of 0.9 or above. Page or section quotes are passed to
    the Critic as unverified full-text quotes."""
    import prediction_card as pc
    ev = ((card or {}).get("gap") or {}).get("evidence") or {}
    sides = [(k, ev.get(k)) for k in ("lit_a", "lit_b") if isinstance(ev.get(k), dict)]
    if ev.get("quoted_prediction") and ev.get("theory_source"):
        sides.append(("theory_source", {"doi": ev["theory_source"], "quoted_prediction": ev["quoted_prediction"],
                                        "location": ev.get("location")}))
    if not sides:
        return _rule("R-11", "SKIP", [], note="no quoted gap predictions on the card")
    details, flagged = [], 0
    for name, s in sides:
        q, loc = s.get("quoted_prediction"), pc._location_kind(s.get("location"))
        item = {"side": name, "doi": s.get("doi"), "flag": True}
        if not q:
            item["result"] = "no quoted prediction"
        elif loc != "abstract":
            item["result"] = "unverified full-text quote (page or section), for the Critic's phase 1"
        else:
            ab = _abstract_for(str(s.get("doi") or ""), cache, abstracts, offline)
            if not ab:
                item["result"] = "abstract unavailable"
            else:
                ratio = quote_ratio(q, ab)
                item.update(ratio=round(ratio, 3), flag=ratio < GAP_QUOTE_MIN_RATIO,
                            result="matches the abstract" if ratio >= GAP_QUOTE_MIN_RATIO
                            else "does not match the abstract")
        flagged += item["flag"]
        details.append(item)
    return _rule("R-11", "FLAG" if flagged else "PASS", details)


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

def _forum_config() -> dict:
    try:
        return json.loads(AGENTS_FILE.read_text(encoding="utf-8")).get("forum_config", {}) or {}
    except (OSError, json.JSONDecodeError):
        return {}


def _promote(rule: dict, fail_rules: set) -> dict:
    """FLAG becomes a blocking FAIL only for promotable rules the researcher
    has listed in forum_config.precheck_fail_rules after the audit."""
    if rule["status"] == "FLAG" and rule["id"] in PROMOTABLE and rule["id"] in fail_rules:
        rule = {**rule, "status": "FAIL", "blocking": True}
    return rule


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def run_all(post_path, role: str, round_num: int, *, events=None, offline: bool = False,
            cache: dict | None = None, cache_path: Path | None = None,
            forum_dir: Path | None = None, card: dict | None = None,
            results: dict | None = None, gate: dict | None = None,
            gate_card: dict | None = None, results_by_round: dict | None = None,
            abstracts: dict | None = None, exists=None, write: bool = True) -> dict:
    """Run the rules that apply to the role on one post. FLAG mode. Returns
    {"post", "role", "round", "rules": [...], "counts": {...},
    "blocking_failed": bool} and, with write=True, merges it into
    knowledge/prechecks/R<NN>.json."""
    import prediction_card as pc
    post_path = Path(post_path)
    text = post_path.read_text(encoding="utf-8")
    forum_dir = forum_dir or post_path.parent
    events = load_trace(events) if events else []
    own_cache = cache is None
    cache = load_doi_cache(cache_path) if cache is None else cache
    if gate is None:
        try:
            gate = json.loads(ACTIVE_ARC_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            gate = {}
    cfg = _forum_config()
    fail_rules = set(cfg.get("precheck_fail_rules") or [])
    wanted = ROLE_RULES.get(role, ("R-04", "R-05", "R-10"))
    if card is None and role in ("literature_scout", "data_analyst"):
        card = pc.load_cards().get(int(round_num))
    if results is None and role == "data_analyst":
        results = pc.load_results(round_num)
    rules = []
    for rid in wanted:
        if rid == "R-01":
            rules.append(rule_r01(card, results))
        elif rid == "R-02":
            rules.append(rule_r02(text, results, events))
        elif rid == "R-04":
            rules.append(rule_r04(text, post_path.name, forum_dir))
        elif rid == "R-05":
            rules.append(rule_r05(text, cache, offline=offline))
        elif rid == "R-06":
            if gate_card is None:
                cards = pc.load_cards()
                start = int(gate.get("start_round") or round_num)
                gate_card = cards.get(start)
                if results_by_round is None:
                    results_by_round = {r: pc.load_results(r) for r in cards if start <= r <= round_num}
            rules.append(rule_r06(gate_card, results_by_round or {int(round_num): results or {}}, exists))
        elif rid == "R-07":
            rules.append(rule_r07(results, card, gate))
        elif rid == "R-08":
            rules.append(rule_r08(text, round_num))
        elif rid == "R-09":
            rules.append(rule_r09(text, events))
        elif rid == "R-10":
            rules.append(rule_r10(text, gate))
        elif rid == "R-11":
            if (cfg.get("stage2") or {}).get("gap_c_quotes", False) or not write:
                rules.append(rule_r11(card, cache, abstracts=abstracts if abstracts is not None
                                      else load_abstracts(), offline=offline))
    rules = [_promote(r, fail_rules) for r in rules]
    counts = {k: sum(1 for r in rules if r["status"] == k) for k in ("PASS", "FLAG", "FAIL", "SKIP")}
    out = {"post": post_path.name, "role": role, "round": int(round_num), "ts": _now_iso(),
           "mode": "FLAG" if not fail_rules else "FLAG with promoted rules",
           "rules": rules, "counts": counts,
           "blocking_failed": any(r["status"] == "FAIL" and r["blocking"] for r in rules)}
    if own_cache and not offline:
        save_doi_cache(cache, cache_path)
    if write:
        _merge_round_file(int(round_num), out)
    return out


def _merge_round_file(round_num: int, result: dict) -> Path:
    path = PRECHECKS_DIR / f"R{round_num:02d}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {"round": round_num, "posts": {}}
    data["posts"][result["post"]] = result
    data["rates"] = _rates(data["posts"].values())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _rates(post_results) -> dict:
    rates = {}
    for pr in post_results:
        for r in pr.get("rules") or []:
            d = rates.setdefault(r["id"], {"PASS": 0, "FLAG": 0, "FAIL": 0, "SKIP": 0, "items_flagged": 0})
            d[r["status"]] = d.get(r["status"], 0) + 1
            d["items_flagged"] += sum(1 for x in r.get("details") or [] if x.get("flag"))
    return rates


def flag_rates(prechecks_dir: Path | None = None) -> dict:
    """{rule: {round: counts}} over every knowledge/prechecks/R<NN>.json."""
    out = {}
    d = prechecks_dir or PRECHECKS_DIR
    for p in sorted(d.glob("R*.json")) if d.exists() else []:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for rid, counts in (data.get("rates") or {}).items():
            out.setdefault(rid, {})[int(data.get("round", 0))] = counts
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Precheck rulebook (Stage 2, FLAG mode)")
    sub = ap.add_subparsers(dest="cmd")
    d = sub.add_parser("dois", help="Print the DOIs extracted from a post")
    d.add_argument("post")
    r = sub.add_parser("run", help="Run the rules for one post")
    r.add_argument("post")
    r.add_argument("--role", required=True, choices=sorted(ROLE_RULES))
    r.add_argument("--round", type=int, required=True)
    r.add_argument("--offline", action="store_true", help="Resolve DOIs from the cache only")
    r.add_argument("--no-write", action="store_true")
    sub.add_parser("rates", help="Flag counts per rule and round")
    args = ap.parse_args()
    if args.cmd == "dois":
        print("\n".join(extract_dois(Path(args.post).read_text(encoding="utf-8"))))
    elif args.cmd == "run":
        out = run_all(args.post, args.role, args.round, offline=args.offline, write=not args.no_write)
        for rule in out["rules"]:
            print(f"  {rule['id']} {rule['name']:<20} {rule['status']}")
            for item in rule["details"]:
                if item.get("flag"):
                    print(f"      - {json.dumps(item, ensure_ascii=False)[:200]}")
    elif args.cmd == "rates":
        print(json.dumps(flag_rates(), indent=1))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
