"""Round and arc identity (M12): frontmatter read and line-level write, the
legacy mapping for posts 001-090 checked against the real forum/ directory
(read-only), and the resume plan for an incomplete round."""

import json
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import forum_index as fi  # noqa: E402

REAL_FORUM = ROOT / "forum"
SCOUT, ANALYST, CRITIC = fi.ROLE_ORDER

KEYS = {
    "round": 31,
    "arc": 6,
    "role": "critic",
    "run_id": "r31_critic_20260925T120000_ab12cd",
    "model": "claude-opus-5-5",
    "models_used": ["claude-opus-5-5"],
    "claude_code_version": "2.1.282",
    "effort": "high",
    "num_turns": 57,
    "terminal_reason": None,
    "attempt": 1,
}


def _legacy_real_posts() -> list[Path]:
    posts = [p for p in fi.all_posts(forum_dir=REAL_FORUM)
             if fi._post_num(p) <= fi.LEGACY_LAST_POST]
    if len(posts) < fi.LEGACY_LAST_POST:
        pytest.skip("real forum/ does not hold the 90 legacy posts")
    return posts


def _post(d: Path, n: int, role: str, fm: dict | None = None, body: str = "") -> Path:
    """A minimal post with the fm keys written into its first --- block."""
    d.mkdir(parents=True, exist_ok=True)
    head = ["---", 'author: "test"', 'date: "2026-09-25 12:00"', f"type: [{role}]"]
    for k, v in (fm or {}).items():
        head.append(f"{k}: {fi._dump_value(v)}")
    head.append("---")
    p = d / f"{n:03d}_{role}.md"
    p.write_text("\n".join(head) + f"\n\n# Post {n}\n\n{body}\n", encoding="utf-8")
    return p


def _legacy_forum(d: Path, last: int) -> Path:
    """Posts 001..last on the legacy triple grid, no orchestrator keys."""
    for n in range(1, last + 1):
        _post(d, n, fi.ROLE_ORDER[(n - 1) % 3])
    return d


# ---------------------------------------------------------------------------
# Legacy mapping against the real forum (read-only)
# ---------------------------------------------------------------------------

def test_real_forum_legacy_mapping_all_90_posts():
    posts = _legacy_real_posts()
    assert [fi._post_num(p) for p in posts] == list(range(1, 91))
    for p in posts:
        n = fi._post_num(p)
        meta = fi.post_meta(p)
        assert set(meta) >= {"path", "post_num", "round", "arc", "role", "legacy"}
        assert meta["legacy"] is True and meta["source"] == "legacy", p.name
        assert meta["post_num"] == n
        assert meta["round"] == (n - 1) // 3 + 1, p.name
        assert meta["role"] == fi.ROLE_ORDER[(n - 1) % 3], p.name
        assert p.name == f"{n:03d}_{meta['role']}.md"
        first, last = fi.LEGACY_ARCS[meta["arc"]]
        assert first <= meta["round"] <= last, p.name

    by_name = {p.name: fi.post_meta(p) for p in posts}
    assert by_name["090_critic.md"]["round"] == 30
    assert by_name["073_literature_scout.md"]["round"] == 25
    expected_arcs = {
        "001_literature_scout.md": (1, 1), "039_critic.md": (13, 1),
        "040_literature_scout.md": (14, 2), "066_critic.md": (22, 2),
        "067_literature_scout.md": (23, 3), "072_critic.md": (24, 3),
        "073_literature_scout.md": (25, 4), "081_critic.md": (27, 4),
        "082_literature_scout.md": (28, 5), "090_critic.md": (30, 5),
    }
    for name, (rnd, arc) in expected_arcs.items():
        assert (by_name[name]["round"], by_name[name]["arc"]) == (rnd, arc), name


def test_real_forum_is_thirty_complete_triples():
    posts = _legacy_real_posts()
    metas = [m for m in fi.index(forum_dir=REAL_FORUM) if m["post_num"] <= 90]
    assert [m["path"] for m in metas] == posts
    rounds: dict[int, list[str]] = {}
    for m in metas:
        rounds.setdefault(m["round"], []).append(m["role"])
    assert sorted(rounds) == list(range(1, 31))
    for rnd, roles in rounds.items():
        assert roles == list(fi.ROLE_ORDER), rnd
    # The public helpers agree at every arc boundary.
    for rnd in sorted({r for span in fi.LEGACY_ARCS.values() for r in span}):
        assert fi.missing_roles(rnd, forum_dir=REAL_FORUM) == []
        assert [p.name for p in fi.round_posts(rnd, forum_dir=REAL_FORUM)] == [
            f"{3 * (rnd - 1) + i + 1:03d}_{r}.md" for i, r in enumerate(fi.ROLE_ORDER)]
    # The scan and the per-post lookup agree.
    for m in metas:
        assert fi.post_meta(m["path"]) == m


