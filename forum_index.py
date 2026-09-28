#!/usr/bin/env python3
"""Round and arc identity of forum posts (Season 2 v2.1, since 2026-09-25).

Until v2.1 every script took a post's round from its file index divided by
three. That holds only while every round is a complete Scout, Analyst, Critic
triple. When the R30 Critic failed, the next --resume run started all three
agents again, which produced phantom rounds and four commits labeled with the
same round.

From v2.1 the orchestrator writes the post's identity into its frontmatter
(round, arc, role and the provenance keys in ORCHESTRATOR_KEYS) by a
line-level edit of the first --- block, so the agent's own YAML stays
byte-identical. This module reads that identity back:

  frontmatter  the post carries a `round` key (every post from Arc 6 on).
  legacy       posts 001-090 carry no keys. They are 30 complete triples in
               ROLE_ORDER, so the round is (n - 1) // 3 + 1, the role comes
               from the file name, and the arc from LEGACY_ARCS. A post in
               that range whose role does not fit its triple slot is
               inferred instead.
  inferred     a post without keys outside that grid (a crash between the
               agent's post and the key write). It joins the round of the
               post before it when that round is incomplete and does not
               have its role yet, and otherwise opens the next round.

Usage:
    python3 forum_index.py            # print the round plan for --resume
    python3 forum_index.py --posts    # print every post's identity
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"

ROLE_ORDER = ("literature_scout", "data_analyst", "critic")

# Keys the orchestrator writes into a post's first --- block. Agents do not
# write them, and nothing else in the block is touched when they are set.
ORCHESTRATOR_KEYS = ("round", "arc", "role", "run_id", "model", "models_used",
                     "claude_code_version", "effort", "num_turns",
                     "terminal_reason", "attempt")

# Arcs that predate frontmatter identity: arc number -> (first round, last
# round). Season 1 per SEASON2.md (R1-R13 diverse topics, R14-R22 progressive
# ambition, R23-R24 committee chair allocation). Season 2 Arc 4 (R25-R27) and
# Arc 5 (R28-R30), opened at R25 and R28 in topic_gate.md.
LEGACY_ARCS = {
    1: (1, 13),
    2: (14, 22),
    3: (23, 24),
    4: (25, 27),
    5: (28, 30),
}
LEGACY_LAST_ROUND = max(last for _, last in LEGACY_ARCS.values())
LEGACY_LAST_POST = LEGACY_LAST_ROUND * len(ROLE_ORDER)   # 090_critic.md

_POST_RE = re.compile(r"^(\d+)_(.+)\.md$")
_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)[ \t]*:(?:[ \t]+(.*?))?[ \t]*$")
_INT_RE = re.compile(r"^[-+]?\d+$")


# ---------------------------------------------------------------------------
# Frontmatter: read flat key: value pairs, write single lines in place
# ---------------------------------------------------------------------------

def _is_fence(line: str) -> bool:
    return line.lstrip("\ufeff").rstrip() == "---"


def _split_flow(inner: str) -> list[str]:
    """Split the inside of a flow list on commas outside quotes."""
    items, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            items.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail or items:
        items.append(tail)
    return [i for i in items if i != ""]


def _parse_scalar(raw: str | None):
    """Parse one flat YAML value: quoted string, flow list, int, bool, null,
    or a plain string (with a trailing ' # comment' removed)."""
    if raw is None:
        return None
    s = raw.strip()
    if s == "" or s in ("null", "Null", "NULL", "~"):
        return None
    if s[0] == '"' and s.endswith('"') and len(s) >= 2:
        try:
            return json.loads(s)
        except ValueError:
            return s[1:-1]
    if s[0] == "'" and s.endswith("'") and len(s) >= 2:
        return s[1:-1].replace("''", "'")
    if s[0] == "[" and s.endswith("]"):
        try:
            return json.loads(s)
        except ValueError:
            return [_parse_scalar(i) for i in _split_flow(s[1:-1])]
    s = re.sub(r"\s+#.*$", "", s)
    if _INT_RE.match(s):
        return int(s)
    if s in ("true", "True", "TRUE"):
        return True
    if s in ("false", "False", "FALSE"):
        return False
    return s


def _split_lines(text: str) -> list[str]:
    """Lines with their endings, split on \\n only, so "".join gives the
    text back byte for byte. str.splitlines would also split on U+2028."""
    parts = text.split("\n")
    lines = [part + "\n" for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def _is_continuation(line: str) -> bool:
    """An indented or '- item' line that belongs to the key above it."""
    text = line.rstrip("\r\n")
    return bool(text.strip()) and (text[0].isspace() or text == "-" or text.startswith("- "))


def _block_bounds(lines: list[str]) -> tuple[int, int] | None:
    """(0, closing index) of the first --- block, or None if the text does
    not open with a closed one."""
    if not lines or not _is_fence(lines[0]):
        return None
    for j in range(1, len(lines)):
        if _is_fence(lines[j]):
            return 0, j
    return None


def _parse_block(block: list[str]) -> dict:
    out: dict = {}
    key, value, items, extra = None, None, [], []

    def flush():
        if key is None:
            return
        if value is None and items:
            out[key] = [_parse_scalar(i) for i in items]
        elif value is None and extra:
            out[key] = "\n".join(extra)
        else:
            out[key] = _parse_scalar(value)

    for line in block:
        text = line.rstrip("\r\n")
        if not text.strip() or text.startswith("#"):
            continue
        m = _KEY_RE.match(text)
        if m and not text[0].isspace():
            flush()
            key, value, items, extra = m.group(1), m.group(2), [], []
            if value is not None and value.strip() in ("|", ">", "|-", ">-"):
                value = None
            continue
        if key is None:
            continue
        stripped = text.strip()
        if stripped.startswith("- ") or stripped == "-":
            items.append(stripped[1:].strip())
        else:
            extra.append(stripped)
    flush()
    return out


def read_frontmatter(path: Path) -> dict:
    """Flat key: value pairs of the post's first --- block ({} if none).

    Only the first block is read, so YAML blocks the agents put in the body
    (scoring, prediction cards) never leak in. Indented '- item' lines under
    an empty key become a list, a flow list '[a, b]' becomes a list, ints,
    booleans and null are converted, everything else stays a string."""
    lines = []
    try:
        with open(path, encoding="utf-8") as f:
            first = f.readline()
            if not _is_fence(first):
                return {}
            for line in f:
                if _is_fence(line):
                    return _parse_block(lines)
                lines.append(line)
    except (OSError, UnicodeDecodeError):
        return {}
    return {}   # unclosed block


def _dump_value(value) -> str:
    """One-line YAML value that the flat reader and yaml.safe_load both read
    back to the same thing (strings are JSON-quoted, lists are flow lists)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_dump_value(v) for v in value) + "]"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    out = json.dumps(str(value), ensure_ascii=False)
    for ch in ("\u2028", "\u2029", "\x85"):
        out = out.replace(ch, "\\u%04x" % ord(ch))
    return out


