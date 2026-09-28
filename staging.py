#!/usr/bin/env python3
"""
Staged agent side effects (v2.1, M13)
=====================================
A failed agent run must leave no trace in the ledgers (a failed R25 Critic
run once appended two retreats without a post), and an accepted run may
only change what its role is allowed to change (an R27 rerun once rewrote
an earlier coding dictionary).

Lifecycle, driven by the orchestrator around each agent run:

    run = staging.begin(run_id, role)          # snapshot forum/ and knowledge/
    result = claude_cli.run_claude(..., extra_env=staging.env(run))
    if result.ok:
        report = staging.commit(run, post_path, allowlist)
    else:
        quarantine = staging.rollback(run, reason)

begin() copies forum/, knowledge/ (except knowledge/staging/ and
knowledge/archive/), summaries/, docs/, articles/ and the root files
topic_gate.md, agents.json and FORUM_RULES.md (everything the round and paper
commits publish) to knowledge/staging/_snapshots/<run_id>/ and takes an
external-write baseline (write_guard). Agents see KNA_RUN_ID and
KNA_STAGING_DIR=knowledge/staging/<run_id>/. Staged files there:

    retreats.jsonl        retreat rows (log_retreat writes here when staged)
    hand_coding/*.jsonl   new coding dictionaries

commit() reverts every change outside the role's allowlist (the agent's
version is kept under the staging dir), merges staged retreats, moves staged
dictionaries into knowledge/hand_coding/ (never overwriting), records
dictionary hashes and reports external writes. rollback() moves the run's
changes, including a partial post, to knowledge/staging/failed_<run_id>/
and restores the snapshot. Nothing is deleted and nothing is committed to
git. Files written outside agent runs (RESEARCHER_OWNED) are never reverted,
but any change to them during a run is reported as researcher_owned_changed,
with both versions kept under the staging dir, so the orchestrator can stop
the arc. recover() rolls back a run whose process died before commit or
rollback, from its leftover snapshot.
"""

import fnmatch
import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SNAPSHOT_ROOTS = ("forum", "knowledge", "summaries", "docs", "articles")
# Root files no agent run may change (published by the round commits).
SNAPSHOT_FILES = ("topic_gate.md", "agents.json", "FORUM_RULES.md")
EXCLUDED_PREFIXES = ("knowledge/staging/", "knowledge/archive/")
SKIP_NAMES = {"__pycache__", ".DS_Store"}
# Files written outside agent runs, by the researcher or the orchestrating
# session (notes, waivers, gate entries and candidates, and the files the open
# decisions ask the researcher to edit). They are never reverted, because a
# change during a run may be the researcher's own edit. Every such change is
# reported (researcher_owned_changed) and the orchestrator stops the arc until
# someone acknowledges it.
RESEARCHER_OWNED = (
    "knowledge/human_context.md",
    "knowledge/waivers.jsonl",
    "knowledge/gate_candidates.jsonl",
    "topic_gate.md",
    "knowledge/party_blocs.csv",
    "knowledge/diversity_calibration.jsonl",
    "knowledge/critic_calibration/researcher_labels.jsonl",
)
HAND_CODING = "knowledge/hand_coding/"

DOI_RE = re.compile(r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/\S+)$", re.IGNORECASE)
PRECHECK_RE = re.compile(r"^precheck:(R-\d{2})$", re.IGNORECASE)
POST_LINE_RE = re.compile(r"^(?:forum/)?(\d{3})(?:_[A-Za-z_]+\.md)?:(\d+)(?:-(\d+))?$")
LINE_SUFFIX_RE = re.compile(r":(\d+)(?:-(\d+))?$")


@dataclass
class StagingRun:
    run_id: str
    role: str
    staging_dir: Path
    snapshot_dir: Path
    manifest: dict = field(default_factory=dict)       # repo-relative path -> sha256 at begin
    guard_baseline: dict | None = None                  # write_guard snapshot
    started: str = ""