def test_real_forum_posts_carry_no_orchestrator_keys():
    for p in _legacy_real_posts():
        fm = fi.read_frontmatter(p)
        assert {"author", "date", "type", "references"} <= set(fm), p.name
        assert not set(fm) & set(fi.ORCHESTRATOR_KEYS), p.name
        assert isinstance(fm["references"], list) and fm["references"], p.name


def test_real_forum_plan_after_arc_5():
    all_real = fi.all_posts(forum_dir=REAL_FORUM)
    if len(all_real) != 90:
        pytest.skip("forum/ has moved past the frozen R30 state")
    assert fi.current_round(forum_dir=REAL_FORUM) == 30
    assert fi.next_round_plan(forum_dir=REAL_FORUM) == (31, list(fi.ROLE_ORDER))
    assert fi.next_post_number(forum_dir=REAL_FORUM) == 91


def test_arc_table_matches_arc_openers_in_forum():
    """Arcs 3-5 name themselves in the Scout post that opens them."""
    posts = {p.name: p for p in _legacy_real_posts()}
    for arc in (3, 4, 5):
        first = fi.LEGACY_ARCS[arc][0]
        opener = posts[f"{3 * (first - 1) + 1:03d}_literature_scout.md"]
        head = opener.read_text(encoding="utf-8")[:4000]
        assert re.search(rf"\bArc {arc}\b", head), opener.name
        # The round before the opener belongs to the previous arc.
        prev = posts[f"{3 * (first - 1):03d}_critic.md"]
        assert fi.post_meta(prev)["arc"] == arc - 1


def test_arc_table_matches_season1_record():
    season2 = ROOT / "SEASON2.md"
    if season2.exists():
        line = next((l for l in season2.read_text(encoding="utf-8").splitlines()
                     if "three arcs" in l), None)
        if line:
            spans = [(int(a), int(b)) for a, b in re.findall(r"R(\d+)-R(\d+)", line)]
            assert spans == [fi.LEGACY_ARCS[1], fi.LEGACY_ARCS[2], fi.LEGACY_ARCS[3]]
    archive = ROOT / "forum_archive" / "20260428_arc2_progressive_ambition"
    if archive.is_dir():
        nums = sorted(int(p.name[:3]) for p in archive.glob("[0-9][0-9][0-9]_*.md"))
        rounds = {(n - 1) // 3 + 1 for n in nums}
        assert min(rounds) == fi.LEGACY_ARCS[2][0] and max(rounds) == fi.LEGACY_ARCS[2][1]
    gate = ROOT / "topic_gate.md"
    if gate.exists():
        for rnd, arc in re.findall(r"^## R(\d+)\b.*?\bArc (\d+) opening",
                                   gate.read_text(encoding="utf-8"), flags=re.MULTILINE):
            if int(arc) in fi.LEGACY_ARCS:
                first, last = fi.LEGACY_ARCS[int(arc)]
                assert first <= int(rnd) <= last, (rnd, arc)


def test_active_arc_start_is_an_arc_boundary():
    f = ROOT / "knowledge" / "active_arc.json"
    if not f.exists():
        pytest.skip("no active arc")
    start = json.loads(f.read_text(encoding="utf-8")).get("start_round")
    if not start or start > fi.LEGACY_LAST_ROUND:
        pytest.skip("active arc is past the legacy table")
    assert fi.LEGACY_ARCS[fi._legacy_arc(start)][0] == start


# ---------------------------------------------------------------------------
# Frontmatter read
# ---------------------------------------------------------------------------

def test_read_frontmatter_real_shapes():
    posts = {p.name: p for p in _legacy_real_posts()}
    fm1 = fi.read_frontmatter(posts["001_literature_scout.md"])
    assert fm1["author"] == "Scout (Literature Tracker)"
    assert fm1["date"] == "2026-03-31 11:38"
    assert fm1["type"] == "literature_scan"
    assert fm1["references"][0] == "Seo 2025 doi:10.21487/jrm.2025.3.10.1.49"
    fm73 = fi.read_frontmatter(posts["073_literature_scout.md"])
    assert fm73["type"] == ["research_agenda", "literature_scan", "response"]
    assert fm73["references"][0] == "10.1111/lsq.12440"
    # The body's ```yaml block (round: R25 ...) never leaks into the first block.
    assert "round" not in fm73 and "topic_gate" not in fm73


def test_read_frontmatter_agrees_with_yaml_on_real_posts():
    yaml = pytest.importorskip("yaml")
    for p in _legacy_real_posts():
        text = p.read_text(encoding="utf-8")
        block = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL).group(1)
        assert fi.read_frontmatter(p) == yaml.safe_load(block), p.name


