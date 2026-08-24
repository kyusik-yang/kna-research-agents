#!/usr/bin/env python3
"""Topic-diversity guard (Season 2, since 2026-08-24).

The forum's Season 1 weakness was not only the kind of idea it proposed but
how often it proposed the same one: R7-R8 re-ran the R1-R2 housing question,
and R18-R22 produced four papers from one design. This module embeds every
Scout post and every article with the same multilingual sentence model the
literature Vector DB uses, and after Scout posts it reports the nearest prior
arc post and article. Analyst and Critic see the result in their prompts;
above the block threshold Critic archives the round as a duplicate topic.

Thresholds were calibrated on Season 1 (cosine on title + opening text):
the three Arc 2 near-duplicate papers score 0.83-0.85 against each other,
the R7 housing re-run scores 0.70 against the R2 housing paper, and clearly
distinct topics score 0.33-0.66. Defaults: warn at 0.68, block at 0.80.

Usage:
    python3 topic_diversity.py check forum/073_literature_scout.md
    python3 topic_diversity.py matrix          # Season 1 article-by-article cosine
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"
ARTICLES_DIR = BASE_DIR / "articles"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
AGENTS_FILE = BASE_DIR / "agents.json"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
LOG_FILE = KNOWLEDGE_DIR / "topic_diversity.jsonl"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"   # same as tools/literature_vectordb.py

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _config() -> dict:
    try:
        with open(AGENTS_FILE) as f:
            return json.load(f).get("forum_config", {})
    except Exception:
        return {}


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.DOTALL)


def post_text(path: Path, n_chars: int = 1500) -> str:
    body = _strip_frontmatter(path.read_text(encoding="utf-8"))
    return re.sub(r"\s+", " ", body)[:n_chars]


def article_text(path: Path, n_chars: int = 1200) -> str:
    raw = path.read_text(encoding="utf-8")
    m = re.search(r'^title:\s*"?(.+?)"?\s*$', raw, re.MULTILINE)
    title = m.group(1) if m else ""
    body = _strip_frontmatter(raw)
    return title + ". " + re.sub(r"\s+", " ", body)[:n_chars]


def _round_of(post_path: Path, n_agents: int = 3) -> int:
    n = int(post_path.name[:3])
    return (n - 1) // n_agents + 1


def _article_round(path: Path) -> int:
    m = re.search(r"_r(\d+)", path.stem)
    return int(m.group(1)) if m else 0


def _arc_start(current_round: int | None = None) -> int:
    """First round of the active arc. Without an active arc (Season 1 posts,
    or a check run by hand) every earlier round counts as prior."""
    if ACTIVE_ARC_FILE.exists():
        try:
            return int(json.loads(ACTIVE_ARC_FILE.read_text()).get("start_round") or 1)
        except Exception:
            pass
    return current_round if current_round is not None else 1


def prior_corpus(current_round: int, arc_start: int) -> list[dict]:
    """Everything from BEFORE the active arc: Scout posts of earlier arcs and
    all articles drafted before this arc. Within-arc similarity is expected
    (depth first) and is not penalized."""
    items = []
    for p in sorted(FORUM_DIR.glob("*_literature_scout.md")):
        r = _round_of(p)
        if r < arc_start and r < current_round:
            items.append({"id": p.stem, "kind": "scout_post", "round": r, "text": post_text(p)})
    for a in sorted(ARTICLES_DIR.glob("2026-*_r*.md")):
        r = _article_round(a)
        if r < arc_start:
            items.append({"id": a.stem, "kind": "article", "round": r, "text": article_text(a)})
    return items


def check_post(post_path: Path, log: bool = True) -> dict:
    """Nearest prior post and article for a freshly written Scout post."""
    cfg = _config()
    warn = float(cfg.get("topic_similarity_warn", 0.68))
    block = float(cfg.get("topic_similarity_block", 0.80))
    current_round = _round_of(post_path)
    arc_start = _arc_start(current_round)
    corpus = prior_corpus(current_round, arc_start)
    result = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "post": post_path.name, "round": current_round, "arc_start": arc_start,
        "n_prior": len(corpus), "warn": warn, "block": block,
        "nearest_post": None, "nearest_article": None, "status": "clear",
    }
    if not corpus:
        result["status"] = "no_prior"
    else:
        model = _get_model()
        q = model.encode([post_text(post_path)], normalize_embeddings=True)[0]
        E = model.encode([c["text"] for c in corpus], normalize_embeddings=True)
        sims = E @ q
        best = {"scout_post": None, "article": None}
        for c, s in zip(corpus, sims):
            k = c["kind"]
            if best[k] is None or s > best[k][0]:
                best[k] = (float(s), c["id"], c["round"])
        for k, key in (("scout_post", "nearest_post"), ("article", "nearest_article")):
            if best[k]:
                result[key] = {"cosine": round(best[k][0], 3), "id": best[k][1], "round": best[k][2]}
        top = max(v[0] for v in best.values() if v)
        result["max_cosine"] = round(top, 3)
        result["status"] = "block" if top >= block else ("warn" if top >= warn else "clear")
    if log:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    return result


def latest_result(round_num: int | None = None) -> dict | None:
    if not LOG_FILE.exists():
        return None
    rows = [json.loads(l) for l in LOG_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    if round_num is not None:
        rows = [r for r in rows if r.get("round") == round_num]
    return rows[-1] if rows else None


def format_for_prompt(round_num: int | None = None) -> str:
    """Block for Analyst and Critic prompts in the same round as the Scout post."""
    r = latest_result(round_num)
    if not r or r.get("status") == "no_prior":
        return ""
    lines = ["\n## Topic Diversity Check (Season 2)\n"]
    np_, na = r.get("nearest_post"), r.get("nearest_article")
    if np_:
        lines.append(f"- Nearest prior Scout post: {np_['id']} (R{np_['round']}), cosine {np_['cosine']:.2f}")
    if na:
        lines.append(f"- Nearest prior article: {na['id']} (R{na['round']}), cosine {na['cosine']:.2f}")
    lines.append(f"- Thresholds: warn {r['warn']:.2f}, block {r['block']:.2f}. Status: **{r['status'].upper()}**")
    if r["status"] == "block":
        lines.append(
            "\nThis round's question is a restatement of a prior arc or article. Critic: verdict archive with "
            "reason \"duplicate topic\" unless Scout explicitly changed the quantity, mechanism, or population "
            "and said so. Analyst: do not build on it; test only what is genuinely new, or report the overlap."
        )
    elif r["status"] == "warn":
        lines.append(
            "\nClose to a prior topic. Critic: require Scout's post to state what is different (quantity, "
            "mechanism, population) and cap research_novelty at 2/4 if it does not."
        )
    return "\n".join(lines) + "\n"


def prior_topics_for_scout() -> str:
    """Compact list of prior arc topics so Scout can avoid them before posting."""
    arts = sorted(ARTICLES_DIR.glob("2026-*_r*.md"))
    arc_start = _arc_start()
    lines = ["\n## Topic Diversity (Season 2): questions already taken\n",
             "Your question is checked against every prior arc's Scout posts and articles after you post "
             "(cosine on the multilingual sentence model; warn 0.68, block 0.80). Restating any of these, "
             "with a new dataset or a new decade, is a duplicate. Change the quantity, the mechanism, or the population.\n"]
    for a in arts:
        if _article_round(a) < arc_start:
            m = re.search(r'^title:\s*"?(.+?)"?\s*$', a.read_text(encoding="utf-8"), re.MULTILINE)
            if m:
                lines.append(f"- R{_article_round(a)}: {m.group(1)}")
    return "\n".join(lines) + "\n"


def matrix() -> None:
    arts = sorted(ARTICLES_DIR.glob("2026-*_r*.md"))
    model = _get_model()
    E = model.encode([article_text(a) for a in arts], normalize_embeddings=True)
    S = E @ E.T
    ids = [f"r{_article_round(a)}" for a in arts]
    print("       " + " ".join(i.rjust(4) for i in ids))
    for i, r in enumerate(ids):
        print(r.rjust(6), " ".join(f"{S[i, j]:.2f}" if i != j else " -- " for j in range(len(ids))))


def main() -> None:
    ap = argparse.ArgumentParser(description="Season 2 topic-diversity guard")
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("check", help="Check one Scout post against prior arcs and articles")
    c.add_argument("post")
    c.add_argument("--no-log", action="store_true")
    sub.add_parser("matrix", help="Article-by-article cosine matrix")
    args = ap.parse_args()
    if args.cmd == "check":
        r = check_post(Path(args.post), log=not args.no_log)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.cmd == "matrix":
        matrix()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