def _staging_root() -> Path:
    return BASE_DIR / "knowledge" / "staging"


def _rel(p: Path) -> str:
    p = Path(p)
    if not p.is_absolute():
        p = BASE_DIR / p
    return p.resolve().relative_to(BASE_DIR.resolve()).as_posix()


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _tracked_files() -> dict:
    """{repo-relative posix path: sha256} for the snapshot roots and files."""
    out = {}
    for name in SNAPSHOT_FILES:
        p = BASE_DIR / name
        if p.is_file():
            out[name] = _sha256(p)
    for root in SNAPSHOT_ROOTS:
        base = BASE_DIR / root
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or any(part in SKIP_NAMES for part in p.parts):
                continue
            rel = p.relative_to(BASE_DIR).as_posix()
            if rel.startswith(EXCLUDED_PREFIXES):
                continue
            out[rel] = _sha256(p)
    return out


def _changes(run: StagingRun) -> list[tuple[str, str]]:
    """[(rel, 'added'|'modified'|'deleted')] since begin()."""
    now = _tracked_files()
    out = []
    for rel in sorted(set(run.manifest) | set(now)):
        if rel not in run.manifest:
            out.append((rel, "added"))
        elif rel not in now:
            out.append((rel, "deleted"))
        elif run.manifest[rel] != now[rel]:
            out.append((rel, "modified"))
    return out


def _guard_snapshot() -> dict | None:
    try:
        import write_guard
        return write_guard.guard_before()
    except Exception as e:  # the guard must never block a run
        print(f"  [staging] write_guard baseline unavailable: {e}")
        return None


def _guard_after(run: StagingRun) -> list[dict]:
    if run.guard_baseline is None:
        return []
    try:
        import write_guard
        return write_guard.guard_after(run.guard_baseline, run.run_id)
    except Exception as e:
        print(f"  [staging] write_guard check failed: {e}")
        return [{"where": "write_guard", "kind": "check_failed", "path": "", "detail": str(e)}]


def _record_containment(run_id: str, report: dict) -> None:
    try:
        import claude_cli
        claude_cli.update_sidecar(run_id, containment=report)
    except Exception:
        pass


def begin(run_id: str, role: str) -> StagingRun:
    """Snapshot forum/ and knowledge/ and take the external-write baseline."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", run_id):
        raise ValueError(f"run id {run_id!r} is not filesystem-safe")
    staging_dir = _staging_root() / run_id
    snapshot_dir = _staging_root() / "_snapshots" / run_id
    if snapshot_dir.exists():
        raise FileExistsError(f"staging snapshot for {run_id} already exists: {snapshot_dir}")
    staging_dir.mkdir(parents=True, exist_ok=True)
    (staging_dir / "hand_coding").mkdir(exist_ok=True)
    manifest = _tracked_files()
    for rel in manifest:
        dest = snapshot_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BASE_DIR / rel, dest)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now().isoformat(timespec="seconds")
    # Written last: recover() trusts a snapshot only when this record exists.
    (staging_dir / "SNAPSHOT.json").write_text(json.dumps(
        {"run_id": run_id, "role": role, "started": started, "manifest": manifest},
        ensure_ascii=False), encoding="utf-8")
    return StagingRun(run_id=run_id, role=role, staging_dir=staging_dir, snapshot_dir=snapshot_dir,
                      manifest=manifest, guard_baseline=_guard_snapshot(), started=started)


def env(run: StagingRun) -> dict:
    """Environment for the agent subprocess (pass as run_claude extra_env)."""
    return {"KNA_RUN_ID": run.run_id, "KNA_STAGING_DIR": str(run.staging_dir)}


def _restore(run: StagingRun, rel: str) -> None:
    src = run.snapshot_dir / rel
    dest = BASE_DIR / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _keep_copy(src: Path, dest_root: Path, rel: str, move: bool) -> Path:
    """Copy (or move) the agent's version of a file under dest_root/rel."""
    dest = dest_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if move:
        shutil.move(str(src), str(dest))
    else:
        shutil.copy2(src, dest)
    return dest