def test_read_frontmatter_edge_cases(tmp_path):
    none = tmp_path / "none.md"
    none.write_text("# Title\n\n---\nround: 5\n---\n", encoding="utf-8")
    assert fi.read_frontmatter(none) == {}
    unclosed = tmp_path / "unclosed.md"
    unclosed.write_text("---\nround: 5\n# Title\n", encoding="utf-8")
    assert fi.read_frontmatter(unclosed) == {}
    assert fi.read_frontmatter(tmp_path / "missing.md") == {}
    odd = tmp_path / "odd.md"
    odd.write_text("---\r\nround: 7  # set by orchestrator\r\nflag: true\r\nempty:\r\n"
                   "note: 'it''s'\r\nurl: https://x.org/a#b\r\n---\r\nbody\r\n",
                   encoding="utf-8")
    assert fi.read_frontmatter(odd) == {"round": 7, "flag": True, "empty": None,
                                        "note": "it's", "url": "https://x.org/a#b"}


# ---------------------------------------------------------------------------
# Frontmatter write (line-level, first block only)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["073_literature_scout.md", "090_critic.md",
                                  "001_literature_scout.md"])
def test_set_keys_leaves_agent_bytes_identical(tmp_path, name):
    src = REAL_FORUM / name
    if not src.exists():
        pytest.skip("real post missing")
    dst = tmp_path / name
    shutil.copyfile(src, dst)
    before = src.read_bytes().decode("utf-8")
    fi.set_frontmatter_keys(dst, KEYS)
    after = dst.read_bytes().decode("utf-8")

    old_lines = before.split("\n")
    close = old_lines.index("---", 1)
    new_lines = after.split("\n")
    new_close = new_lines.index("---", 1)
    # Agent frontmatter lines come first and unchanged, then the new keys.
    assert new_lines[:close] == old_lines[:close]
    assert new_lines[close:new_close] == [f"{k}: {fi._dump_value(v)}" for k, v in KEYS.items()]
    # Everything after the first block, including every body ```yaml block,
    # is byte-identical.
    assert "\n".join(new_lines[new_close:]) == "\n".join(old_lines[close:])

    fm = fi.read_frontmatter(dst)
    for k, v in KEYS.items():
        assert fm[k] == v, k
    assert fm["author"] == fi.read_frontmatter(src)["author"]

    meta = fi.post_meta(dst)
    assert (meta["round"], meta["arc"], meta["role"], meta["source"]) == (31, 6, "critic", "frontmatter")
    assert meta["legacy"] is False

    # Idempotent: the same keys again change nothing.
    fi.set_frontmatter_keys(dst, KEYS)
    assert dst.read_bytes().decode("utf-8") == after


def test_set_keys_output_is_valid_yaml_for_the_site(tmp_path):
    yaml = pytest.importorskip("yaml")
    p = _post(tmp_path, 91, SCOUT)
    fi.set_frontmatter_keys(p, dict(KEYS, run_id='a "quoted" id: with colon # and hash',
                                    terminal_reason="line1\nline2\u2028x"))
    text = p.read_text(encoding="utf-8")
    block = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL).group(1)
    loaded = yaml.safe_load(block)
    fm = fi.read_frontmatter(p)
    for k in KEYS:
        assert loaded[k] == fm[k], k
    assert fm["run_id"] == 'a "quoted" id: with colon # and hash'
    assert fm["terminal_reason"] == "line1\nline2\u2028x"


def test_set_keys_replaces_in_place_and_drops_duplicates(tmp_path):
    p = tmp_path / "091_literature_scout.md"
    p.write_text("---\nauthor: \"x\"\nround: 3\nmodels_used:\n  - old-a\n  - old-b\n"
                 "type: scan\nround: 4\n---\n\n```yaml\nround: R99\n```\n", encoding="utf-8")
    fi.set_frontmatter_keys(p, {"round": 31, "models_used": ["claude-opus-5-5"]})
    assert p.read_text(encoding="utf-8") == (
        "---\nauthor: \"x\"\nround: 31\nmodels_used: [\"claude-opus-5-5\"]\n"
        "type: scan\n---\n\n```yaml\nround: R99\n```\n")
    assert fi.read_frontmatter(p)["round"] == 31


