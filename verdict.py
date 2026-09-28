#!/usr/bin/env python3
"""The Critic's verdict of record (M10a) and the scripted checks that decide
whether a pursue binds (M10b, Stage 2).

Stage 1. The Critic run passes knowledge/schemas/critic_verdict.json through
--json-schema, so the run returns its verdict as structured output. That
structured verdict is the verdict of record. The YAML scoring block stays in
the post for the site. record() reconciles the two, writes one row per round
to knowledge/verdicts.jsonl, and refuses a second write for the same round.
A disagreement on the verdict field itself makes the effective verdict
revise. Posts 001-090 predate the schema, and verdict_of_record() reads them
from the LAST ```yaml scoring block of the Critic post, falling back to the
old first-hit regex only when a post has no scoring block.

Stage 2 (forum_config.stage2.binding_checks). binding_checks() computes, from
committed prediction cards and results files and never from the Critic,
whether the gate's falsifier was tested, how many arc rounds ran a new kill
test on the headline claim, whether every reported null had a pre-committed
equivalence bound, and whether the headline was prespecified. A pursue that
fails any of them is recorded as revise, with the reasons.

Usage:
    python3 verdict.py --write-schema     # regenerate critic_verdict.json from taxonomy constants
    python3 verdict.py show --round N     # verdict of record for one round
    python3 verdict.py distribution --since R [--arc-start A]
"""

import argparse
import ast
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
LOGS_DIR = BASE_DIR / "logs"
WORKSPACE_DIR = BASE_DIR / "workspace"
AGENTS_FILE = BASE_DIR / "agents.json"
VERDICTS_FILE = KNOWLEDGE_DIR / "verdicts.jsonl"
SHIFTS_FILE = KNOWLEDGE_DIR / "verdict_shifts.jsonl"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
PRECHECKS_DIR = KNOWLEDGE_DIR / "prechecks"

SCHEMA_PATH = "knowledge/schemas/critic_verdict.json"
SCHEMA_ID = "critic_verdict.v1"
SCHEMA_FILE = Path(__file__).resolve().parent / SCHEMA_PATH   # not moved by tests

VERDICTS = ("pursue", "revise", "archive")
SCORE_FIELDS = ("research_novelty", "empirical_rigor", "theoretical_connection", "actionability")
LABEL_FIELDS = ("opportunity_pattern", "method_paradigm", "operation")
FALSIFIER_VALUES = ("yes", "no", "not_applicable")
PRIOR_STATUS = ("supported", "overturned", "inconclusive", "not_tested")
HEADLINE_BASIS = ("prespecified", "exploratory")
REQUIRED_FIELDS = (*SCORE_FIELDS, *LABEL_FIELDS, "falsifier_tested", "prior_status",
                   "headline_basis", "verdict", "one_line")
COMPARED_FIELDS = (*SCORE_FIELDS, *LABEL_FIELDS, "falsifier_tested", "prior_status",
                   "headline_basis", "verdict")
ONE_LINE_MAX = 400
DISTRIBUTION_FLAG_SHARE = 0.70

YAML_BLOCK_RE = re.compile(r"```[ \t]*(?:yaml|yml)[ \t]*\n(.*?)\n[ \t]*```", re.DOTALL | re.IGNORECASE)
YAML_KEY_RE = re.compile(r"^(\s*)([A-Za-z_][\w-]*)\s*:\s*(.*)$")
LEGACY_VERDICT_RE = re.compile(r"verdict:\s*(pursue|revise|archive)")
LEGACY_FALSIFIER_RE = re.compile(r"falsifier_tested:\s*([A-Za-z_]+)")
LEGACY_ONE_LINE_RE = re.compile(r'one_line:\s*"([^"]+)"')


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------

