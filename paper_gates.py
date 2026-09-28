#!/usr/bin/env python3
"""
Paper gates (v2.1, M07)
=======================
Deterministic checks that a drafted paper must pass before it is published.
Paper D shipped with four citation keys missing from its bibliography (the
PDF shows "(?)"), used "pre-registered" 23 times with no registry, and Paper
E points to a replication archive that does not exist. Nothing checked any
of it, and the drafting pipeline exited 0 either way.

Gates (blocking gates fail the draft closed, flag gates are only reported):

  G1  blocking  every \\cite, \\citet, \\citep ... key exists in the .bib file
  G2  blocking  nothing unresolved: undefined citations and references in the
                .log, missing entries in the .blg, "??" / "(?)" / a lone "?"
                in the pdftotext output, PLACEHOLDER or TODO, figure
                placeholder boxes, \\includegraphics targets that do not exist,
                TeX error lines in the .log, and (in the drafting pipeline) a
                missing .log or PDF, which means the compile did not finish
  G3  flag      blank cells in coefficient tables (an estimate without its
                uncertainty row, a blank N or fixed-effects indicator cell).
                A flag until it is tuned on the published papers.
  G4  blocking  overclaim lint: "pre-registered" without a registry id (OSF,
                AsPredicted, EGAP, AEA), and a replication-archive claim
                without a built and verified replication/arc_N package that
                the paper names
  G5  flag      bibliography entries that no forum post of the arc mentions
                must match Crossref or OpenAlex metadata (first-author
                surname and year). KCI is not queried (it needs an API key),
                so a Korean entry that neither index holds is only flagged.
  G6  blocking  leak lint (leak_lint.scan_text) over the tex, the bib, any
                \\input file next to the tex and the paper's figure scripts.
                Absolute home or volume paths and private patterns marked
                block: fail the gate. Every other hit is listed as a flag,
                following the FLAG-first rollout of the leak lint (M02).

run_all() returns {"ok", "gates": [{"id", "name", "blocking", "passed",
"details"}], "counts"}. ok is true when every blocking gate passed. The counts
(words, figures, tables, references) are what status reports should quote.

Usage:
    python3 paper_gates.py articles/2026-08-24_r27.tex            # gates on the files as they are
    python3 paper_gates.py articles/2026-08-24_r27.tex --recompile # compile a temporary copy first
    python3 paper_gates.py TEX --json --offline
Exit status: 0 all blocking gates pass, 2 a blocking gate failed, 1 error.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.parse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
REF_CACHE_FILE = LOGS_DIR / "paper_gates" / "ref_cache.json"
REPLICATION_DIR = BASE_DIR / "replication"

GATE_NAMES = {
    "G1": "citation keys resolve in the bibliography",
    "G2": "no unresolved citations, references or placeholders",
    "G3": "no blank cells in coefficient tables",
    "G4": "no overclaims (pre-registration, replication archive)",
    "G5": "new references match Crossref or OpenAlex metadata",
    "G6": "no absolute paths or private patterns",
}
BLOCKING = {"G1": True, "G2": True, "G3": False, "G4": True, "G5": False, "G6": True}

# Leak-lint pattern ids that fail G6. Everything else is a flag.
G6_BLOCKING_PATTERNS = {"home_path", "windows_home_path", "volume_path"}

# ---------------------------------------------------------------------------
# LaTeX helpers
# ---------------------------------------------------------------------------

CITE_RE = re.compile(
    r"\\(?:[Cc]ite(?:t|p|alt|alp|author|year|yearpar|num|text)?\*?|[Cc]itep\*?|[Cc]itet\*?|nocite)"
    r"\s*(?:\[[^\]]*\]\s*){0,2}\{([^}]*)\}")
INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
INPUT_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
FBOX_PLACEHOLDER_RE = re.compile(r"\\fbox\s*\{\s*\\parbox")
PLACEHOLDER_RE = re.compile(r"\b(?:PLACEHOLDER|TODO)\b")


def strip_comments(tex: str) -> str:
    """Drop LaTeX comments (an unescaped % to the end of the line)."""
    return re.sub(r"(?<!\\)%.*", "", tex)


def body_of(tex: str) -> str:
    """Text between \\begin{document} and \\end{document} (all of it if absent)."""
    m = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", tex, re.DOTALL)
    return m.group(1) if m else tex


def cite_keys(tex: str) -> list[str]:
    """Citation keys in order of first use, de-duplicated."""
    seen, out = set(), []
    for m in CITE_RE.finditer(strip_comments(tex)):
        for k in m.group(1).split(","):
            k = k.strip()
            if k and k != "*" and k not in seen:
                seen.add(k)
                out.append(k)
    return out


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def word_count(tex: str) -> int:
    """Rough prose word count of the document body (commands stripped)."""
    s = strip_comments(body_of(tex))
    s = re.sub(r"\\begin\{(?:verbatim|equation\*?|align\*?)\}.*?\\end\{(?:verbatim|equation\*?|align\*?)\}",
               " ", s, flags=re.DOTALL)
    s = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", s)
    s = re.sub(r"[{}\\$&_^~]", " ", s)
    return len(s.split())


def counts(tex: str, bib_entries: dict) -> dict:
    t = strip_comments(tex)
    return {
        "words": word_count(tex),
        "figures": len(re.findall(r"\\begin\{figure\*?\}", t)),
        "graphics": len(INCLUDEGRAPHICS_RE.findall(t)),
        "tables": len(re.findall(r"\\begin\{table\*?\}", t)),
        "cited_keys": len(cite_keys(tex)),
        "bib_entries": len(bib_entries),
    }


# ---------------------------------------------------------------------------
# BibTeX parsing (small, brace-aware, no dependency)
# ---------------------------------------------------------------------------

def _read_braced(text: str, i: int) -> tuple[str, int]:
    """text[i] is '{'. Returns (content, index after the matching '}')."""
    depth, j = 0, i
    while j < len(text):
        c = text[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j], j + 1
        j += 1
    return text[i + 1:], len(text)


def parse_bib(text: str) -> dict:
    """{key: {"type", "fields": {name: value}, "line"}} for every entry.
    @comment, @string and @preamble are skipped."""
    entries = {}
    for m in re.finditer(r"@(\w+)\s*\{", text or ""):
        etype = m.group(1).lower()
        if etype in ("comment", "string", "preamble"):
            continue
        body, _ = _read_braced(text, m.end() - 1)
        key, _, rest = body.partition(",")
        key = key.strip()
        if not key:
            continue
        fields, i = {}, 0
        while i < len(rest):
            fm = re.compile(r"\s*([A-Za-z][\w-]*)\s*=\s*").match(rest, i)
            if not fm:
                nxt = rest.find(",", i)
                if nxt < 0:
                    break
                i = nxt + 1
                continue
            name, i = fm.group(1).lower(), fm.end()
            if i < len(rest) and rest[i] == "{":
                val, i = _read_braced(rest, i)
            elif i < len(rest) and rest[i] == '"':
                j = i + 1
                while j < len(rest) and not (rest[j] == '"' and rest[j - 1] != "\\"):
                    j += 1
                val, i = rest[i + 1:j], j + 1
            else:
                vm = re.compile(r"[^,]*").match(rest, i)
                val, i = vm.group(0), vm.end()
            fields[name] = re.sub(r"\s+", " ", val).strip()
            comma = rest.find(",", i)
            i = comma + 1 if comma >= 0 else len(rest)
        entries[key] = {"type": etype, "fields": fields, "line": _line_of(text, m.start())}
    return entries


def _fold(s: str) -> str:
    s = re.sub(r"\\[a-zA-Z]+|[{}\\'\"`^~]", "", s or "")
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def first_author_surname(author_field: str) -> str | None:
    if not author_field:
        return None
    first = re.split(r"\s+and\s+", author_field.strip(), maxsplit=1)[0].strip().strip("{}")
    if "," in first:
        return first.split(",")[0].strip().strip("{}") or None
    parts = first.split()
    return parts[-1].strip("{}") if parts else None


def _entry_year(fields: dict) -> int | None:
    m = re.search(r"(1[89]\d\d|20\d\d)", fields.get("year", "") or fields.get("date", ""))
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# G1  citation keys
# ---------------------------------------------------------------------------

def _gate(gid: str, passed: bool, details: dict) -> dict:
    return {"id": gid, "name": GATE_NAMES[gid], "blocking": BLOCKING[gid], "passed": bool(passed),
            "details": details}


def gate_g1(tex: str, bib_entries: dict | None) -> dict:
    keys = cite_keys(tex)
    if bib_entries is None:
        return _gate("G1", not keys, {"error": "bibliography file missing", "cited": len(keys),
                                     "missing": sorted(keys)})
    missing = sorted(k for k in keys if k not in bib_entries)
    return _gate("G1", not missing, {"cited": len(keys), "missing": missing})


# ---------------------------------------------------------------------------
# G2  unresolved
# ---------------------------------------------------------------------------

LOG_CITE_RE = re.compile(r"Citation [`'\"]([^'`\"]+)['\"] on page \S+ undefined")
LOG_REF_RE = re.compile(r"Reference [`'\"]([^'`\"]+)['\"] on page \S+ undefined")
BLG_MISSING_RE = re.compile(r"I didn't find a database entry for [\"']([^\"']+)[\"']")
BLG_NO_BIB_RE = re.compile(r"I couldn't open database file (\S+)")
# LaTeX error lines in the .log. A line that starts with "!" is a TeX error
# (an aborted run ends with "! Emergency stop." or "!  ==> Fatal error").
LOG_ERROR_RE = re.compile(r"^!.*$|^.*(?:Emergency stop|No pages of output|Fatal error occurred).*$",
                          re.MULTILINE)
PDF_SHAPES = [
    ("double_question", re.compile(r"\?\?")),
    ("paren_question", re.compile(r"\(\?\)")),
    ("question_before_name", re.compile(r"\(\?(?=[A-Z])")),
    # A lone "?" token: natbib prints it for an undefined \citet or inside a
    # citation list. A question mark that ends a word is ordinary prose.
    ("lone_question", re.compile(r"(?<![^\s(\[;,])\?(?=[\s,;)\].]|$)", re.MULTILINE)),
]


def _context(text: str, start: int, end: int, width: int = 60) -> str:
    return re.sub(r"\s+", " ", text[max(0, start - width):end + width]).strip()


def gate_g2(tex: str, *, tex_dir: Path | None = None, pdf_text: str | None = None,
            log_text: str | None = None, blg_text: str | None = None,
            compiled: bool = False, pdf_exists: bool | None = None) -> dict:
    """compiled=True is the drafting pipeline's case, where the paper was just
    compiled. Then a missing .log or PDF fails the gate (the compile did not
    run or aborted), so a draft never passes on its .tex alone. TeX error
    lines in the .log fail the gate whenever a .log is given."""
    d: dict = {"sources": [], "log_undefined_citations": [], "log_undefined_references": [],
               "blg_missing_entries": [], "pdf_hits": [], "placeholders": [], "missing_graphics": [],
               "log_errors": [], "compile_problems": []}
    if compiled:
        if log_text is None:
            d["compile_problems"].append("no .log file: the paper did not compile")
        if not pdf_exists:
            d["compile_problems"].append("no PDF was produced")
    if log_text is not None:
        d["sources"].append("log")
        d["log_undefined_citations"] = sorted(set(LOG_CITE_RE.findall(log_text)))
        d["log_undefined_references"] = sorted(set(LOG_REF_RE.findall(log_text)))
        errors = []
        for m in LOG_ERROR_RE.finditer(log_text):
            line = m.group(0).strip()
            if line and line not in errors:
                errors.append(line[:200])
        d["log_errors"] = errors[:20]
    if blg_text is not None:
        d["sources"].append("blg")
        d["blg_missing_entries"] = sorted(set(BLG_MISSING_RE.findall(blg_text)))
        d["blg_missing_database"] = sorted(set(BLG_NO_BIB_RE.findall(blg_text)))
    if pdf_text is not None:
        d["sources"].append("pdftotext")
        seen = set()
        for shape, rx in PDF_SHAPES:
            for m in rx.finditer(pdf_text):
                if m.start() in seen or m.start() - 1 in seen:
                    continue   # one hit per marker ("??" also matches the lone-? shape)
                seen.update((m.start(), m.end() - 1))
                d["pdf_hits"].append({"shape": shape, "line": _line_of(pdf_text, m.start()),
                                      "context": _context(pdf_text, m.start(), m.end())})
        for m in PLACEHOLDER_RE.finditer(pdf_text):
            d["placeholders"].append({"where": "pdf", "line": _line_of(pdf_text, m.start()),
                                      "text": m.group(0)})
    t = strip_comments(tex)
    d["sources"].append("tex")
    for m in PLACEHOLDER_RE.finditer(t):
        d["placeholders"].append({"where": "tex", "line": _line_of(t, m.start()), "text": m.group(0)})
    for m in FBOX_PLACEHOLDER_RE.finditer(t):
        d["placeholders"].append({"where": "tex", "line": _line_of(t, m.start()),
                                  "text": "figure placeholder box (\\fbox{\\parbox...})"})
    if tex_dir is not None:
        for m in INCLUDEGRAPHICS_RE.finditer(t):
            target = m.group(1).strip()
            p = Path(tex_dir) / target
            cands = [p] if p.suffix else [p.with_suffix(s) for s in (".pdf", ".png", ".jpg", ".jpeg")]
            if not any(c.exists() for c in cands):
                d["missing_graphics"].append({"line": _line_of(t, m.start()), "target": target})
    failed = any(d[k] for k in ("log_undefined_citations", "log_undefined_references",
                                 "blg_missing_entries", "pdf_hits", "placeholders", "missing_graphics",
                                 "log_errors", "compile_problems"))
    failed = failed or bool(d.get("blg_missing_database"))
    return _gate("G2", not failed, d)


# ---------------------------------------------------------------------------
# G3  blank cells in coefficient tables (flag)
# ---------------------------------------------------------------------------

RULE_RE = re.compile(r"\\(?:toprule|midrule|bottomrule|hline|cmidrule(?:\([^)]*\))?\{[^}]*\}|addlinespace"
                     r"(?:\[[^\]]*\])?|cline\{[^}]*\})")
NUM_RE = re.compile(r"^\$?\s*[-\u2212+]?\s*\d[\d,]*(?:\.\d+)?\s*(?:\^\{?\**\}?|\^\{\*+\}|\*+)?\s*\$?$")
UNC_RE = re.compile(r"^\$?\s*[(\[]\s*[-\u2212+]?\s*[\d.,]+\s*[)\]]\s*\$?$")
N_ROW_RE = re.compile(r"^(?:N\b|n\b|Observations|Obs\.|Num\.?\s*obs|Number of)", re.IGNORECASE)
YESNO_RE = re.compile(r"^(?:Yes|No|\\checkmark|X)$", re.IGNORECASE)


def _clean_cell(c: str) -> str:
    c = re.sub(r"\\multicolumn\{\d+\}\{[^}]*\}\{(.*)\}", r"\1", c.strip())
    c = re.sub(r"\\(?:textbf|textit|emph|mathbf)\{([^}]*)\}", r"\1", c)
    c = c.replace("$-$", "-").replace("\\,", "")
    return c.strip()


def _tabulars(tex: str):
    for m in re.finditer(r"\\begin\{tabular\*?\}(?:\{[^}]*\})?\s*\{", tex):
        _, spec_end = _read_braced(tex, m.end() - 1)
        end = tex.find("\\end{tabular", spec_end)
        if end < 0:
            continue
        yield spec_end, tex[spec_end:end]


def gate_g3(tex: str) -> dict:
    """Blank cells in coefficient tables. A table counts as a coefficient
    table when some cell is an uncertainty cell like (0.54) or [0.15]. Within
    a rule-delimited section that has uncertainty rows, every numeric
    estimate needs an uncertainty cell right below it. N rows and Yes/No
    indicator rows must have no blank cell anywhere."""
    t = strip_comments(tex)
    findings = []
    section_rule = re.compile(r"\\(?:toprule|midrule|bottomrule|hline)")
    for offset, body in _tabulars(t):
        rows, section = [], 0
        for raw in re.split(r"\\\\(?:\[[^\]]*\])?", body):
            if section_rule.search(raw):
                section += 1
            txt = RULE_RE.sub("", raw).strip()
            if not txt or ("\\multicolumn" in txt and "&" not in txt):
                continue
            line_no = _line_of(t, offset + body.find(raw))
            cells = [_clean_cell(c) for c in re.split(r"(?<!\\)&", txt)]
            rows.append((line_no, section, cells))
        if not any(UNC_RE.match(c) for _, _, cells in rows for c in cells[1:]):
            continue
        ncol = max(len(c) for _, _, c in rows)
        unc_sections = {sec for _, sec, cells in rows if any(UNC_RE.match(c) for c in cells[1:])}
        for i, (line_no, sec, cells) in enumerate(rows):
            label = cells[0] if cells else ""
            data = cells[1:] + [""] * (ncol - len(cells))
            if N_ROW_RE.match(label):
                if any(not c for c in data):
                    findings.append({"line": line_no, "row": label[:60], "kind": "blank N cell"})
                continue
            if any(YESNO_RE.match(c) for c in data):
                if any(not c for c in data):
                    findings.append({"line": line_no, "row": label[:60], "kind": "blank indicator cell"})
                continue
            if sec not in unc_sections or not label or UNC_RE.match(label):
                continue
            nxt = rows[i + 1] if i + 1 < len(rows) else None
            below_row = nxt[2][1:] if nxt and nxt[1] == sec and nxt[2] and not nxt[2][0] else []
            for j, c in enumerate(data):
                if not c or not NUM_RE.match(c):
                    continue
                below = below_row[j] if j < len(below_row) else ""
                if not UNC_RE.match(below):
                    findings.append({"line": line_no, "row": label[:60], "column": j + 1,
                                     "kind": "estimate without an uncertainty cell"})
    return _gate("G3", not findings, {"blank_cells": findings})


# ---------------------------------------------------------------------------
# G4  overclaims
# ---------------------------------------------------------------------------

PREREG_RE = re.compile(r"\bpre-?registered\b", re.IGNORECASE)
REGISTRY_RE = re.compile(
    r"osf\.io/[A-Za-z0-9]{4,}|10\.17605/OSF\.IO/[A-Za-z0-9]+|aspredicted\.org/[\w/.-]+"
    r"|AsPredicted\s*(?:\\?#|No\.?|number)\s*\d+|egap\.org/registration/\d+"
    r"|EGAP\s*(?:ID|registration(?:\s+ID)?)?\s*:?\s*20\d{4}[A-Za-z]{0,3}\b|AEARCTR-\d{7}",
    re.IGNORECASE)
REPLICATION_CLAIM_RE = re.compile(
    r"\breplication\s+(?:archive|package|materials?|files?|code|data(?:set)?|repository|dictionary)\b"
    r"|\b(?:available|deposited|released)\s+(?:in|at|from|on)\s+(?:the\s+|our\s+|a\s+)?(?:project'?s\s+)?"
    r"(?:public\s+)?(?:repository|archive|GitHub|Dataverse)\b",
    re.IGNORECASE)
ARC_PACKAGE_RE = re.compile(r"replication/arc(?:\\_|_)(\d+)")


def replication_status(arc_dir: Path | None) -> dict:
    """What a replication claim can rest on: the package's MANIFEST.json."""
    if arc_dir is None:
        return {"exists": False, "reason": "no replication package given"}
    manifest = Path(arc_dir) / "MANIFEST.json"
    if not manifest.exists():
        return {"exists": False, "reason": f"{Path(arc_dir).name}/MANIFEST.json missing"}
    try:
        m = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"exists": False, "reason": f"MANIFEST.json unreadable ({type(e).__name__})"}
    verify = m.get("verify") or {}
    return {"exists": True, "arc": m.get("arc"), "build_ok": bool(m.get("build", {}).get("ok")),
            "verify_passed": verify.get("passed") is True}