def test_set_keys_preserves_crlf_and_inserts_missing_block(tmp_path):
    crlf = tmp_path / "091_critic.md"
    crlf.write_bytes(b"---\r\nauthor: \"x\"\r\n---\r\n\r\nbody\r\n")
    fi.set_frontmatter_keys(crlf, {"round": 31, "role": "critic"})
    assert crlf.read_bytes() == (b"---\r\nauthor: \"x\"\r\nround: 31\r\nrole: \"critic\"\r\n"
                                 b"---\r\n\r\nbody\r\n")
    bare = tmp_path / "092_critic.md"
    bare.write_text("# No frontmatter\n\n---\nkeep: me\n---\n", encoding="utf-8")
    fi.set_frontmatter_keys(bare, {"round": 31})
    assert bare.read_text(encoding="utf-8") == (
        "---\nround: 31\n---\n# No frontmatter\n\n---\nkeep: me\n---\n")
    assert fi.read_frontmatter(bare) == {"round": 31}
    with pytest.raises(ValueError):
        fi.set_frontmatter_keys(bare, {"bad key": 1})
    assert not list(tmp_path.glob(".*.tmp"))


# ---------------------------------------------------------------------------
# Rounds, missing roles, resume plan (fixture forums)
# ---------------------------------------------------------------------------

def test_empty_forum(tmp_path):
    d = tmp_path / "forum"
    assert fi.all_posts(forum_dir=d) == []
    assert fi.current_round(forum_dir=d) == 0
    assert fi.next_round_plan(forum_dir=d) == (1, list(fi.ROLE_ORDER))
    assert fi.next_post_number(forum_dir=d) == 1


def test_missing_critic_resumes_only_the_critic(tmp_path):
    """Plan test (1): posts 001-089 and no 090 plan only the Critic for R30."""
    d = _legacy_forum(tmp_path / "forum", 89)
    (d / ".gitkeep").write_text("")
    assert fi.current_round(forum_dir=d) == 30
    assert fi.missing_roles(30, forum_dir=d) == [CRITIC]
    assert fi.next_round_plan(forum_dir=d) == (30, [CRITIC])
    assert fi.next_post_number(forum_dir=d) == 90
    # Analyst-first order keeps its own sequence.
    order = (ANALYST, SCOUT, CRITIC)
    assert fi.next_round_plan(order, forum_dir=d) == (30, [CRITIC])
    _post(d, 90, CRITIC, {"round": 30, "arc": 5, "role": CRITIC})
    assert fi.next_round_plan(forum_dir=d) == (31, list(fi.ROLE_ORDER))


def test_incomplete_r28_does_not_absorb_the_next_scout(tmp_path):
    """Plan test (3): with 082 and 083 and no 084, R28 is incomplete and a
    new Scout post is not grouped into R28, keyed or not."""
    for keyed in (False, True):
        d = _legacy_forum(tmp_path / f"forum_{keyed}", 83)
        assert fi.next_round_plan(forum_dir=d) == (28, [CRITIC])
        assert [p.name for p in fi.round_posts(28, forum_dir=d)] == [
            "082_literature_scout.md", "083_data_analyst.md"]
        scout = _post(d, 84, SCOUT, {"round": 29, "arc": 5, "role": SCOUT} if keyed else None)
        meta = fi.post_meta(scout)
        assert meta["round"] == 29
        assert meta["source"] == ("frontmatter" if keyed else "inferred")
        assert meta["arc"] == 5
        assert [p.name for p in fi.round_posts(28, forum_dir=d)] == [
            "082_literature_scout.md", "083_data_analyst.md"]
        assert fi.missing_roles(28, forum_dir=d) == [CRITIC]
        assert fi.current_round(forum_dir=d) == 29
        assert fi.next_round_plan(forum_dir=d) == (29, [ANALYST, CRITIC])