def _allowed(rel: str, patterns: list[str], run: StagingRun, post_rel: str | None) -> bool:
    if post_rel and rel == post_rel:
        return True
    for pat in patterns:
        pat = pat.replace("{run_id}", run.run_id).replace("{post}", post_rel or "")
        if fnmatch.fnmatchcase(rel, pat):
            return True
    return False


def _next_rev(target: Path) -> Path:
    """round_25.jsonl -> round_25.rev<k>.jsonl with the first free k."""
    k = 1
    while True:
        cand = target.with_name(f"{target.stem}.rev{k}{target.suffix}")
        if not cand.exists():
            return cand
        k += 1


def _hashes_file() -> Path:
    return BASE_DIR / "knowledge" / "hand_coding" / "HASHES.json"


def _record_hash(path: Path, run_id: str) -> None:
    """Record a dictionary's sha256 at creation. Existing entries are never
    overwritten, so a later edit shows up as a hash mismatch."""
    hf = _hashes_file()
    try:
        data = json.loads(hf.read_text(encoding="utf-8")) if hf.exists() else {}
    except json.JSONDecodeError:
        data = {}
    name = path.name
    if name in data:
        return
    data[name] = {"sha256": _sha256(path), "created": datetime.now().isoformat(timespec="seconds"),
                  "run_id": run_id}
    hf.parent.mkdir(parents=True, exist_ok=True)
    hf.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_dictionary(rel: str) -> bool:
    return rel.startswith(HAND_CODING) and rel.endswith(".jsonl")


def _post_line_ok(num: str, line: int, post_path: Path | None) -> bool:
    candidates = sorted((BASE_DIR / "forum").glob(f"{num}_*.md"))
    if post_path is not None and Path(post_path).name.startswith(f"{num}_"):
        candidates.append(Path(post_path))
    for c in candidates:
        try:
            if len(c.read_text(encoding="utf-8").splitlines()) >= line:
                return True
        except OSError:
            continue
    return False


def _run_round(run: StagingRun | None) -> int | None:
    m = re.match(r"r(\d+)_", run.run_id) if run is not None else None
    return int(m.group(1)) if m else None


def _precheck_ok(rule_id: str, run: StagingRun | None) -> bool:
    """A precheck id names a rule result that exists in
    knowledge/prechecks/R<NN>.json (the run's round when its id carries one).
    Stage 1 runs no prechecks, so no precheck id resolves there."""
    d = BASE_DIR / "knowledge" / "prechecks"
    files = sorted(d.glob("R*.json")) if d.exists() else []
    rnd = _run_round(run)
    if rnd is not None:
        files = [f for f in files if f.stem == f"R{rnd:02d}"]
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for res in (data.get("posts") or {}).values():
            if any(str(r.get("id", "")).upper() == rule_id.upper() for r in res.get("rules") or []):
                return True
    return False


def _doi_ok(doi: str) -> bool:
    """A DOI resolves when Crossref or OpenAlex knows it (prechecks.resolve_doi,
    answers cached in the prechecks DOI cache). An unknown DOI, or one that
    could not be checked, is rejected. The rejected retreat is kept in the
    staging dir."""
    cache_path = BASE_DIR / "logs" / "doi_cache.json"
    try:
        import prechecks
        cache = prechecks.load_doi_cache(cache_path)
        rec = prechecks.resolve_doi(doi, cache)
        try:
            prechecks.save_doi_cache(cache, cache_path)
        except OSError:
            pass
    except Exception:
        return False
    return rec.get("found") is True


def _inside(p: Path, roots: list[Path]) -> bool:
    try:
        rp = p.resolve()
    except (OSError, ValueError):
        return False
    for r in roots:
        try:
            rp.relative_to(r.resolve())
            return True
        except ValueError:
            continue
    return False