def build_schema() -> dict:
    """The verdict schema, with the label enums taken from taxonomy_monitor
    so the two cannot drift (a test compares this with the file on disk)."""
    import taxonomy_monitor as tm
    score = {"type": "integer", "minimum": 0, "maximum": 4}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "Critic verdict of record",
        "description": ("Returned by the Critic run as structured output. It is the verdict of "
                        "record. The YAML scoring block in the post is kept for the site."),
        "type": "object",
        "properties": {
            "research_novelty": {**score, "description": "0 to 4."},
            "empirical_rigor": {**score, "description": "0 to 4."},
            "theoretical_connection": {**score, "description": "0 to 4."},
            "actionability": {**score, "description": "0 to 4."},
            "opportunity_pattern": {"type": "string", "enum": list(tm.OPPORTUNITY),
                                    "description": "Kept for comparison only."},
            "method_paradigm": {"type": "string", "enum": list(tm.METHOD),
                                "description": "Kept for comparison only."},
            "operation": {"type": "string", "enum": list(tm.OPERATION),
                          "description": "Kept for comparison only."},
            "falsifier_tested": {
                "type": "string", "enum": list(FALSIFIER_VALUES),
                "description": ("yes when the gate's falsifier test has been run as committed in "
                                "this arc, no when it has not been run, not_applicable when the "
                                "round tests no arc claim."),
            },
            "prior_status": {
                "type": "string", "enum": list(PRIOR_STATUS),
                "description": ("supported when the falsifier test ran and the prior's prediction "
                                "held, overturned when the falsifier test fired, inconclusive when "
                                "the test ran but cannot decide, not_tested when the falsifier has "
                                "not been run."),
            },
            "headline_basis": {
                "type": "string", "enum": list(HEADLINE_BASIS),
                "description": ("prespecified when the headline claim and its test were committed "
                                "in a card or in the gate before its estimate was seen, "
                                "exploratory when the headline emerged from the data."),
            },
            "verdict": {
                "type": "string", "enum": list(VERDICTS),
                "description": ("pursue means the headline claim as scoped is confirmatory and has "
                                "passed every kill test the gate's decision rule names in this arc, "
                                "so drafting is recommended if the arc ended now. revise means the "
                                "arc should continue, and one_line names the next kill test. "
                                "archive means close the arc without a paper (fatal flaw, already "
                                "answered, duplicate topic, or an overturned prior). The one "
                                "exception is an arc whose block lists a null result as the paper. "
                                "There an overturned prior is revise."),
            },
            "one_line": {"type": "string", "maxLength": ONE_LINE_MAX,
                         "description": ("One sentence stating the headline claim and, for revise, "
                                         "the next kill test.")},
            "headline_claim_id": {"type": "string",
                                  "description": "Optional. claim_id of the headline claim on the committed card."},
            "decision_rule_quoted": {"type": "string",
                                     "description": "Optional. Verbatim copy of the gate's decision_rule."},
            "exclusions_checked": {
                "type": "array",
                "description": "Optional. One item per numbered gate exclusion.",
                "items": {"type": "object",
                          "properties": {"id": {"type": "string"},
                                         "quoted_text": {"type": "string"},
                                         "respected": {"type": "string",
                                                       "enum": ["yes", "no", "needs_amendment"]}},
                          "required": ["id", "respected"]},
            },
        },
        "required": list(REQUIRED_FIELDS),
        "additionalProperties": False,
    }


def load_schema() -> dict:
    return json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))


def write_schema() -> Path:
    path = SCHEMA_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def schema_errors(obj: dict, schema: dict | None = None) -> list[str]:
    from prediction_card import schema_errors as _check
    return _check(obj, schema or load_schema())


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def _strip_comment(value: str) -> tuple[str, bool]:
    """Return (value without trailing comment, closed). A value that opens a
    quote without closing it on the line is returned with closed=False."""
    v = value.strip()
    if v[:1] in ('"', "'"):
        q = v[0]
        i = 1
        while i < len(v):
            if v[i] == "\\" and q == '"':
                i += 2
                continue
            if v[i] == q:
                if q == "'" and v[i + 1:i + 2] == "'":
                    i += 2
                    continue
                return v[:i + 1], True
            i += 1
        return v, False
    return re.split(r"\s+#", v, maxsplit=1)[0].strip(), True