def test_keyed_rounds_after_legacy(tmp_path):
    d = _legacy_forum(tmp_path / "forum", 90)
    kn = tmp_path / "knowledge"
    kn.mkdir()
    (kn / "active_arc.json").write_text(json.dumps({"arc_id": 6, "start_round": 31}))
    _post(d, 91, SCOUT, {"round": 31, "arc": 6, "role": SCOUT})
    _post(d, 92, ANALYST, {"round": 31, "arc": 6, "role": ANALYST})
    assert fi.next_round_plan(forum_dir=d) == (31, [CRITIC])
    assert fi.next_post_number(forum_dir=d) == 93
    # A crash between the agent's post and the key write leaves an unkeyed
    # Critic, which joins R31 instead of opening a phantom round.
    critic = _post(d, 93, CRITIC)
    meta = fi.post_meta(critic)
    assert (meta["round"], meta["arc"], meta["source"]) == (31, 6, "inferred")
    assert fi.next_round_plan(forum_dir=d) == (32, list(fi.ROLE_ORDER))
    # An unkeyed post opening a new round takes its arc from active_arc.json.
    scout = _post(d, 94, SCOUT)
    assert (fi.post_meta(scout)["round"], fi.post_meta(scout)["arc"]) == (32, 6)
    # A keyed post without an arc key also falls back to the active arc.
    analyst = _post(d, 95, ANALYST, {"round": 32})
    assert fi.post_meta(analyst)["arc"] == 6
    # All metas agree with the scan.
    for m in fi.index(forum_dir=d):
        assert fi.post_meta(m["path"]) == m


def test_relative_forum_dir_finds_the_active_arc(tmp_path, monkeypatch):
    d = _legacy_forum(tmp_path / "forum", 90)
    kn = tmp_path / "knowledge"
    kn.mkdir()
    (kn / "active_arc.json").write_text(json.dumps({"arc_id": "arc6", "start_round": 31}))
    _post(d, 91, SCOUT, {"round": 31})
    monkeypatch.chdir(d)
    meta = fi.post_meta(Path("091_literature_scout.md"))
    assert (meta["round"], meta["arc"]) == (31, 6)
    assert fi.round_posts(31, forum_dir=Path(".")) == [Path("091_literature_scout.md")]


def test_next_post_number_uses_the_highest_number(tmp_path):
    d = tmp_path / "forum"
    _post(d, 1, SCOUT)
    _post(d, 5, ANALYST, {"round": 1})
    (d / "notes.md").write_text("not a post")
    assert fi.next_post_number(forum_dir=d) == 6
    assert [p.name for p in fi.all_posts(forum_dir=d)] == ["001_literature_scout.md",
                                                          "005_data_analyst.md"]


def test_monkeypatched_forum_dir(tmp_path, monkeypatch):
    d = _legacy_forum(tmp_path / "forum", 4)
    monkeypatch.setattr(fi, "FORUM_DIR", d)
    assert fi.current_round() == 2
    assert fi.missing_roles(2) == [ANALYST, CRITIC]
    assert fi.next_round_plan() == (2, [ANALYST, CRITIC])
    assert fi.next_post_number() == 5
    assert [p.name for p in fi.round_posts(1)] == [
        "001_literature_scout.md", "002_data_analyst.md", "003_critic.md"]


def test_r30_failure_replay_never_repeats_a_round_role(tmp_path):
    """Plan test (4) at the index level: replay the R30 sequence (Critic
    fails, the next run resumes, a Scout later fails too). Following
    next_round_plan never assigns one role twice to a round and never
    labels two completed rounds the same."""
    d = _legacy_forum(tmp_path / "forum", 89)
    failures = {(30, CRITIC): 2, (31, SCOUT): 1}   # attempts that post nothing
    completed_labels = []
    for _ in range(12):
        rnd, roles = fi.next_round_plan(forum_dir=d)
        for role in roles:
            if failures.get((rnd, role), 0) > 0:
                failures[(rnd, role)] -= 1
                break                                # run stops, the next run resumes
            n = fi.next_post_number(forum_dir=d)
            _post(d, n, role, {"round": rnd, "role": role})
        else:
            completed_labels.append(rnd)
        if fi.current_round(forum_dir=d) >= 33 and not fi.missing_roles(33, forum_dir=d):
            break
    assert len(completed_labels) == len(set(completed_labels))
    seen = set()
    for m in fi.index(forum_dir=d):
        assert (m["round"], m["role"]) not in seen, m["path"].name
        seen.add((m["round"], m["role"]))
    for rnd in range(1, fi.current_round(forum_dir=d) + 1):
        assert fi.missing_roles(rnd, forum_dir=d) == [], rnd
    assert completed_labels[:2] == [30, 31]