def gate_g4(tex: str, *, replication: dict | None = None, arc: int | str | None = None) -> dict:
    t = strip_comments(body_of(tex))
    prereg = [{"line": _line_of(t, m.start()), "context": _context(t, m.start(), m.end())}
              for m in PREREG_RE.finditer(t)]
    registry_ids = sorted(set(m.group(0) for m in REGISTRY_RE.finditer(t)))
    prereg_fail = bool(prereg) and not registry_ids

    claims = [{"line": _line_of(t, m.start()), "context": _context(t, m.start(), m.end())}
              for m in REPLICATION_CLAIM_RE.finditer(t)]
    named = sorted(set(ARC_PACKAGE_RE.findall(t)))
    rep = replication or {"exists": False, "reason": "no replication package given"}
    problems = []
    if claims:
        if not rep.get("exists"):
            problems.append(rep.get("reason") or "no replication package")
        else:
            if not rep.get("build_ok"):
                problems.append("replication package build did not pass")
            if not rep.get("verify_passed"):
                problems.append("replication package verify has not passed")
        if not named:
            problems.append("the paper does not name its package as replication/arc_N")
        elif arc is not None and str(arc) not in named:
            problems.append(f"the paper names replication/arc_{', arc_'.join(named)}, not arc_{arc}")
    details = {
        "preregistered_uses": len(prereg), "registry_ids": registry_ids,
        "preregistered_without_registry": prereg if prereg_fail else [],
        "replication_claims": len(claims), "replication_packages_named": named,
        "replication_problems": problems,
        "replication_claims_unbacked": claims if problems else [],
    }
    return _gate("G4", not prereg_fail and not problems, details)