def _unquote(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return v[1:-1]
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def _parse_block(body: str) -> dict:
    out: dict = {}
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = YAML_KEY_RE.match(line)
        if not m:
            continue
        key, raw = m.group(2), m.group(3)
        if not raw.strip():
            continue   # a mapping header such as 'scoring:'
        value, closed = _strip_comment(raw)
        while not closed and i < len(lines):
            value, closed = _strip_comment(value + " " + lines[i].strip())
            i += 1
        out[key] = _unquote(value)
    return out


def scoring_blocks(post_text: str) -> list[dict]:
    """Every ```yaml block that carries a verdict key, in post order."""
    blocks = []
    for body in YAML_BLOCK_RE.findall(post_text or ""):
        parsed = _parse_block(body)
        if "verdict" in parsed:
            blocks.append(parsed)
    return blocks


def parse_scoring_block(post_text: str) -> dict:
    """Normalized fields of the LAST ```yaml scoring block (the one with a
    verdict key), or {} when the post has none. Scores such as '4/4' become
    integers, labels and enums are lower-cased."""
    blocks = scoring_blocks(post_text)
    return normalize(blocks[-1]) if blocks else {}


def regex_legacy(post_text: str) -> dict:
    """The pre-v2.1 first-hit regex, kept only as a logged fallback for
    posts without a scoring block."""
    out = {}
    m = LEGACY_VERDICT_RE.search(post_text or "")
    if m:
        out["verdict"] = m.group(1)
    m = LEGACY_FALSIFIER_RE.search(post_text or "")
    if m:
        out["falsifier_tested"] = m.group(1).lower()
    m = LEGACY_ONE_LINE_RE.search(post_text or "")
    if m:
        out["one_line"] = m.group(1)
    return normalize(out)


def normalize(d: dict | None) -> dict:
    """Coerce a structured or YAML verdict into canonical types."""
    if not d:
        return {}
    out = {}
    for k, v in d.items():
        if k in SCORE_FIELDS:
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                out[k] = int(v)
            else:
                m = re.match(r"^\s*(\d+)(?:\s*/\s*\d+)?", str(v))
                if m:
                    out[k] = int(m.group(1))
        elif k == "verdict":
            m = re.match(r"^\s*(pursue|revise|archive)\b", str(v).lower())
            out[k] = m.group(1) if m else str(v).strip().lower()
        elif k == "falsifier_tested":
            s = str(v).strip().lower()
            s = {"true": "yes", "false": "no", "n/a": "not_applicable", "na": "not_applicable",
                 "not applicable": "not_applicable"}.get(s, s)
            out[k] = s.split()[0] if s else s
        elif k in LABEL_FIELDS or k in ("prior_status", "headline_basis"):
            out[k] = str(v).strip().lower().replace(" ", "_")
        elif k == "one_line":
            out[k] = str(v).strip()
        else:
            out[k] = v
    return out


# --------------------------------------------------------------------------
# Config and posts
# --------------------------------------------------------------------------

def _forum_config() -> dict:
    try:
        return json.loads(AGENTS_FILE.read_text(encoding="utf-8")).get("forum_config", {}) or {}
    except (OSError, json.JSONDecodeError):
        return {}


def stage2_enabled(flag: str) -> bool:
    """forum_config.stage2.<flag>, false when absent (D-01)."""
    return bool((_forum_config().get("stage2") or {}).get(flag, False))


def _round_posts(round_num: int) -> list[Path]:
    try:
        import forum_index
        posts = forum_index.round_posts(round_num, forum_dir=FORUM_DIR)
        if posts:
            return list(posts)
    except Exception:
        pass
    # Fallback: frontmatter round key, else the legacy three-posts-per-round rule.
    out = []
    for p in sorted(FORUM_DIR.glob("*.md")) if FORUM_DIR.exists() else []:
        m = re.match(r"^(\d+)_", p.name)
        if not m:
            continue
        n = int(m.group(1))
        head = p.read_text(encoding="utf-8")[:600]
        fm = re.search(r"^round:\s*R?(\d+)\s*$", head, re.MULTILINE)
        r = int(fm.group(1)) if fm else (n - 1) // 3 + 1
        if r == round_num:
            out.append(p)
    return out


def _role_post(round_num: int, role: str) -> Path | None:
    for p in _round_posts(round_num):
        if role in p.name:
            return p
    return None


def _arc_of_post(path: Path) -> str | int | None:
    try:
        import forum_index
        return forum_index.post_meta(path).get("arc")
    except Exception:
        return None


def _rel(p: Path | None) -> str | None:
    if p is None:
        return None
    try:
        return str(Path(p).resolve().relative_to(BASE_DIR))
    except ValueError:
        return Path(p).name


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def load_rows() -> list[dict]:
    return _read_jsonl(VERDICTS_FILE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# Record
# --------------------------------------------------------------------------

def record(round_num: int, arc_id: str | None, post_path: Path, structured: dict | None,
           run_id: str, *, events_paths: list | None = None) -> dict:
    """Reconcile the structured verdict with the post's YAML block, append
    one row to knowledge/verdicts.jsonl and return it.

    The returned "verdict" is the effective verdict of record. It equals the
    Critic's verdict unless the YAML and structured verdicts disagree, or a
    Stage 2 check overrides a pursue, in which case it is revise and
    "overrides" lists why. "verdict_critic" keeps what the Critic said.

    Idempotent. A second call for the same round and run_id returns the
    stored row. A call for a round that already has a row from another run is
    refused and returns the stored row with "refused_run_id" set."""
    for row in load_rows():
        if int(row.get("round", -1)) == int(round_num):
            if row.get("run_id") == run_id:
                return row
            print(f"  [Verdict] R{round_num}: already recorded by run {row.get('run_id')}; "
                  f"refusing a second write from {run_id}")
            return {**row, "refused_run_id": run_id}

    post_path = Path(post_path) if post_path else None
    text = post_path.read_text(encoding="utf-8") if post_path and post_path.exists() else ""
    yaml_v = parse_scoring_block(text)
    s = normalize(structured) if isinstance(structured, dict) else {}
    schema_errs = schema_errors(dict(structured)) if isinstance(structured, dict) else []
    if s.get("verdict") in VERDICTS:
        source, base = "structured", s
    elif yaml_v.get("verdict") in VERDICTS:
        source, base = "yaml", yaml_v
    else:
        source, base = "regex_legacy", regex_legacy(text)
        if base:
            print(f"  [Verdict] R{round_num}: no structured or YAML verdict, legacy regex used")

    mismatch = []
    if s and yaml_v:
        mismatch = [k for k in COMPARED_FIELDS if k in s and k in yaml_v and s[k] != yaml_v[k]]
    verdict_critic = base.get("verdict") if base.get("verdict") in VERDICTS else None
    verdict = verdict_critic
    overrides = []
    if "verdict" in mismatch:
        verdict = "revise"
        overrides.append(f"verdict mismatch: structured output says {s.get('verdict')}, "
                         f"post YAML says {yaml_v.get('verdict')}")

    row = {
        "ts": _now_iso(),
        "round": int(round_num),
        "arc": arc_id,
        "run_id": run_id,
        "post": _rel(post_path) if post_path else None,
        "verdict": verdict,
        "verdict_critic": verdict_critic,
        "verdict_structured": s.get("verdict"),
        "verdict_yaml": yaml_v.get("verdict"),
        "falsifier_tested": base.get("falsifier_tested"),
        "prior_status": base.get("prior_status"),
        "headline_basis": base.get("headline_basis"),
        "scores": {k: base.get(k) for k in SCORE_FIELDS},
        "labels": {k: base.get(k) for k in LABEL_FIELDS},
        "one_line": base.get("one_line"),
        "source": source,
        "mismatch": mismatch,
        "yaml_missing": bool(s) and not yaml_v,
        "schema_errors": schema_errs,
        "schema": SCHEMA_ID,
        "overrides": overrides,
    }
    if base.get("headline_claim_id"):
        row["headline_claim_id"] = base["headline_claim_id"]

    if stage2_enabled("binding_checks"):
        try:
            bc = binding_checks(round_num, arc_id, base)
            row["binding"] = {k: bc[k] for k in ("headline_claim_id", "falsifier_tested",
                                                 "kill_depth", "kill_rounds", "new_test_this_round",
                                                 "null_ok", "headline_basis_computed")}
            if verdict == "pursue" and bc["overrides"]:
                verdict = "revise"
                overrides += bc["overrides"]
        except Exception as e:   # a check that crashes must not pass a pursue silently
            if verdict == "pursue":
                verdict = "revise"
                overrides.append(f"binding checks failed to run: {e}")

    if stage2_enabled("claim_sheet_first") and events_paths:
        verdict = _apply_order_check(row, round_num, base, verdict, overrides, events_paths)

    row["verdict"] = verdict
    VERDICTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VERDICTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    flag = f" (Critic said {verdict_critic}; {len(overrides)} override(s))" if verdict != verdict_critic else ""
    print(f"  [Verdict] R{round_num}: {verdict} from {source}{flag}")
    return row


def _apply_order_check(row: dict, round_num: int, base: dict, verdict: str | None,
                       overrides: list, events_paths: list) -> str | None:
    """M16. The provisional verdict must be written before the Critic reads
    the Analyst post or scripts, and a later move needs an executed check."""
    import claim_sheet
    import prechecks
    events = prechecks.load_trace(events_paths)
    analyst = _role_post(round_num, "data_analyst")
    scripts = claim_sheet.analyst_scripts(round_num)
    order = claim_sheet.order_check(events, analyst_post_name=analyst.name if analyst else None,
                                    analyst_scripts=scripts)
    row["order"] = "respected" if order["respected"] else "order not respected"
    row["order_detail"] = order
    prov_path = WORKSPACE_DIR / f"r{int(round_num)}" / "critic_provisional.json"
    if not prov_path.exists():
        return verdict
    try:
        provisional = json.loads(prov_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return verdict
    shift = claim_sheet.provisional_shift(provisional, base, events, order.get("first_touch_idx"))
    row["provisional"] = {"verdict": provisional.get("verdict"), "moved": shift["moved"],
                          "check_after_reading": shift["check_after_reading"]}
    if shift["moved"]:
        SHIFTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SHIFTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _now_iso(), "round": int(round_num), "run_id": row["run_id"],
                                **shift}, ensure_ascii=False) + "\n")
    if shift["moved"] and not shift["check_after_reading"] and provisional.get("verdict") in VERDICTS \
            and provisional.get("verdict") != verdict:
        overrides.append("verdict moved from the provisional value without a check executed "
                         "after reading the Analyst post, so the provisional verdict stands")
        return provisional["verdict"]
    return verdict


