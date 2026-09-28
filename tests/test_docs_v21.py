"""Public docs stay in step with the v2.1 code (verifier findings V-05, V-06, V-13).

Read-only checks on the public docs README.md, SEASON2.md and FORUM_RULES.md,
cross-checked against the code where the docs describe it.
Nothing here writes a file."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ("README.md", "SEASON2.md", "FORUM_RULES.md")


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _season2_line(prefix: str) -> str:
    hits = [ln for ln in _read("SEASON2.md").splitlines() if ln.startswith(prefix)]
    assert len(hits) == 1, f"expected one SEASON2.md line starting with {prefix!r}"
    return hits[0]


def _prose(text: str) -> str:
    """Drop inline code spans so `.,;)]}` and similar literals do not count."""
    return re.sub(r"`[^`]*`", "", text)


# A colon joining two clauses, as in "Zahavy: what moves a field". Bold labels
# such as "**v2.1:** the" end in "**" before the space and do not match.
CLAUSE_COLON = re.compile(r"[\w.)]: [a-z]")


# --- V-05: every --comment example carries --by ------------------------------

@pytest.mark.parametrize("name", DOCS)
def test_comment_examples_name_their_author(name):
    text = _read(name)
    # The quoted note may span lines, so match the
    # quote as a unit and look at the rest of the command line after it.
    for m in re.finditer(r'run_forum\.py --comment "[^"]*"([^\n]*)', text):
        assert "--by" in m.group(1), f"{name}: --comment example without --by: {m.group(0)[:80]!r}"


def test_run_forum_still_requires_by():
    src = _read("run_forum.py")
    assert "--comment needs --by" in src, "docs require --by because run_forum.py does"


def test_readme_diagram_draws_attributed_comment_channel():
    text = _read("README.md")
    arch = text.split("## Architecture", 1)[1].split("### Round Flow", 1)[0]
    assert "Human Researcher" not in arch
    assert '--comment "Focus on X" --by <who>' in arch
    assert "orchestrating Claude session" in arch
    assert "knowledge/human_context.md" in arch


def test_readme_diagram_box_is_rectangular():
    text = _read("README.md")
    arch = text.split("## Architecture", 1)[1]
    top = next(ln for ln in arch.splitlines() if ln.startswith("  ┌"))
    box = []
    for ln in arch.splitlines()[arch.splitlines().index(top):]:
        box.append(ln)
        if ln.startswith("  └"):
            break
    assert len({len(ln) for ln in box}) == 1, "comment box lines differ in width"


# --- V-06: no clause joined by a semicolon or colon in the v2.1-edited lines ---

@pytest.mark.parametrize("prefix", [
    "| **Scout opens with one testable prediction.**",
    "| **Topic-diversity guard.**",
    "| **Research-taste labels and a bridge cap.**",
    "Chen et al.'s corpus is machine learning",   # the Caveats paragraph
    "- **Critic prompt.**",
    "- **Topic gate provenance.**",
])
def test_season2_edited_lines_join_no_clauses(prefix):
    line = _season2_line(prefix)
    # The last table cell lists file locations, not prose.
    prose = _prose(line.rsplit("|", 2)[0] if line.startswith("|") else line)
    assert ";" not in prose, f"semicolon in {prefix!r}"
    assert not CLAUSE_COLON.search(prose), f"clause-joining colon in {prefix!r}: {CLAUSE_COLON.search(prose)}"


def test_caveats_keep_season1_figures():
    # D-06 was decided on 2026-09-26. The caveat now carries the corrected count.
    caveats = _season2_line("Chen et al.'s corpus is machine learning")
    assert "72 Season 1 posts and 24 Critic verdicts" in caveats
    assert "(25% / 37.5%)" in _season2_line("| **Research-taste labels and a bridge cap.**")


# --- V-13: Critic prompt and provenance described as the code behaves ---------

def test_critic_prompt_description_matches_build_prompt():
    src = _read("run_forum.py")
    div = _read("topic_diversity.py")
    line = _season2_line("- **Critic prompt.**")
    # The code gives the Critic a round id for log_retreat ...
    if "Round id for log_retreat" in src:
        assert "log_retreat" in line and "round id" in line
        assert "no round counts" not in line
    # ... and the topic-diversity block with cosines and thresholds.
    if "Thresholds (provisional, uncalibrated)" in div:
        assert "topic-diversity check" in line and "thresholds" in line
        assert "no monitor numbers" not in line
    # What stays out of the prompt.
    for absent in ("no stop rules", "no depth rule", "no scoring cap", "entropies",
                   "the round the arc opened at"):
        assert absent in line, absent
    assert 'lines.append(f"- Arc opened at round' in src and "if not critic:" in src


def test_provenance_sentences_allow_unrecorded_legacy_entries():
    gate = _read("topic_gate.md")
    entries = re.split(r"\n## ", gate.split("## Template", 1)[1])[1:]
    legacy = [e for e in entries if not e.lstrip().startswith("<") and "drafted_by:" not in e]
    assert legacy, "topic_gate.md has legacy entries without drafted_by"
    readme = _read("README.md")
    assert "every entry records who drafted" not in readme
    assert "every new entry records who drafted and who signed it" in readme
    assert "read as unrecorded" in readme
    line = _season2_line("- **Topic gate provenance.**")
    assert line.startswith("- **Topic gate provenance.** Every new entry records")
    assert "`unrecorded`" in line