# ---------------------------------------------------------------------------
# G5  new references against Crossref / OpenAlex (flag)
# ---------------------------------------------------------------------------

def _http_get_json(url: str, timeout: int = 15):
    import requests  # noqa: E402
    mail = os.environ.get("KNA_MAILTO")
    headers = {"User-Agent": "kna-research-agents/2.1" + (f" (mailto:{mail})" if mail else "")}
    r = requests.get(url, headers=headers, timeout=timeout)
    if r.status_code != 200:
        return None
    return r.json()


def _title_sim(a: str, b: str) -> float:
    a, b = re.sub(r"[^a-z0-9 ]", " ", _fold(a)), re.sub(r"[^a-z0-9 ]", " ", _fold(b))
    try:
        from rapidfuzz import fuzz
        return fuzz.token_set_ratio(a, b) / 100.0
    except ImportError:
        import difflib
        return difflib.SequenceMatcher(None, " ".join(a.split()), " ".join(b.split())).ratio()


def _search_records(title: str, surname: str | None, year: int | None) -> list[dict]:
    """Crossref bibliographic query, then OpenAlex title search."""
    out = []
    q = " ".join(x for x in (title, surname or "", str(year or "")) if x)
    mail = os.environ.get("KNA_MAILTO")
    url = ("https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(q)
           + (f"&mailto={urllib.parse.quote(mail)}" if mail else ""))
    js = _http_get_json(url)
    for it in ((js or {}).get("message") or {}).get("items") or []:
        years = set()
        for k in ("issued", "published-print", "published-online"):
            parts = (it.get(k) or {}).get("date-parts") or [[None]]
            if parts and parts[0] and parts[0][0]:
                years.add(int(parts[0][0]))
        au = it.get("author") or []
        out.append({"source": "crossref", "title": (it.get("title") or [""])[0], "years": sorted(years),
                    "first_author": (au[0].get("family") or au[0].get("name")) if au else None,
                    "authors": [a.get("family") or a.get("name") for a in au[:12]],
                    "doi": it.get("DOI")})
    time.sleep(0.2)
    url = ("https://api.openalex.org/works?per-page=3&search=" + urllib.parse.quote(title)
           + (f"&mailto={urllib.parse.quote(mail)}" if mail else ""))
    js = _http_get_json(url)
    for w in (js or {}).get("results") or []:
        names = [(a.get("author") or {}).get("display_name") or "" for a in (w.get("authorships") or [])[:12]]
        auth = names[0] if names else None
        out.append({"source": "openalex", "title": w.get("title") or "",
                    "years": [w["publication_year"]] if w.get("publication_year") else [],
                    "first_author": auth.split()[-1] if auth else None,
                    "authors": [n.split()[-1] for n in names if n.split()], "doi": w.get("doi")})
    time.sleep(0.2)
    return out