# --------------------------------------------------------------------------
# Verdict of record and distribution
# --------------------------------------------------------------------------

def verdict_of_record(round_num: int) -> dict | None:
    """The stored verdicts.jsonl row for the round. For rounds without one
    (posts 001-090), the legacy rule, which is the first verdict line of the
    Critic post. That is the verdict the pre-v2.1 pipeline recorded, and
    ledger_audit.tally uses the same rule, so both give the same verdict for
    a post that scores several projects. The other fields come from the first
    scoring block when it holds that verdict (source yaml), else from the
    legacy regex (source regex_legacy). None when the round has no Critic post."""
    for row in load_rows():
        if int(row.get("round", -1)) == int(round_num):
            return row
    post = _role_post(round_num, "critic")
    if post is None:
        return None
    text = post.read_text(encoding="utf-8")
    legacy = regex_legacy(text)
    blocks = scoring_blocks(text)
    parsed = normalize(blocks[0]) if blocks else {}
    source = "yaml"
    if not parsed.get("verdict") or parsed.get("verdict") != legacy.get("verdict"):
        parsed, source = legacy, "regex_legacy"
    if not parsed:
        return None
    return {
        "round": int(round_num),
        "arc": _arc_of_post(post),
        "run_id": None,
        "post": _rel(post),
        "verdict": parsed.get("verdict"),
        "verdict_critic": parsed.get("verdict"),
        "falsifier_tested": parsed.get("falsifier_tested"),
        "prior_status": parsed.get("prior_status"),
        "headline_basis": parsed.get("headline_basis"),
        "scores": {k: parsed.get(k) for k in SCORE_FIELDS},
        "labels": {k: parsed.get(k) for k in LABEL_FIELDS},
        "one_line": parsed.get("one_line"),
        "source": source,
        "mismatch": [],
        "overrides": [],
        "legacy": True,
    }