def set_frontmatter_keys(path: Path, keys: dict) -> None:
    """Replace or insert `key: value` lines in the post's first --- block.

    A key already in the block is rewritten on its own line (with any
    indented continuation lines under it). A new key is inserted just before
    the closing ---. Every other byte of the file, including the agent's own
    frontmatter lines and all body YAML blocks, is left as it was. A file
    without a closed first block gets a new block on top. Never a YAML load
    and dump."""
    path = Path(path)
    for k in keys:
        if not isinstance(k, str) or not _KEY_RE.match(f"{k}: x"):
            raise ValueError(f"invalid frontmatter key: {k!r}")
    if not keys:
        return

    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    lines = _split_lines(text)
    eol = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    bounds = _block_bounds(lines)
    if bounds is None:
        bom = "\ufeff" if text.startswith("\ufeff") else ""
        body = text[len(bom):]
        new = [f"{k}: {_dump_value(v)}{eol}" for k, v in keys.items()]
        out = bom + f"---{eol}" + "".join(new) + f"---{eol}" + body
    else:
        _, close = bounds
        block = lines[1:close]
        for k, v in keys.items():
            new_line = f"{k}: {_dump_value(v)}"
            hits = []
            for i, line in enumerate(block):
                m = _KEY_RE.match(line.rstrip("\r\n"))
                if m and not line[0].isspace() and m.group(1) == k:
                    hits.append(i)
            if not hits:
                block.append(new_line + eol)
                continue
            # Rewrite the first occurrence in place and drop later duplicates,
            # so the reader (last wins) and the writer agree.
            for i in reversed(hits):
                end = i + 1
                while end < len(block) and _is_continuation(block[end]):
                    end += 1
                old = block[i]
                line_eol = old[len(old.rstrip("\r\n")):] or eol
                if i == hits[0]:
                    block[i:end] = [new_line + line_eol]
                else:
                    del block[i:end]
        out = lines[0] + "".join(block) + "".join(lines[close:])

    tmp = path.with_name(f".{path.name}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    os.chmod(tmp, os.stat(path).st_mode & 0o7777)
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Post identity
# ---------------------------------------------------------------------------

def _forum_dir(forum_dir: Path | None) -> Path:
    return Path(forum_dir) if forum_dir is not None else FORUM_DIR


def _post_num(path: Path) -> int | None:
    m = _POST_RE.match(Path(path).name)
    return int(m.group(1)) if m else None


def _filename_role(path: Path) -> str | None:
    m = _POST_RE.match(Path(path).name)
    if not m:
        return None
    rest = m.group(2)
    for role in ROLE_ORDER:
        if rest == role or rest.startswith(role + "_"):
            return role
    return rest


def _parse_round(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        m = re.fullmatch(r"\s*[Rr]?(\d+)\s*", value)
        if m and int(m.group(1)) > 0:
            return int(m.group(1))
    return None


def _parse_arc(value):
    """Arc number as an int ('6', 6, 'arc6', 'Arc 6', 'A6'). Any other
    non-empty value is returned unchanged."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    m = re.fullmatch(r"\s*(?:arc|a)?[\s_-]*(\d+)\s*", str(value), flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
    return value if str(value).strip() else None


def _legacy_arc(round_num: int | None) -> int | None:
    if round_num is None:
        return None
    for arc, (first, last) in LEGACY_ARCS.items():
        if first <= round_num <= last:
            return arc
    return None


def _active_arc(forum_dir: Path) -> dict:
    # Resolve first, so a relative forum dir such as "." still finds its
    # sibling knowledge/ folder.
    f = Path(forum_dir).resolve().parent / "knowledge" / "active_arc.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _arc_for_round(round_num: int | None, forum_dir: Path) -> int | str | None:
    """Static table first, then the active arc if the round lies in it."""
    arc = _legacy_arc(round_num)
    if arc is not None or round_num is None:
        return arc
    active = _active_arc(forum_dir)
    arc_id = _parse_arc(active.get("arc_id", active.get("arc")))
    start = _parse_round(active.get("start_round"))
    if arc_id is not None and start is not None and round_num >= start:
        return arc_id
    return None


def _is_legacy_slot(post_num: int | None, role: str | None) -> bool:
    """Posts 001-090 whose file-name role matches their triple slot."""
    if post_num is None or not 1 <= post_num <= LEGACY_LAST_POST:
        return False
    return role == ROLE_ORDER[(post_num - 1) % len(ROLE_ORDER)]


def _role(fm: dict, path: Path) -> str | None:
    role = fm.get("role")
    return role if isinstance(role, str) and role else _filename_role(path)


def _meta_direct(path: Path, fm: dict, forum_dir: Path) -> dict | None:
    """Identity from frontmatter or the legacy grid, or None if it needs
    the neighbouring posts (inferred)."""
    n = _post_num(path)
    role = _role(fm, path)
    rnd = _parse_round(fm.get("round"))
    if rnd is not None:
        source = "frontmatter"
    elif _is_legacy_slot(n, role):
        rnd, source = (n - 1) // len(ROLE_ORDER) + 1, "legacy"
    else:
        return None
    arc = _parse_arc(fm.get("arc"))
    if arc is None:
        arc = _arc_for_round(rnd, forum_dir)
    return {"path": Path(path), "post_num": n, "round": rnd, "arc": arc,
            "role": role, "legacy": source == "legacy", "source": source}


def all_posts(*, forum_dir: Path | None = None) -> list[Path]:
    """Numbered posts (NNN_<role>.md) in post-number order."""
    d = _forum_dir(forum_dir)
    if not d.is_dir():
        return []
    posts = [p for p in d.iterdir() if p.is_file() and _POST_RE.match(p.name)]
    return sorted(posts, key=lambda p: (_post_num(p), p.name))


def index(*, forum_dir: Path | None = None) -> list[dict]:
    """post_meta for every post, in post-number order, in one pass."""
    d = _forum_dir(forum_dir)
    metas: list[dict] = []
    roles_by_round: dict[int, set] = {}
    for p in all_posts(forum_dir=d):
        fm = read_frontmatter(p)
        meta = _meta_direct(p, fm, d)
        if meta is None:
            role = _role(fm, p)
            prev = metas[-1] if metas else None
            if prev is None:
                rnd = 1
            elif role not in ROLE_ORDER or role not in roles_by_round.get(prev["round"], set()):
                # A non-agent post, or a role the round in progress still
                # lacks, joins that round. A repeated role opens the next.
                rnd = prev["round"]
            else:
                rnd = prev["round"] + 1
            if prev is not None and prev["round"] == rnd and prev["arc"] is not None:
                arc = prev["arc"]
            else:
                arc = _arc_for_round(rnd, d)
            meta = {"path": p, "post_num": _post_num(p), "round": rnd, "arc": arc,
                    "role": role, "legacy": False, "source": "inferred"}
        roles_by_round.setdefault(meta["round"], set()).add(meta["role"])
        metas.append(meta)
    return metas


def post_meta(path: Path) -> dict:
    """{"path", "post_num", "round", "arc", "role", "legacy", "source"}.

    source is "frontmatter", "legacy" or "inferred" (see the module
    docstring). A post that needs inference is placed by scanning its
    folder, so the answer always agrees with index()."""
    path = Path(path)
    fm = read_frontmatter(path)
    meta = _meta_direct(path, fm, path.parent)
    if meta is not None:
        return meta
    for m in index(forum_dir=path.parent):
        if m["path"].name == path.name:
            return m
    return {"path": path, "post_num": _post_num(path), "round": None, "arc": None,
            "role": _role(fm, path), "legacy": False, "source": "inferred"}


def round_posts(round_num: int, *, forum_dir: Path | None = None) -> list[Path]:
    """Posts of one round, in post-number order."""
    return [m["path"] for m in index(forum_dir=forum_dir) if m["round"] == round_num]


def current_round(*, forum_dir: Path | None = None) -> int:
    """Highest round with any post (0 if the forum is empty)."""
    return max((m["round"] for m in index(forum_dir=forum_dir) if m["round"]), default=0)


def missing_roles(round_num: int, order=ROLE_ORDER, *,
                  forum_dir: Path | None = None) -> list[str]:
    """Roles in `order` that have no post in the round yet."""
    have = {m["role"] for m in index(forum_dir=forum_dir) if m["round"] == round_num}
    return [r for r in order if r not in have]


def next_round_plan(order=ROLE_ORDER, *, forum_dir: Path | None = None) -> tuple[int, list[str]]:
    """(round, roles to run). An incomplete latest round is resumed at its
    missing roles only. Otherwise the next round runs every role."""
    cur = current_round(forum_dir=forum_dir)
    if cur == 0:
        return 1, list(order)
    missing = missing_roles(cur, order, forum_dir=forum_dir)
    if missing:
        return cur, missing
    return cur + 1, list(order)


def next_post_number(*, forum_dir: Path | None = None) -> int:
    """Highest post number plus one, so a gap or a quarantined post never
    makes two posts share a number."""
    return max((_post_num(p) for p in all_posts(forum_dir=forum_dir)), default=0) + 1


def main():
    parser = argparse.ArgumentParser(description="Forum round and arc index")
    parser.add_argument("--posts", action="store_true", help="List every post's identity")
    args = parser.parse_args()
    if args.posts:
        for m in index():
            flag = "" if m["source"] == "frontmatter" else f" ({m['source']})"
            print(f"  {m['path'].name:32s} R{m['round']:<3} arc {m['arc']}  {m['role']}{flag}")
    rnd, roles = next_round_plan()
    print(f"  current round: {current_round()}  next post: {next_post_number():03d}")
    print(f"  plan: round {rnd}, roles {', '.join(roles)}")


if __name__ == "__main__":
    sys.exit(main())