def _author_match(bib_surname: str | None, rec_surname: str | None) -> bool:
    if not bib_surname or not rec_surname:
        return False
    a, b = re.sub(r"[^a-z]", "", _fold(bib_surname)), re.sub(r"[^a-z]", "", _fold(rec_surname))
    return bool(a) and bool(b) and (a == b or a in b or b in a)


def _year_match(year: int | None, years: list) -> bool:
    return year is not None and any(abs(int(y) - year) <= 1 for y in years or [])


def _status(author_ok: bool, year_ok: bool) -> str:
    """verified, or which part failed. author_unconfirmed covers records whose
    author field holds an affiliation, a suffix or a non-Latin name that a
    romanized bib surname cannot match."""
    if author_ok and year_ok:
        return "verified"
    if author_ok:
        return "year_mismatch"
    if year_ok:
        return "author_unconfirmed"
    return "mismatch"


def check_reference(key: str, entry: dict, cache: dict, *, offline: bool = False) -> dict:
    f = entry.get("fields", {})
    surname = first_author_surname(f.get("author", "") or f.get("editor", ""))
    year = _entry_year(f)
    title = re.sub(r"[{}]", "", f.get("title", ""))
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", f.get("doi", "").strip(), flags=re.I)
    out = {"key": key, "surname": surname, "year": year, "doi": doi or None}
    if doi:
        import prechecks  # noqa: E402  (Crossref, then OpenAlex, cached by DOI)
        rec = prechecks.resolve_doi(doi, cache, offline=offline)
        if rec.get("found") is None:
            out.update(status="unchecked", reason=rec.get("source"))
        elif not rec.get("found"):
            out.update(status="not_found", reason="DOI resolves on neither Crossref nor OpenAlex")
        else:
            ok_a = _author_match(surname, rec.get("first_author"))
            ok_y = _year_match(year, rec.get("years") or [])
            out.update(status=_status(ok_a, ok_y), source=rec.get("source"),
                       found_author=rec.get("first_author"), found_years=rec.get("years"))
        return out
    if not title:
        out.update(status="unchecked", reason="no title and no DOI")
        return out
    ck = f"q:{_fold(title)[:120]}|{_fold(surname or '')}|{year}"
    if ck in cache:
        recs = cache[ck]
    elif offline:
        out.update(status="unchecked", reason="offline")
        return out
    else:
        try:
            recs = _search_records(title, surname, year)
        except Exception as e:  # network trouble is not evidence against the entry
            out.update(status="unchecked", reason=f"error: {type(e).__name__}")
            return out
        cache[ck] = recs
    best = None
    for r in recs:
        sim = _title_sim(title, r.get("title") or "")
        if sim >= 0.9 and (best is None or sim > best[0]):
            best = (sim, r)
    if best is None:
        out.update(status="not_found", reason="no Crossref or OpenAlex record with a matching title "
                                              "(KCI not queried)")
        return out
    r = best[1]
    ok_a = any(_author_match(surname, a) for a in (r.get("authors") or [r.get("first_author")]))
    ok_y = _year_match(year, r.get("years") or [])
    out.update(status=_status(ok_a, ok_y), source=r.get("source"),
               found_author=r.get("first_author"), found_years=r.get("years"), found_doi=r.get("doi"))
    return out