def distribution(rounds, min_n: int = 3) -> dict:
    """Share of each verdict of record over the given rounds. A label above
    70 percent is flagged once at least min_n verdicts exist. For
    arc_status.json and the site, never for an agent prompt."""
    counts = Counter()
    for r in rounds:
        v = verdict_of_record(r)
        if v and v.get("verdict") in VERDICTS:
            counts[v["verdict"]] += 1
    n = sum(counts.values())
    shares = {k: (counts[k] / n if n else 0.0) for k in VERDICTS}
    flagged = [k for k in VERDICTS if n >= min_n and shares[k] > DISTRIBUTION_FLAG_SHARE]
    return {"n": n, "counts": {k: counts[k] for k in VERDICTS}, "shares": shares, "flagged": flagged}


def distribution_line(arc_rounds, season_rounds) -> str:
    def part(label, d):
        body = ", ".join(f"{k} {d['counts'][k]}/{d['n']}" for k in VERDICTS) if d["n"] else "no verdicts"
        flag = f" FLAG {'/'.join(d['flagged'])} above 70 percent." if d["flagged"] else ""
        return f"{label} {body}.{flag}"
    return " ".join([part("Verdicts this arc:", distribution(arc_rounds)),
                     part("Season:", distribution(season_rounds))])


def prompt_note(round_num: int) -> str:
    """One line for the next round's prompts when a pursue was overridden."""
    v = verdict_of_record(round_num)
    if not v or not v.get("overrides"):
        return ""
    reasons = "; ".join(v["overrides"][:4])
    return (f"\n(Verdict of record for R{round_num}: {v.get('verdict')}. The Critic's "
            f"{v.get('verdict_critic')} was not binding because: {reasons}.)\n")


# --------------------------------------------------------------------------
# Stage 2: scripted binding checks (M10b)
# --------------------------------------------------------------------------

_EXPR_FUNCS = {"abs": abs}
_EXPR_FIELD_FUNCS = ("estimate", "ci_low", "ci_high", "n", "se")