def evidence_resolves(evidence, run: StagingRun | None = None, post_path: Path | None = None) -> bool:
    """True if new_evidence names something checkable: an existing output
    file inside the repository (workspace/ included) or the run's staging dir,
    a precheck id (precheck:R-NN) whose result exists, a post line reference
    (NNN:LL) or a DOI that Crossref or OpenAlex knows. Directories, paths
    outside the repository and bare tokens do not resolve. A list resolves if
    any item does."""
    if isinstance(evidence, (list, tuple)):
        return any(evidence_resolves(e, run, post_path) for e in evidence)
    if not isinstance(evidence, str) or not evidence.strip():
        return False
    ev = evidence.strip()
    m = PRECHECK_RE.match(ev)
    if m:
        return _precheck_ok(m.group(1), run)
    m = DOI_RE.match(ev)
    if m:
        return _doi_ok(m.group(1).rstrip(".,;)]}"))
    m = POST_LINE_RE.match(ev)
    if m:
        return _post_line_ok(m.group(1), int(m.group(3) or m.group(2)), post_path)
    path_part = LINE_SUFFIX_RE.sub("", ev)
    roots = [BASE_DIR] + ([run.staging_dir] if run is not None else [])
    bases = [BASE_DIR, BASE_DIR / "workspace"] + ([run.staging_dir] if run is not None else [])
    p = Path(os.path.expandvars(path_part)).expanduser()
    cands = [p] if p.is_absolute() else [b / p for b in bases]
    return any(c.is_file() and _inside(c, roots) for c in cands)


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _merge_retreats(run: StagingRun, post_path: Path | None) -> tuple[int, list[dict]]:
    staged = _read_jsonl(run.staging_dir / "retreats.jsonl")
    if not staged:
        return 0, []
    ledger = BASE_DIR / "knowledge" / "retreats.jsonl"
    seen = {(r.get("run_id"), (r.get("finding") or "").strip()) for r in _read_jsonl(ledger)}
    merged, rejected = [], []
    for row in staged:
        row = dict(row)
        row["run_id"] = run.run_id
        key = (run.run_id, (row.get("finding") or "").strip())
        if key in seen:
            continue
        if not evidence_resolves(row.get("new_evidence"), run, post_path):
            rejected.append({**row, "rejected": "new_evidence does not resolve"})
            continue
        row.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
        seen.add(key)
        merged.append(row)
    if merged:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger, "a", encoding="utf-8") as f:
            for row in merged:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if rejected:
        with open(run.staging_dir / "retreats_rejected.jsonl", "a", encoding="utf-8") as f:
            for row in rejected:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(merged), rejected


def _move_dictionaries(run: StagingRun, allowlist: list[str], post_rel: str | None,
                       violations: list[dict], to_hash: list[Path]) -> list[str]:
    """Move staged dictionaries into knowledge/hand_coding/. A name that
    already exists is saved as a rev file, never overwritten. A dictionary
    the role may not write stays in the staging dir."""
    moved = []
    src_dir = run.staging_dir / "hand_coding"
    if not src_dir.exists():
        return moved
    dest_dir = BASE_DIR / HAND_CODING
    for src in sorted(src_dir.glob("*.jsonl")):
        target = dest_dir / src.name
        if not _allowed(_rel(target), allowlist, run, post_rel):
            violations.append({"path": _rel(target), "change": "staged_dictionary",
                               "action": "left in staging (not in allowlist)"})
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        if target.exists():
            rev = _next_rev(target)
            shutil.move(str(src), str(rev))
            violations.append({"path": _rel(target), "change": "rewrite_existing_dictionary",
                               "action": f"kept original, staged version saved as {rev.name}"})
            target = rev
        else:
            shutil.move(str(src), str(target))
        to_hash.append(target)
        moved.append(_rel(target))
    return moved


