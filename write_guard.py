#!/usr/bin/env python3
"""
External-write detector (v2.1, M03 step 1)
===========================================
Agents run with Bash, so a tool list alone cannot stop a write into a
sibling repository or the KNA data directory (the R26 Analyst edited
another repository's codebook, and a Paper E repair wrote into the data
directory). This module records, before and after each agent run and each
Rscript run, the state of every watched location:

  - watched git repositories (forum_config.watched_repos, default the
    sibling checkouts ../kna and ../kr-hearings-data): HEAD, the sha256 of
    `git diff HEAD` and a size/mtime stat of untracked files. This works on
    repositories that are already dirty.
  - data directories ($KBL_DATA, plus forum_config.watched_data): a
    size/mtime manifest of every file.

Any difference is reported and written to logs/external_writes/<run_id>.patch.
Nothing is reverted automatically.

Usage from code:
    before = write_guard.guard_before()
    ... run the agent or Rscript ...
    changes = write_guard.guard_after(before, run_id)   # [] when clean

Watched entries may use ~, $VARS or paths relative to the repo root, so the
public agents.json never needs an absolute path.
"""

import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_WATCHED_REPOS = ("../kna", "../kr-hearings-data")
MAX_MANIFEST_FILES = 200_000


def _config() -> dict:
    try:
        with open(BASE_DIR / "agents.json", encoding="utf-8") as f:
            return dict(json.load(f).get("forum_config", {}))
    except (OSError, json.JSONDecodeError):
        return {}


def _expand(entry: str) -> Path:
    p = Path(os.path.expandvars(os.path.expanduser(str(entry))))
    return p if p.is_absolute() else (BASE_DIR / p)


def watched_repos(cfg: dict | None = None) -> list[Path]:
    """Existing watched repositories, resolved. The forum repo itself is never
    watched here (staging handles it)."""
    cfg = cfg if cfg is not None else _config()
    entries = cfg.get("watched_repos") or list(DEFAULT_WATCHED_REPOS)
    out = []
    for e in entries:
        p = _expand(e)
        if p.is_dir():
            r = p.resolve()
            if r != BASE_DIR.resolve() and r not in out:
                out.append(r)
    return out


def watched_data(cfg: dict | None = None) -> list[Path]:
    """Data directories to manifest: $KBL_DATA and forum_config.watched_data."""
    cfg = cfg if cfg is not None else _config()
    entries = list(cfg.get("watched_data") or [])
    if os.environ.get("KBL_DATA"):
        entries.insert(0, os.environ["KBL_DATA"])
    out = []
    for e in entries:
        p = _expand(e)
        if p.is_dir():
            r = p.resolve()
            if r not in out:
                out.append(r)
    return out


def _git(repo: Path, *args: str) -> bytes | None:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def _stat(p: Path) -> list[int] | None:
    try:
        st = p.stat()
    except OSError:
        return None
    return [st.st_size, st.st_mtime_ns]


def repo_state(repo: Path) -> dict:
    """HEAD, hash of the tracked diff, and untracked-file stats of one repo."""
    head = _git(repo, "rev-parse", "HEAD")
    if head is None and _git(repo, "rev-parse", "--git-dir") is None:
        return {"path": str(repo), "is_git": False, "files": tree_manifest(repo)}
    diff = _git(repo, "diff", "HEAD", "--binary") or b""
    untracked = {}
    listing = _git(repo, "ls-files", "-z", "--others", "--exclude-standard") or b""
    for rel in listing.decode("utf-8", errors="replace").split("\0"):
        if rel:
            untracked[rel] = _stat(repo / rel)
    return {
        "path": str(repo),
        "is_git": True,
        "head": head.decode().strip() if head else None,
        "diff_sha256": hashlib.sha256(diff).hexdigest(),
        "untracked": untracked,
    }