def eval_rule_expr(expr: str, quantities: dict) -> bool:
    """Evaluate a gate decision_rule_expr over {quantity_id: row}. Names are
    quantity ids (their estimate). ci_low(q), ci_high(q), se(q), n(q) and
    abs(x) are available. Anything else raises ValueError."""
    tree = ast.parse(expr, mode="eval")

    def val(q, field):
        row = quantities.get(q)
        if row is None:
            raise ValueError(f"unknown quantity {q!r}")
        if field in ("ci_low", "ci_high"):
            ci = row.get("ci") or [row.get("ci_low"), row.get("ci_high")]
            v = ci[0] if field == "ci_low" else ci[1]
        else:
            v = row.get(field)
        if v is None:
            raise ValueError(f"{field} of {q!r} is missing")
        return float(v)

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.BoolOp):
            vals = [ev(v) for v in node.values]
            return all(vals) if isinstance(node.op, ast.And) else any(vals)
        if isinstance(node, ast.UnaryOp):
            v = ev(node.operand)
            if isinstance(node.op, ast.Not):
                return not v
            if isinstance(node.op, ast.USub):
                return -v
            if isinstance(node.op, ast.UAdd):
                return +v
        if isinstance(node, ast.BinOp):
            a, b = ev(node.left), ev(node.right)
            ops = {ast.Add: lambda: a + b, ast.Sub: lambda: a - b,
                   ast.Mult: lambda: a * b, ast.Div: lambda: a / b}
            for t, f in ops.items():
                if isinstance(node.op, t):
                    return f()
        if isinstance(node, ast.Compare):
            left = ev(node.left)
            for op, comp in zip(node.ops, node.comparators):
                right = ev(comp)
                ok = {ast.Lt: left < right, ast.LtE: left <= right, ast.Gt: left > right,
                      ast.GtE: left >= right, ast.Eq: left == right, ast.NotEq: left != right}
                hit = [v for t, v in ok.items() if isinstance(op, t)]
                if not hit or not hit[0]:
                    return False
                left = right
            return True
        if isinstance(node, ast.Name):
            return val(node.id, "estimate")
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            name = node.func.id
            if name in _EXPR_FIELD_FUNCS and len(node.args) == 1 and isinstance(node.args[0], ast.Name):
                return val(node.args[0].id, name)
            if name in _EXPR_FUNCS and len(node.args) == 1:
                return _EXPR_FUNCS[name](ev(node.args[0]))
        raise ValueError(f"unsupported expression element: {ast.dump(node)[:80]}")

    return bool(ev(tree))