def gate_g5(bib_entries: dict | None, *, forum_text: str | None = None, cache: dict | None = None,
            offline: bool = False, enabled: bool = True) -> dict:
    if bib_entries is None:
        return _gate("G5", False, {"error": "bibliography file missing"})
    if not enabled:
        return _gate("G5", True, {"skipped": True})
    known = (forum_text or "").lower()
    cache = {} if cache is None else cache
    results, known_n = [], 0
    for key, e in bib_entries.items():
        doi = e["fields"].get("doi", "").strip().lower()
        if forum_text is not None and (key.lower() in known or (doi and doi in known)):
            known_n += 1
            continue
        results.append(check_reference(key, e, cache, offline=offline))
    bad = [r for r in results if r["status"] not in ("verified", "unchecked")]
    unchecked = [r for r in results if r["status"] == "unchecked"]
    # A reference that could not be checked (offline, network error) is not
    # counted as verified: the flag gate stays raised until it is.
    return _gate("G5", not bad and not unchecked, {
        "entries": len(bib_entries), "mentioned_in_forum": known_n, "checked": len(results),
        "verified": sum(r["status"] == "verified" for r in results),
        "unchecked": len(unchecked), "unchecked_keys": [r["key"] for r in unchecked],
        "flagged": bad, "forum_context": forum_text is not None})