def tree_manifest(root: Path) -> dict:
    """{relative path: [size, mtime_ns]} for every file under root."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for name in filenames:
            p = Path(dirpath) / name
            out[str(p.relative_to(root))] = _stat(p)
            if len(out) >= MAX_MANIFEST_FILES:
                return out
    return out


def snapshot(repos: list[Path] | None = None, data: list[Path] | None = None) -> dict:
    """State of every watched location."""
    repos = watched_repos() if repos is None else [Path(r) for r in repos]
    data = watched_data() if data is None else [Path(d) for d in data]
    return {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "repos": {str(r): repo_state(r) for r in repos},
        "data": {str(d): tree_manifest(d) for d in data},
    }


def _manifest_changes(where: str, kind: str, before: dict, after: dict) -> list[dict]:
    changes = []
    for rel in sorted(set(before) | set(after)):
        if rel not in before:
            changes.append({"where": where, "kind": f"{kind}_added", "path": rel})
        elif rel not in after:
            changes.append({"where": where, "kind": f"{kind}_removed", "path": rel})
        elif before[rel] != after[rel]:
            changes.append({"where": where, "kind": f"{kind}_modified", "path": rel})
    return changes


def compare(before: dict, after: dict) -> list[dict]:
    """Differences between two snapshots, one dict per change."""
    changes = []
    for repo, b in (before.get("repos") or {}).items():
        a = (after.get("repos") or {}).get(repo)
        if a is None:
            changes.append({"where": repo, "kind": "repo_missing", "path": ""})
            continue
        if not b.get("is_git"):
            changes += _manifest_changes(repo, "file", b.get("files") or {}, a.get("files") or {})
            continue
        if b.get("head") != a.get("head"):
            changes.append({"where": repo, "kind": "head_moved", "path": "",
                            "detail": f"{b.get('head')} -> {a.get('head')}"})
        if b.get("diff_sha256") != a.get("diff_sha256"):
            changes.append({"where": repo, "kind": "tracked_diff_changed", "path": ""})
        changes += _manifest_changes(repo, "untracked", b.get("untracked") or {}, a.get("untracked") or {})
    for d, b in (before.get("data") or {}).items():
        a = (after.get("data") or {}).get(d, {})
        changes += _manifest_changes(d, "data", b, a)
    return changes


def write_patch(run_id: str, changes: list[dict], after: dict | None = None) -> Path:
    """logs/external_writes/<run_id>.patch: the change list, then the current
    `git diff HEAD` and status of every repo that changed. Private (logs/)."""
    out_dir = BASE_DIR / "logs" / "external_writes"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run_id}.patch"
    lines = [f"# External writes detected for run {run_id} at {datetime.now().isoformat(timespec='seconds')}",
             "# Nothing was reverted. Review and restore by hand.", ""]
    for c in changes:
        detail = f" ({c['detail']})" if c.get("detail") else ""
        lines.append(f"# {c['kind']}: {c['where']} {c.get('path', '')}{detail}".rstrip())
    lines.append("")
    repos_changed = []
    for c in changes:
        if c["where"] not in repos_changed and (after or {}).get("repos", {}).get(c["where"], {}).get("is_git"):
            repos_changed.append(c["where"])
    for repo in repos_changed:
        lines.append(f"### git status --porcelain ({repo})")
        lines.append((_git(Path(repo), "status", "--porcelain") or b"").decode("utf-8", errors="replace"))
        lines.append(f"### git diff HEAD ({repo})")
        lines.append((_git(Path(repo), "diff", "HEAD") or b"").decode("utf-8", errors="replace"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _location_label(where: str, cfg: dict) -> str:
    """A watched location as it may appear in tracked files: the configured
    watched_repos or watched_data entry (for example ../kna), $KBL_DATA for
    the data directory, a repo-relative path, else the folder name."""
    try:
        r = Path(where).resolve()
    except (OSError, ValueError):
        return Path(str(where)).name
    if os.environ.get("KBL_DATA") and _expand(os.environ["KBL_DATA"]).resolve() == r:
        return "$KBL_DATA"
    for e in list(cfg.get("watched_repos") or DEFAULT_WATCHED_REPOS) + list(cfg.get("watched_data") or []):
        try:
            if _expand(e).resolve() == r:
                return str(e)
        except (OSError, ValueError):
            continue
    try:
        return r.relative_to(BASE_DIR.resolve()).as_posix()
    except ValueError:
        return r.name


def public_changes(changes: list[dict], cfg: dict | None = None) -> list[dict]:
    """Change entries with no absolute machine path, for the tracked
    knowledge/arc_status.json. The private patch file keeps the full detail."""
    cfg = cfg if cfg is not None else _config()
    out = []
    for c in changes or []:
        item = {k: c.get(k) for k in ("kind", "path") if c.get(k) is not None}
        item["where"] = _location_label(str(c.get("where") or ""), cfg)
        if c.get("patch"):
            item["patch"] = f"logs/external_writes/{Path(str(c['patch'])).name}"
        out.append(item)
    return out


def guard_before() -> dict:
    """Baseline before an agent run or an Rscript run."""
    return snapshot()


def guard_after(before: dict, run_id: str) -> list[dict]:
    """Compare with the baseline. On any change, write the patch file and
    return the change list (each entry also names the patch). [] when clean."""
    repos = [Path(r) for r in (before.get("repos") or {})]
    data = [Path(d) for d in (before.get("data") or {})]
    after = snapshot(repos=repos, data=data)
    changes = compare(before, after)
    if changes:
        patch = write_patch(run_id, changes, after)
        for c in changes:
            c["patch"] = str(patch)
    return changes