def _active_gate() -> dict:
    try:
        return json.loads(ACTIVE_ARC_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _analyst_start(round_num: int) -> str | None:
    """Earliest Analyst run start for the round from logs/rNN/*.sidecar.json."""
    starts = []
    for d in {LOGS_DIR / f"r{int(round_num):02d}", LOGS_DIR / f"r{int(round_num)}"}:
        for p in d.glob("*.sidecar.json") if d.exists() else []:
            try:
                sc = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if sc.get("role") != "data_analyst":
                continue
            t = sc.get("created") or ((sc.get("attempts") or [{}])[0].get("started"))
            if t:
                starts.append(t)
    return min(starts, key=_ts) if starts else None


def _ts(s):
    from prediction_card import _ts as parse
    return parse(s)


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _has_result(res: dict | None) -> bool:
    return bool(res) and str(res.get("status", "")).lower() != "not_computable"


def _is_reported_null(res: dict, spec: dict | None) -> bool:
    import prediction_card as pc
    if "reported_null" in res:
        return bool(res["reported_null"])
    lo, hi = res.get("ci_low"), res.get("ci_high")
    return bool(spec) and spec.get("role") in pc.KILL_ROLES and lo is not None and hi is not None \
        and lo <= 0 <= hi


def binding_checks(round_num: int, arc_id: str | None = None, critic: dict | None = None, *,
                   headline_claim_id: str | None = None, gate: dict | None = None,
                   cards: dict | None = None, card_meta: dict | None = None,
                   results: dict | None = None, quantities: list | None = None,
                   prechecks: dict | None = None, analyst_start: dict | None = None,
                   arc_start_round: int | None = None, exists=None) -> dict:
    """Scripted checks on the arc's committed cards and results (M10b).

    Computed from files, never from the Critic's text:
      falsifier_tested     the gate's decisive spec (the arc-opening card's
                           primary, or a spec marked decisive) has a results
                           file whose script and output exist, its card was
                           committed before that round's Analyst run started,
                           and the headline claim is the claim under the gate
      kill_depth           arc rounds with at least one new kill spec for the
                           headline claim. A kill spec is a primary,
                           robustness or placebo spec whose normalized
                           (outcome_def, sample_def, model) appears in no
                           earlier card for the same claim and whose results
                           file exists. Reproduction, calibration and sanity
                           specs never count.
      new_test_this_round  this round is one of those rounds
      null_ok              every reported null has an equivalence bound on a
                           card committed before its estimate
    Returns the checks, the reasons a pursue would not bind ("overrides"),
    and verdict_effective for the Critic's verdict."""
    import prediction_card as pc
    critic = critic or {}
    cards = cards if cards is not None else pc.load_cards()
    meta = card_meta if card_meta is not None else pc.card_meta()
    gate = gate if gate is not None else _active_gate()
    start = arc_start_round or int(gate.get("start_round") or 0) or (min(cards) if cards else round_num)
    rounds = [r for r in sorted(cards) if start <= r <= round_num]
    res_by_round = results if results is not None else {r: pc.load_results(r) for r in rounds}
    quantities = quantities if quantities is not None else pc.load_quantities()
    exists = exists or (lambda p: bool(p) and (BASE_DIR / str(p)).exists())
    starts = analyst_start if analyst_start is not None else {r: _analyst_start(r) for r in rounds}
    gate_card = cards.get(start) or {}
    gate_claim = gate_card.get("claim_id")
    headline = headline_claim_id or critic.get("headline_claim_id") or gate_claim

    # Kill specs and depth
    seen: dict = {}
    for r in sorted(cards):
        if r < start:
            for s in cards[r].get("spec_plan") or []:
                seen.setdefault(pc.spec_claim_id(cards[r], s), set()).add(pc.signature(s))
    kill_rounds, new_kill = [], {}
    for r in rounds:
        card, rr = cards[r], res_by_round.get(r) or {}
        found = []
        for s in card.get("spec_plan") or []:
            cid = pc.spec_claim_id(card, s)
            if s.get("role") in pc.KILL_ROLES and pc.signature(s) not in seen.get(cid, set()) \
                    and _has_result(rr.get(s.get("spec_id"))):
                found.append([cid, s.get("spec_id")])
        for s in card.get("spec_plan") or []:
            seen.setdefault(pc.spec_claim_id(card, s), set()).add(pc.signature(s))
        new_kill[r] = found
        if any(c == headline for c, _ in found):
            kill_rounds.append(r)
    new_test = round_num in kill_rounds

    # Falsifier executed under the committed card
    ft, ft_reason = False, ""
    specs = gate_card.get("spec_plan") or []
    decisive = next((s for s in specs if s.get("decisive")), None) \
        or next((s for s in specs if s.get("role") == "primary"), None)
    if not gate_card:
        ft_reason = "no card committed for the arc's opening round"
    elif headline != gate_claim:
        ft_reason = f"headline claim {headline} is not the claim under the gate's falsifier ({gate_claim})"
    elif decisive is None:
        ft_reason = "the opening card has no decisive spec"
    else:
        ft_reason = f"decisive spec {decisive.get('spec_id')} has no results file"
        committed = _ts((meta.get(start) or {}).get("committed_at"))
        for r in rounds:
            res = (res_by_round.get(r) or {}).get(decisive.get("spec_id"))
            if not _has_result(res):
                continue
            began = _ts(starts.get(r))
            if not exists(res.get("script")):
                ft_reason = f"script {res.get('script')} not found"
            elif not exists(res.get("output")):
                ft_reason = f"output file {res.get('output')} not found"
            elif not (committed and began and committed < began):
                ft_reason = "card commit time does not precede the Analyst run start"
            else:
                ft, ft_reason = True, f"decisive spec {decisive.get('spec_id')} executed in R{r}"
            break

    # Nulls need a bound committed before estimation
    null_problems = []
    for r in rounds:
        card = cards[r]
        spec_map = {s.get("spec_id"): s for s in card.get("spec_plan") or []}
        for sid, res in sorted((res_by_round.get(r) or {}).items()):
            spec = spec_map.get(sid)
            if not _is_reported_null(res, spec):
                continue
            cid = res.get("claim_id") or (pc.spec_claim_id(card, spec) if spec else None)
            bound_round, claim = None, None
            for r2 in sorted(cards):
                if r2 <= r and pc.claim_by_id(cards[r2], cid):
                    bound_round, claim = r2, pc.claim_by_id(cards[r2], cid)
                    break
            if claim is None or claim.get("equivalence_bound") is None:
                null_problems.append(f"R{r} {sid}: null reported without an equivalence bound")
                continue
            committed = _ts((meta.get(bound_round) or {}).get("committed_at"))
            estimated = _ts(res.get("created_at")) or _ts(starts.get(r))
            if not (committed and estimated and committed < estimated):
                null_problems.append(f"R{r} {sid}: equivalence bound not committed before estimation")
    null_ok = not null_problems

    # Decision rule quote and expression (legacy gates without a rule skip both)
    rule = gate.get("decision_rule")
    quote_ok = None
    if rule:
        head_claim = None
        for r in reversed(rounds):
            head_claim = pc.claim_by_id(cards[r], headline)
            if head_claim:
                break
        quotes = [q for q in ((head_claim or {}).get("decision_rule_quoted"),
                              critic.get("decision_rule_quoted")) if q]
        quote_ok = bool(quotes) and all(_norm_ws(q) in _norm_ws(rule) for q in quotes)
    expr_ok, expr_error = None, None
    if gate.get("decision_rule_expr") and quantities:
        latest = {}
        for row in sorted(quantities, key=lambda x: int(x.get("round", 0))):
            if start <= int(row.get("round", 0)) <= round_num:
                latest[row.get("quantity_id")] = row
        try:
            expr_ok = eval_rule_expr(gate["decision_rule_expr"], latest)
        except (ValueError, SyntaxError, ZeroDivisionError) as e:
            expr_ok, expr_error = False, str(e)

    # Headline basis from the ledger
    basis = None
    head_q = None
    for r in rounds:
        c = pc.claim_by_id(cards[r], headline)
        if c:
            head_q = c.get("quantity_id")
            break
    if head_q:
        st = pc.quantity_status(head_q, quantities, since_round=start)
        basis = None if st is None else ("prespecified" if st == "confirmatory" else "exploratory")

    # Blocking prechecks
    pre = prechecks if prechecks is not None else _load_prechecks(round_num)
    blocking = []
    for post in (pre.get("posts") or {}).values():
        for rule_row in post.get("rules") or []:
            if rule_row.get("status") == "FAIL" and rule_row.get("blocking"):
                blocking.append(rule_row.get("id"))

    overrides = []
    if not ft:
        overrides.append(f"falsifier_tested false: {ft_reason}")
    if not new_test:
        overrides.append("new_test_this_round false: no new kill test on the headline claim this round")
    if not null_ok:
        overrides.append("null_ok false: " + "; ".join(null_problems[:3]))
    if basis == "exploratory" or critic.get("headline_basis") == "exploratory":
        overrides.append("headline is exploratory")
    if quote_ok is False:
        overrides.append("decision_rule_quoted is not a verbatim part of the gate's decision_rule")
    if expr_ok is False:
        overrides.append("decision_rule_expr is not met" + (f" ({expr_error})" if expr_error else ""))
    if blocking:
        overrides.append("blocking precheck failed: " + ", ".join(sorted(set(blocking))))
    v = critic.get("verdict")
    return {
        "round": int(round_num),
        "arc": arc_id,
        "headline_claim_id": headline,
        "gate_claim_id": gate_claim,
        "falsifier_tested": ft,
        "falsifier_reason": ft_reason,
        "kill_depth": len(kill_rounds),
        "kill_rounds": kill_rounds,
        "new_kill_specs": {str(k): v2 for k, v2 in new_kill.items()},
        "new_test_this_round": new_test,
        "null_ok": null_ok,
        "null_problems": null_problems,
        "decision_rule_quote_ok": quote_ok,
        "decision_rule_expr_ok": expr_ok,
        "headline_basis_computed": basis,
        "blocking_prechecks": sorted(set(blocking)),
        "overrides": overrides,
        "verdict_effective": "revise" if (v == "pursue" and overrides) else v,
    }


def _load_prechecks(round_num: int) -> dict:
    p = PRECHECKS_DIR / f"R{int(round_num):02d}.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> None:
    ap = argparse.ArgumentParser(description="Critic verdict of record")
    ap.add_argument("--write-schema", action="store_true",
                    help="Regenerate knowledge/schemas/critic_verdict.json")
    sub = ap.add_subparsers(dest="cmd")
    sh = sub.add_parser("show", help="Verdict of record for one round")
    sh.add_argument("--round", type=int, required=True)
    di = sub.add_parser("distribution", help="Verdict distribution line")
    di.add_argument("--since", type=int, default=1, help="First round of the season")
    di.add_argument("--arc-start", type=int, default=None)
    di.add_argument("--until", type=int, default=None)
    args = ap.parse_args()
    if args.write_schema:
        print(f"wrote {write_schema()}")
        return
    if args.cmd == "show":
        print(json.dumps(verdict_of_record(args.round), ensure_ascii=False, indent=2))
        return
    if args.cmd == "distribution":
        until = args.until
        if until is None:
            try:
                import forum_index
                until = forum_index.current_round(forum_dir=FORUM_DIR)
            except Exception:
                until = args.since
        arc_start = args.arc_start or int(_active_gate().get("start_round") or args.since)
        print(distribution_line(range(arc_start, until + 1), range(args.since, until + 1)))
        return
    ap.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