# ---------------------------------------------------------------------------
# G6  leak lint
# ---------------------------------------------------------------------------

def gate_g6(texts: dict) -> dict:
    """texts: {display name: text}."""
    import leak_lint  # noqa: E402
    private = leak_lint.load_private_patterns()
    blocking, flags = [], []
    for name, text in texts.items():
        for h in leak_lint.scan_text(text or "", path=name, private=private):
            item = {"path": name, "line": h["line"], "pattern_id": h["pattern_id"]}
            if h["source"] == "generic":
                item["match"] = h["match"]   # generic hits name no private system
            if h["pattern_id"] in G6_BLOCKING_PATTERNS or h.get("block"):
                blocking.append(item)
            else:
                flags.append(item)
    return _gate("G6", not blocking, {"scanned": sorted(texts), "blocking_hits": blocking,
                                      "flag_hits": flags})


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def pdf_text(pdf_path: Path) -> str | None:
    exe = shutil.which("pdftotext")
    if not exe or not Path(pdf_path).exists():
        return None
    try:
        r = subprocess.run([exe, "-enc", "UTF-8", str(pdf_path), "-"],
                           capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def _read(p: Path | None) -> str | None:
    if p is None:
        return None
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def load_ref_cache(path: Path | None = None) -> dict:
    try:
        return json.loads(Path(path or REF_CACHE_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_ref_cache(cache: dict, path: Path | None = None) -> None:
    p = Path(path or REF_CACHE_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def _paper_texts(tex_path: Path, tex: str, bib_path: Path | None, bib_text: str | None) -> dict:
    texts = {tex_path.name: tex}
    if bib_text is not None and bib_path is not None:
        texts[Path(bib_path).name] = bib_text
    for m in INPUT_RE.finditer(strip_comments(tex)):
        name = m.group(1).strip()
        p = tex_path.parent / (name if name.endswith(".tex") else name + ".tex")
        t = _read(p)
        if t is not None:
            texts[p.name] = t
    fig_dir = tex_path.parent / "figures" / tex_path.stem
    if fig_dir.is_dir():
        for r in sorted(fig_dir.glob("*.R")):
            t = _read(r)
            if t is not None:
                texts[f"figures/{tex_path.stem}/{r.name}"] = t
    return texts


def run_all(tex_path, bib_path, pdf_path=None, *, log_path=None, blg_path=None,
            forum_text: str | None = None, replication_dir=None, arc=None,
            cache: dict | None = None, cache_path=None, offline: bool = False,
            check_references: bool = True, compiled: bool = False) -> dict:
    """Run every gate on one paper. log_path and blg_path default to the
    .log and .blg next to the tex (read before the aux cleanup). forum_text
    is the arc's forum posts joined, used by G5 to find new references.
    replication_dir is the replication/arc_N package G4 checks claims against.
    G5 uses the network unless offline=True, and answers are cached. compiled=True
    (the drafting pipeline) makes a missing .log or PDF fail G2."""
    tex_path = Path(tex_path)
    tex = tex_path.read_text(encoding="utf-8", errors="replace")
    bib_path = Path(bib_path) if bib_path else None
    bib_text = _read(bib_path) if bib_path and bib_path.exists() else None
    bib_entries = parse_bib(bib_text) if bib_text is not None else None
    log_path = Path(log_path) if log_path else tex_path.with_suffix(".log")
    blg_path = Path(blg_path) if blg_path else tex_path.with_suffix(".blg")
    ptext = pdf_text(Path(pdf_path)) if pdf_path else None
    own_cache = cache is None
    if own_cache:
        cache = load_ref_cache(cache_path)
    rep = replication_status(Path(replication_dir) if replication_dir else None)

    gates = [
        gate_g1(tex, bib_entries),
        gate_g2(tex, tex_dir=tex_path.parent, pdf_text=ptext,
                log_text=_read(log_path) if log_path.exists() else None,
                blg_text=_read(blg_path) if blg_path.exists() else None,
                compiled=compiled, pdf_exists=bool(pdf_path) and Path(pdf_path).exists()),
        gate_g3(tex),
        gate_g4(tex, replication=rep, arc=arc),
        gate_g5(bib_entries, forum_text=forum_text, cache=cache, offline=offline,
                enabled=check_references),
        gate_g6(_paper_texts(tex_path, tex, bib_path, bib_text)),
    ]
    if own_cache and check_references and not offline:
        try:
            save_ref_cache(cache, cache_path)
        except OSError:
            pass
    return {
        "ok": all(g["passed"] for g in gates if g["blocking"]),
        "gates": gates,
        "failed_blocking": [g["id"] for g in gates if g["blocking"] and not g["passed"]],
        "flags": [g["id"] for g in gates if not g["blocking"] and not g["passed"]],
        "counts": counts(tex, bib_entries or {}),
        "tex": tex_path.name,
        "pdf_checked": ptext is not None,
        "generated": datetime.now().isoformat(timespec="seconds"),
    }


def failing_items(report: dict, limit: int = 40) -> list[str]:
    """One line per failing blocking-gate item, for the fix-pass prompt."""
    lines = []
    for g in report.get("gates", []):
        if not g["blocking"] or g["passed"]:
            continue
        d = g["details"]
        if g["id"] == "G1":
            for k in d.get("missing", []):
                lines.append(f"G1: \\cite key '{k}' has no entry in the .bib file. Add a correct entry for a "
                             f"work the forum posts cite, or remove the citation and its claim.")
        elif g["id"] == "G2":
            for k in d.get("log_undefined_citations", []) + d.get("blg_missing_entries", []):
                lines.append(f"G2: citation '{k}' is undefined in the compiled PDF.")
            for k in d.get("log_undefined_references", []):
                lines.append(f"G2: \\ref label '{k}' is undefined (renders as ??).")
            for h in d.get("pdf_hits", [])[:10]:
                lines.append(f"G2: unresolved marker in the PDF ({h['shape']}): ...{h['context']}...")
            for p in d.get("placeholders", []):
                lines.append(f"G2: placeholder in the {p['where']} at line {p['line']}: {p['text']}")
            for m in d.get("missing_graphics", []):
                lines.append(f"G2: \\includegraphics target '{m['target']}' does not exist (line {m['line']}).")
            for b in d.get("blg_missing_database", []):
                lines.append(f"G2: bibtex could not open the database {b}.")
            for c in d.get("compile_problems", []):
                lines.append(f"G2: {c}. Make the paper compile (fix the LaTeX errors listed).")
            for e in d.get("log_errors", [])[:10]:
                lines.append(f"G2: LaTeX error in the compile log: {e}")
        elif g["id"] == "G4":
            for p in d.get("preregistered_without_registry", []):
                lines.append(f"G4: 'pre-registered' at line {p['line']} with no registry id in the paper. "
                             "Say 'declared before estimation in the forum record' or similar, "
                             "never 'pre-registered'.")
            if d.get("replication_problems"):
                why = "; ".join(d["replication_problems"])
                for c in d.get("replication_claims_unbacked", [])[:10]:
                    lines.append(f"G4: replication-archive claim at line {c['line']} is not backed ({why}). "
                                 f"Remove the claim: ...{c['context']}...")
        elif g["id"] == "G6":
            for h in d.get("blocking_hits", []):
                lines.append(f"G6: {h['pattern_id']} in {h['path']} line {h['line']}. Replace absolute paths "
                             "with $KBL_DATA or a repository-relative path.")
    return lines[:limit]


def recompile_copy(tex_path: Path, bib_path: Path | None, out_dir: Path) -> dict:
    """Compile a copy of a paper in out_dir (xelatex, bibtex, xelatex x2) and
    return the paths of the copy's tex, pdf, log and blg. The original files
    are only read. Figures under figures/<stem>/ and apsr.bst are copied."""
    tex_path = Path(tex_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tex_path, out_dir / tex_path.name)
    if bib_path and Path(bib_path).exists():
        shutil.copy2(bib_path, out_dir / Path(bib_path).name)
    for extra in ("apsr.bst",):
        src = tex_path.parent / extra
        if src.exists():
            shutil.copy2(src, out_dir / extra)
    fig = tex_path.parent / "figures" / tex_path.stem
    if fig.is_dir():
        shutil.copytree(fig, out_dir / "figures" / tex_path.stem, dirs_exist_ok=True)
    # Older papers point at flat figures/<name>.pdf files; copy every target that exists.
    for m in INCLUDEGRAPHICS_RE.finditer(strip_comments(tex_path.read_text(encoding="utf-8", errors="replace"))):
        rel = m.group(1).strip()
        src = tex_path.parent / rel
        if src.is_file() and not (out_dir / rel).exists():
            (out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out_dir / rel)
    xelatex = shutil.which("xelatex") or str(Path.home() / "Library/TinyTeX/bin/universal-darwin/xelatex")
    bibtex = shutil.which("bibtex") or str(Path.home() / "Library/TinyTeX/bin/universal-darwin/bibtex")
    steps = [[xelatex, "-interaction=nonstopmode", tex_path.name], [bibtex, tex_path.stem],
             [xelatex, "-interaction=nonstopmode", tex_path.name],
             [xelatex, "-interaction=nonstopmode", tex_path.name]]
    for cmd in steps:
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=str(out_dir))
        except (OSError, subprocess.TimeoutExpired):
            break
    stem = out_dir / tex_path.stem
    return {"tex": out_dir / tex_path.name, "pdf": stem.with_suffix(".pdf"),
            "log": stem.with_suffix(".log"), "blg": stem.with_suffix(".blg")}


def default_bib(tex_path: Path) -> Path | None:
    """The .bib named by \\bibliography{...}, next to the tex."""
    tex = Path(tex_path).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\\bibliography\{([^}]+)\}", strip_comments(tex))
    if not m:
        return None
    name = m.group(1).split(",")[0].strip()
    return Path(tex_path).parent / (name if name.endswith(".bib") else name + ".bib")


def summary_line(report: dict) -> str:
    parts = []
    for g in report["gates"]:
        mark = "pass" if g["passed"] else ("FAIL" if g["blocking"] else "flag")
        parts.append(f"{g['id']} {mark}")
    c = report["counts"]
    return (" | ".join(parts) + f"  ({c['words']} words, {c['figures']} figures, {c['tables']} tables, "
            f"{c['bib_entries']} bib entries)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the M07 paper gates on one paper.")
    ap.add_argument("tex")
    ap.add_argument("--bib", default=None, help="default: the file named by \\bibliography{}")
    ap.add_argument("--pdf", default=None, help="default: the .pdf next to the tex")
    ap.add_argument("--recompile", action="store_true",
                    help="compile a temporary copy first so G2 can read the .log and .blg")
    ap.add_argument("--replication-dir", default=None)
    ap.add_argument("--arc", default=None)
    ap.add_argument("--offline", action="store_true", help="G5 answers from the cache only")
    ap.add_argument("--no-references", action="store_true", help="skip G5")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    tex = Path(args.tex)
    if not tex.exists():
        print(f"paper_gates: {tex} not found", file=sys.stderr)
        return 1
    bib = Path(args.bib) if args.bib else default_bib(tex)
    kw = dict(replication_dir=args.replication_dir, arc=args.arc, offline=args.offline,
              check_references=not args.no_references)
    if args.recompile:
        with tempfile.TemporaryDirectory(prefix="kna_gates_") as td:
            paths = recompile_copy(tex, bib, Path(td))
            # The copy was just compiled, so a missing .log or PDF fails G2.
            report = run_all(paths["tex"], Path(td) / bib.name if bib else None, paths["pdf"],
                             log_path=paths["log"], blg_path=paths["blg"], compiled=True, **kw)
    else:
        pdf = Path(args.pdf) if args.pdf else tex.with_suffix(".pdf")
        report = run_all(tex, bib, pdf if pdf.exists() else None, **kw)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        print(f"{tex.name}: {summary_line(report)}")
        for line in failing_items(report):
            print(f"  - {line}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
