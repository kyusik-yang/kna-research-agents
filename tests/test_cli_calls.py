"""Every claude invocation goes through claude_cli.run_claude (M01).

The repository scan fails on any direct call outside claude_cli.py: a bare
"-p" or "--print" list element near a claude reference (the old
run_forum.py and agora/run_agora.py pattern), a shutil.which("claude")
lookup, a list starting with CLAUDE, or `claude -p` in a shell script.
run_loop.py is the one named exception until D-23.

Every call site is migrated, so the repository scan runs in the default
suite (V-11).
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

EXEMPT_FILES = {"claude_cli.py", "run_loop.py"}
EXCLUDED_DIRS = {"tests", "workspace", "forum", "forum_archive", "forum_archive_retired", "docs",
                 "articles", "logs", "knowledge", "summaries", "data", ".git", "__pycache__", ".venv"}
WINDOW = 3  # lines before a quoted -p that may name the binary

PY_DASH_P = re.compile(r"""["'](?:-p|--print)["']""")
PY_WHICH = re.compile(r"""which\(\s*["']claude["']\s*\)""")
PY_CLAUDE_LIST = re.compile(r"(?:\[|^)\s*CLAUDE\s*[,\]]")  # [CLAUDE, ...] or a CLAUDE, list line
SH_CALL = re.compile(r"(?:^|[\s;&|(`$])claude\s+(?:-p|--print)\b")


def scan_text(text: str, suffix: str) -> list[tuple[int, str]]:
    """(line number, line) for every direct claude invocation in one file."""
    hits = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if suffix == ".sh":
            if SH_CALL.search(line):
                hits.append((i + 1, stripped))
            continue
        window = "\n".join(lines[max(0, i - WINDOW): i + 1]).lower()
        if (PY_DASH_P.search(line) and "claude" in window) or PY_WHICH.search(line) \
                or PY_CLAUDE_LIST.search(line):
            hits.append((i + 1, stripped))
    return hits


def scan_repo(root: Path) -> list[str]:
    found = []
    for path in sorted(root.rglob("*")):
        if path.suffix not in (".py", ".sh") or not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.parts[0] in EXCLUDED_DIRS or rel.name in EXEMPT_FILES and len(rel.parts) == 1:
            continue
        if any(part in EXCLUDED_DIRS for part in rel.parts[:-1]):
            continue
        for n, line in scan_text(path.read_text(encoding="utf-8", errors="replace"), path.suffix):
            found.append(f"{rel}:{n}: {line}")
    return found


# ---------------------------------------------------------------- scanner tests (always run)

def test_scanner_catches_direct_calls():
    py = 'cmd = [\n    CLAUDE,\n    "-p",\n    "--allowedTools", tools,\n]\n'
    assert [n for n, _ in scan_text(py, ".py")] == [2, 3]
    assert scan_text('subprocess.run(["claude", "-p", "x"])\n', ".py")
    assert scan_text('CLAUDE = shutil.which("claude") or "x"\n', ".py")
    sh = 'FINDING=$(claude -p --allowedTools Read --output-format text "x")\n'
    assert scan_text(sh, ".sh") == [(1, sh.strip())]
    assert scan_text('    claude --print "hi"\n', ".sh")


def test_scanner_ignores_unrelated_dash_p():
    assert scan_text('ap.add_argument("-p", "--port", type=int)\n', ".py") == []
    assert scan_text('"""Execute one agent via claude -p."""\n', ".py") == []
    assert scan_text("mkdir -p logs\n# claude -p in a comment\n", ".sh") == []
    assert scan_text('res = claude_cli.run_claude("agent", prompt, role="critic")\n', ".py") == []


def test_scanner_skips_exempt_and_excluded(tmp_path):
    (tmp_path / "claude_cli.py").write_text('cmd = [CLAUDE, "-p"]\n')
    (tmp_path / "run_loop.py").write_text('cmd = [CLAUDE, "-p"]\n')
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.py").write_text('cmd = [CLAUDE, "-p"]\n')
    (tmp_path / "agora").mkdir()
    (tmp_path / "agora" / "run_agora.py").write_text('cmd = [\n    CLAUDE,\n    "-p",\n]\n')
    (tmp_path / "auto_run.sh").write_text("X=$(claude -p 'y')\n")
    assert scan_repo(tmp_path) == [
        "agora/run_agora.py:2: CLAUDE,", "agora/run_agora.py:3: \"-p\",",
        "auto_run.sh:1: X=$(claude -p 'y')"]


# ---------------------------------------------------------------- repository scan (always runs)

def test_no_direct_claude_calls_outside_wrapper():
    found = scan_repo(ROOT)
    assert not found, "direct claude calls outside claude_cli.py:\n" + "\n".join(found)