def _note_researcher_owned(run: StagingRun, rel: str, change: str, dest_root: Path) -> dict:
    """Keep a researcher-owned file as it is now, and save the version from
    the start of the run and the current version under dest_root, so whoever
    acknowledges the stop can compare them."""
    before = run.snapshot_dir / rel
    after = BASE_DIR / rel
    if before.exists():
        _keep_copy(before, dest_root / "before", rel, move=False)
    if after.exists():
        _keep_copy(after, dest_root / "after", rel, move=False)
    # saved (repo-relative) is where run_arc --researcher-files restore finds
    # the start version.
    return {"path": rel, "change": change, "saved": _rel(dest_root),
            "action": "kept (never reverted), start and end versions saved in the staging dir"}


def commit(run: StagingRun, post_path: Path, allowlist: list[str]) -> dict:
    """Accept a successful run. allowlist holds glob patterns relative to the
    repo root ({run_id} and {post} are expanded). The post path is always
    allowed. Returns {"violations", "retreats_merged", "dictionaries",
    "external_writes", "retreats_rejected", "reverted_dir",
    "researcher_owned_changed"}."""
    post_rel = _rel(post_path) if post_path else None
    reverted_dir = run.staging_dir / "reverted"
    violations: list[dict] = []
    owned_changed: list[dict] = []
    dictionaries: list[str] = []
    to_hash: list[Path] = []   # recorded after every revert, so a restored HASHES.json keeps them

    for rel, change in _changes(run):
        if rel in RESEARCHER_OWNED:
            owned_changed.append(_note_researcher_owned(run, rel, change, run.staging_dir / "researcher_owned"))
            continue
        current = BASE_DIR / rel
        if _is_dictionary(rel) and change != "added" and rel != post_rel:
            # Existing dictionaries are append-never-rewrite: keep the
            # original and save the agent's version as a rev file.
            if change == "modified":
                rev = _next_rev(current)
                shutil.copy2(current, rev)
                _restore(run, rel)
                to_hash.append(rev)
                dictionaries.append(_rel(rev))
                violations.append({"path": rel, "change": "rewrite_existing_dictionary",
                                   "action": f"restored original, agent version saved as {rev.name}"})
            else:
                _restore(run, rel)
                violations.append({"path": rel, "change": change, "action": "restored"})
            continue
        if _allowed(rel, allowlist or [], run, post_rel):
            if _is_dictionary(rel) and change == "added":
                to_hash.append(current)
                dictionaries.append(rel)
            continue
        if change == "added":
            _keep_copy(current, reverted_dir, rel, move=True)
            action = "moved out (not in allowlist)"
        elif change == "modified":
            _keep_copy(current, reverted_dir, rel, move=False)
            _restore(run, rel)
            action = "restored (not in allowlist)"
        else:
            _restore(run, rel)
            action = "restored deleted file (not in allowlist)"
        violations.append({"path": rel, "change": change, "action": action})

    merged, rejected = _merge_retreats(run, post_path)
    dictionaries += _move_dictionaries(run, allowlist or [], post_rel, violations, to_hash)
    for p in to_hash:
        _record_hash(p, run.run_id)
    report = {
        "violations": violations,
        "retreats_merged": merged,
        "dictionaries": dictionaries,
        "external_writes": _guard_after(run),
        "retreats_rejected": rejected,
        "reverted_dir": str(reverted_dir) if reverted_dir.exists() else None,
        "researcher_owned_changed": owned_changed,
    }
    if owned_changed:
        print(f"  [staging] WARNING: {len(owned_changed)} researcher-owned file(s) changed during run "
              f"{run.run_id}: {', '.join(c['path'] for c in owned_changed)}")
    (run.staging_dir / "COMMIT.json").write_text(
        json.dumps({"run_id": run.run_id, "role": run.role, "post": post_rel,
                    "ts": datetime.now().isoformat(timespec="seconds"), **report},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    _record_containment(run.run_id, report)
    shutil.rmtree(run.snapshot_dir, ignore_errors=True)
    return report


def rollback(run: StagingRun, reason: str) -> Path:
    """Quarantine everything the failed run changed (including a partial
    post) to knowledge/staging/failed_<run_id>/ and restore the snapshot.
    Nothing is deleted. Researcher-owned files are left as they are."""
    quarantine = _staging_root() / f"failed_{run.run_id}"
    quarantine.mkdir(parents=True, exist_ok=True)
    changes = []
    owned_changed = []
    for rel, change in _changes(run):
        if rel in RESEARCHER_OWNED:
            owned_changed.append(_note_researcher_owned(run, rel, change, quarantine / "researcher_owned"))
            continue
        current = BASE_DIR / rel
        if change == "added":
            _keep_copy(current, quarantine / "tree", rel, move=True)
        elif change == "modified":
            _keep_copy(current, quarantine / "tree", rel, move=False)
            _restore(run, rel)
        else:
            _restore(run, rel)
        changes.append({"path": rel, "change": change})
    staged = [p for p in run.staging_dir.rglob("*") if p.is_file()] if run.staging_dir.exists() else []
    for p in staged:
        rel = p.relative_to(run.staging_dir).as_posix()
        _keep_copy(p, quarantine / "staged", rel, move=True)
    report = {
        "run_id": run.run_id, "role": run.role, "reason": reason,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "changes": changes,
        "staged_files": [p.relative_to(run.staging_dir).as_posix() for p in staged],
        "external_writes": _guard_after(run),
        "researcher_owned_changed": owned_changed,
    }
    (quarantine / "ROLLBACK.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    _record_containment(run.run_id, {"rolled_back": True, "quarantine": str(quarantine), **report})
    shutil.rmtree(run.snapshot_dir, ignore_errors=True)
    return quarantine


def rollback_report(quarantine: Path | None) -> dict:
    """The ROLLBACK.json that rollback() wrote into a quarantine folder."""
    try:
        return json.loads((Path(quarantine) / "ROLLBACK.json").read_text(encoding="utf-8"))
    except (TypeError, OSError, json.JSONDecodeError):
        return {}


def leftover_snapshots() -> list[str]:
    """Run ids whose snapshot is still in place (the run never reached
    commit or rollback)."""
    d = _staging_root() / "_snapshots"
    return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.exists() else []


def recover(run_id: str, role: str = "unknown") -> Path:
    """Roll back a run whose process stopped before commit or rollback (a
    killed process, a machine that slept). The leftover snapshot is the
    run's starting state, so everything that differs from it now is the
    run's partial work. It is quarantined to knowledge/staging/failed_<run_id>/
    and the snapshot restored, as rollback() does for a failed run. The
    caller makes sure the run is not still in progress."""
    snapshot_dir = _staging_root() / "_snapshots" / run_id
    staging_dir = _staging_root() / run_id
    if not snapshot_dir.is_dir():
        raise FileNotFoundError(f"no snapshot for run {run_id}")
    # begin() writes SNAPSHOT.json after the copy, so a snapshot without it
    # (or with a file missing) is incomplete, and restoring from it could
    # move good files out. That case is left to a person.
    try:
        rec = json.loads((staging_dir / "SNAPSHOT.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise FileNotFoundError(f"snapshot of run {run_id} has no SNAPSHOT.json record (incomplete)")
    manifest = rec.get("manifest") or {}
    missing = [rel for rel in manifest if not (snapshot_dir / rel).is_file()]
    if not manifest or missing:
        raise FileNotFoundError(f"snapshot of run {run_id} is incomplete ({len(missing)} file(s) missing)")
    run = StagingRun(run_id=run_id, role=rec.get("role") or role, staging_dir=staging_dir,
                     snapshot_dir=snapshot_dir, manifest=manifest, guard_baseline=None,
                     started=rec.get("started") or "unknown")
    return rollback(run, "recovered: the run's process stopped before its staging commit or rollback")
