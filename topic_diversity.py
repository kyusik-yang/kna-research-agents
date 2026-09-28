#!/usr/bin/env python3
"""Topic-diversity guard (Season 2, rebuilt 2026-09-25).

The forum's Season 1 weakness was not only the kind of idea it proposed but
how often it proposed the same one: R7-R8 re-ran the R1-R2 housing question,
and R18-R22 produced four papers from one design. After a Scout post this
module reports the nearest prior-arc Scout post and paper.

What is embedded (v2):
- Scout posts: only the "Prediction to Test" and "Gap Type" sections, plus the
  card's quantity, population, comparison and outcome when a ```card block is
  present. Frontmatter, fenced code blocks and topic_gate lines are removed.
  Season 1 posts, which have neither section, use the body without code
  blocks, first 4,000 characters.
- Papers: title, abstract and Introduction of articles/*.tex, LaTeX stripped.

The v1 guard embedded roughly the title and a boilerplate YAML header (the
MiniLM model truncates at 128 tokens) and compared against .md stubs, so the
Season 1 repeats it was built for scored below its warn value.

Model: forum_config.diversity_model, default nlpai-lab/KURE-v1 (8,192 tokens).
Thresholds: forum_config.topic_similarity_warn / topic_similarity_block. They
are provisional until the researcher approves values proposed by
calibrate_diversity.py (knowledge/diversity_calibration.jsonl). The module
defaults (0.68 / 0.80) were set for the v1 MiniLM guard and are not
calibrated for this model.

Structured duplicate check (active only when forum_config.stage2.prediction_cards
is true): the card's outcome, population and comparison are compared with
every card from before the active arc by normalized string match, and an
exact match blocks regardless of cosine.

Usage:
    python3 topic_diversity.py check forum/073_literature_scout.md [--no-log]
    python3 topic_diversity.py text forum/073_literature_scout.md    # show the embedded text
    python3 topic_diversity.py matrix                                # paper-by-paper cosine
"""

import argparse
import hashlib
import json
import os
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
CARDS_DIR = KNOWLEDGE_DIR / "prediction_cards"
LOG_FILE = KNOWLEDGE_DIR / "topic_diversity.jsonl"
# Private runtime cache (logs/ is gitignored). None disables it.
EMBED_CACHE_DIR: Path | None = BASE_DIR / "logs" / "embedding_cache"

MODEL_DEFAULT = "nlpai-lab/KURE-v1"
MAX_SEQ_LENGTH = 8192
TEXT_VERSION = "v2"             # bump when post_text or article_text changes
# v1 (MiniLM) values, kept only as a fallback. Not calibrated for KURE-v1.
DEFAULT_WARN = 0.68
DEFAULT_BLOCK = 0.80
FALLBACK_CHARS = 4000
MAX_TEXT_CHARS = 20000          # safety cap on any embedded text
SECTION_KEYS = ("prediction to test", "gap type")
CARD_FIELDS = ("quantity", "population", "comparison", "outcome")
STRUCTURED_FIELDS = ("outcome", "population", "comparison")

_models: dict = {}
_memo: dict = {}


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

def _config() -> dict:
    try:
        with open(AGENTS_FILE) as f:
            return json.load(f).get("forum_config", {})
    except Exception:
        return {}


def model_name(cfg: dict | None = None) -> str:
    cfg = _config() if cfg is None else cfg
    return cfg.get("diversity_model") or MODEL_DEFAULT


def thresholds(cfg: dict | None = None) -> tuple[float, float, str]:
    """(warn, block, source). source is 'forum_config' or 'module_default'."""
    cfg = _config() if cfg is None else cfg
    if "topic_similarity_warn" in cfg and "topic_similarity_block" in cfg:
        return float(cfg["topic_similarity_warn"]), float(cfg["topic_similarity_block"]), "forum_config"
    return DEFAULT_WARN, DEFAULT_BLOCK, "module_default"


def _stage2(cfg: dict, key: str) -> bool:
    return bool((cfg.get("stage2") or {}).get(key, False))


# --------------------------------------------------------------------------
# Embedding
# --------------------------------------------------------------------------

def _device() -> str | None:
    """KNA_EMBED_DEVICE (cpu, mps, cuda) or None for the library's choice."""
    return os.environ.get("KNA_EMBED_DEVICE") or None


def _get_model(name: str | None = None):
    name = name or model_name()
    if name not in _models:
        from sentence_transformers import SentenceTransformer
        try:
            m = SentenceTransformer(name, device=_device(), local_files_only=True)
        except Exception:
            m = SentenceTransformer(name, device=_device())
        m.max_seq_length = min(MAX_SEQ_LENGTH, getattr(m.tokenizer, "model_max_length", MAX_SEQ_LENGTH) or MAX_SEQ_LENGTH)
        _models[name] = m
    return _models[name]


def _text_key(name: str, text: str) -> str:
    return hashlib.sha256((name + "\0" + text).encode("utf-8")).hexdigest()


def _cache_path(name: str) -> Path | None:
    if EMBED_CACHE_DIR is None:
        return None
    return EMBED_CACHE_DIR / (re.sub(r"[^A-Za-z0-9._-]+", "_", name) + ".npz")


def _load_cache(name: str) -> dict:
    p = _cache_path(name)
    if p is None or not p.exists():
        return {}
    try:
        import numpy as np
        with np.load(p) as z:
            return {k: z[k] for k in z.files}
    except Exception:
        return {}


def _save_cache(name: str, cache: dict) -> None:
    p = _cache_path(name)
    if p is None or not cache:
        return
    try:
        import numpy as np
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp.npz")
        np.savez(tmp, **cache)
        tmp.replace(p)
    except Exception as e:  # a cache failure must never block a check
        print(f"  [Diversity] embedding cache not saved: {e}")


def embed(texts: list[str], name: str | None = None):
    """Unit-normalized embeddings, one row per text. Identical texts are
    embedded once per process and cached on disk under logs/."""
    import numpy as np
    name = name or model_name()
    keys = [_text_key(name, t) for t in texts]
    disk = _load_cache(name)
    missing = [(k, t) for k, t in zip(keys, texts) if (name, k) not in _memo and k not in disk]
    seen = set()
    todo = [(k, t) for k, t in missing if not (k in seen or seen.add(k))]
    if todo:
        model = _get_model(name)
        vecs = model.encode([t for _, t in todo], normalize_embeddings=True, batch_size=1,
                            show_progress_bar=False)
        for (k, _), v in zip(todo, vecs):
            disk[k] = np.asarray(v, dtype=np.float32)
        _save_cache(name, disk)
    out = []
    for k in keys:
        if (name, k) not in _memo:
            _memo[(name, k)] = np.asarray(disk[k], dtype=np.float32)
        out.append(_memo[(name, k)])
    return np.vstack(out) if out else np.zeros((0, 0), dtype=np.float32)


# --------------------------------------------------------------------------
# Text extraction: Scout posts
# --------------------------------------------------------------------------

FENCE_RE = re.compile(r"^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", re.MULTILINE | re.DOTALL)
CARD_RE = re.compile(r"^```card[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\s*\n.*?\n---\s*\n?", "", text, count=1, flags=re.DOTALL)


def _strip_code_blocks(text: str) -> str:
    text = FENCE_RE.sub(" ", text)
    return re.sub(r"(?im)^\s*topic_gate:.*$", "", text)


def extract_card(text: str) -> dict | None:
    """The card from a ```card fenced JSON block. Uses prediction_card when it
    is available so both modules read cards the same way."""
    try:
        import prediction_card
        card = prediction_card.extract_card(text)
        return None if not isinstance(card, dict) or "_parse_error" in card else card
    except ImportError:
        pass
    except Exception:
        return None
    blocks = CARD_RE.findall(text)
    if not blocks:
        return None
    try:
        card = json.loads(blocks[-1])
    except json.JSONDecodeError:
        return None
    return card if isinstance(card, dict) else None


def card_outcome(card: dict) -> str:
    """Top-level 'outcome' if present, else the primary spec's outcome_def."""
    if card.get("outcome"):
        return str(card["outcome"])
    for spec in card.get("spec_plan") or []:
        if isinstance(spec, dict) and spec.get("role") == "primary" and spec.get("outcome_def"):
            return str(spec["outcome_def"])
    return ""


def card_text(card: dict | None) -> str:
    if not card:
        return ""
    vals = {"quantity": card.get("quantity"), "population": card.get("population"),
            "comparison": card.get("comparison"), "outcome": card_outcome(card)}
    return " ".join(f"{k.capitalize()}: {v}." for k, v in vals.items() if v)


def proposal_sections(text: str) -> str:
    """Bodies of the 'Prediction to Test' and 'Gap Type' sections, headings
    excluded. A section runs to the next heading of the same or higher level."""
    body = _strip_code_blocks(_strip_frontmatter(text))
    heads = list(HEADING_RE.finditer(body))
    parts = []
    for i, h in enumerate(heads):
        if not any(k in h.group(2).lower() for k in SECTION_KEYS):
            continue
        level = len(h.group(1))
        end = len(body)
        for h2 in heads[i + 1:]:
            if len(h2.group(1)) <= level:
                end = h2.start()
                break
        parts.append(body[h.end():end])
    joined = "\n".join(parts)
    joined = HEADING_RE.sub(" ", joined)   # drop any subheadings inside
    return _squash(joined)


def _squash(s: str) -> str:
    s = re.sub(r"\*\*|__|`", "", s)
    return re.sub(r"\s+", " ", s).strip()


def post_text(path: Path, n_chars: int = FALLBACK_CHARS) -> str:
    """The text the guard embeds for one Scout post (see module docstring)."""
    raw = path.read_text(encoding="utf-8")
    sections = proposal_sections(raw)
    if sections:
        extra = card_text(extract_card(raw))
        return (sections + (" " + extra if extra else ""))[:MAX_TEXT_CHARS]
    body = _squash(_strip_code_blocks(_strip_frontmatter(raw)))
    return body[:n_chars]


def has_proposal_sections(path: Path) -> bool:
    return bool(proposal_sections(path.read_text(encoding="utf-8")))


# --------------------------------------------------------------------------
# Text extraction: papers (.tex)
# --------------------------------------------------------------------------

_DROP_CMDS = ("cite", "citep", "citet", "citealp", "citeauthor", "citeyearpar", "citeyear",
              "ref", "eqref", "label", "footnote", "url", "thanks", "includegraphics",
              "bibliography", "bibliographystyle", "input", "vspace", "hspace")


def _balanced(s: str, i: int) -> int:
    """Index just past the brace group that starts at s[i] == '{'."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{" and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif s[j] == "}" and (j == 0 or s[j - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return j + 1
    return len(s)


def _drop_commands(s: str) -> str:
    pat = re.compile(r"\\(" + "|".join(_DROP_CMDS) + r")\*?\s*(\[[^\]]*\]\s*)*(?=\{)")
    out, pos = [], 0
    for m in pat.finditer(s):
        if m.start() < pos:
            continue
        out.append(s[pos:m.start()])
        pos = _balanced(s, m.end())
    out.append(s[pos:])
    return "".join(out)


def strip_latex(s: str) -> str:
    s = re.sub(r"(?<!\\)%.*$", "", s, flags=re.MULTILINE)
    s = _drop_commands(s)
    s = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", " ", s)
    s = s.replace("\\\\", " ").replace("~", " ").replace("---", "-").replace("--", "-")
    s = re.sub(r"``|''", '"', s)
    s = re.sub(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?", " ", s)
    s = re.sub(r"\\(.)", r"\1", s)
    s = s.replace("{", "").replace("}", "").replace("$", "")
    return re.sub(r"\s+", " ", s).strip()


def _tex_group(raw: str, cmd: str) -> str:
    m = re.search(r"\\" + cmd + r"\s*\{", raw)
    if not m:
        return ""
    start = m.end() - 1
    return raw[start + 1:_balanced(raw, start) - 1]


def tex_title(raw: str) -> str:
    return strip_latex(_tex_group(raw, "title"))


def tex_abstract(raw: str) -> str:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw, re.DOTALL)
    return strip_latex(m.group(1)) if m else ""


def tex_introduction(raw: str) -> str:
    secs = list(re.finditer(r"\\section\*?\s*\{([^}]*)\}", raw))
    for i, m in enumerate(secs):
        if "introduction" in m.group(1).lower():
            end = secs[i + 1].start() if i + 1 < len(secs) else len(raw)
            end_doc = raw.find("\\end{document}", m.end())
            if end_doc != -1:
                end = min(end, end_doc)
            return strip_latex(raw[m.end():end])
    return ""


def article_text(path: Path) -> str:
    """Title, abstract and Introduction of a paper's .tex source."""
    raw = path.read_text(encoding="utf-8")
    parts = [tex_title(raw), tex_abstract(raw), tex_introduction(raw)]
    return " ".join(p for p in parts if p)[:MAX_TEXT_CHARS]


def article_files(articles_dir: Path | None = None) -> list[Path]:
    """Paper sources, with build_site's template and compile filters."""
    d = articles_dir or ARTICLES_DIR
    return [t for t in sorted(d.glob("*_r*.tex"))
            if not any(x in t.name for x in ("template", "content", "compile", "test"))]


# --------------------------------------------------------------------------
# Rounds and corpus
# --------------------------------------------------------------------------

def _round_of(post_path: Path, n_agents: int = 3) -> int:
    """Legacy file-index round. Kept until the forum_index migration test
    replaces it (M12)."""
    n = int(post_path.name[:3])
    return (n - 1) // n_agents + 1


def _post_round(path: Path) -> int:
    """Round from orchestrator-written frontmatter when forum_index is
    available, otherwise the legacy file-index rule."""
    try:
        import forum_index
        r = forum_index.post_meta(path).get("round")
        if r:
            return int(r)
    except Exception:
        pass
    return _round_of(path)


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


def prior_corpus(current_round: int, arc_start: int, exclude: str | None = None) -> list[dict]:
    """Everything from BEFORE the active arc: Scout posts of earlier arcs and
    all papers drafted before this arc. Within-arc similarity is expected
    (depth first) and is not penalized. exclude is the checked post's name."""
    items = []
    for p in sorted(FORUM_DIR.glob("*_literature_scout.md")):
        if p.name == exclude:
            continue
        r = _post_round(p)
        if r < arc_start and r < current_round:
            items.append({"id": p.stem, "kind": "scout_post", "round": r, "text": post_text(p)})
    for a in article_files():
        r = _article_round(a)
        if r < arc_start:
            items.append({"id": a.stem, "kind": "article", "round": r, "text": article_text(a)})
    return items


# --------------------------------------------------------------------------
# Structured duplicate check (Stage 2, with prediction cards)
# --------------------------------------------------------------------------

def _norm(s) -> str:
    s = str(s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _card_key(card: dict) -> tuple[str, str, str] | None:
    vals = {"outcome": card_outcome(card), "population": card.get("population"),
            "comparison": card.get("comparison")}
    key = tuple(_norm(vals[f]) for f in STRUCTURED_FIELDS)
    return key if all(key) else None


def structured_duplicate(card: dict | None, arc_start: int, cards_dir: Path | None = None) -> dict | None:
    """First card from before the active arc whose normalized outcome,
    population and comparison all equal this card's, or None."""
    if not card:
        return None
    key = _card_key(card)
    if key is None:
        return None
    d = cards_dir or CARDS_DIR
    if not d.exists():
        return None
    for f in sorted(d.glob("R*.json")):
        m = re.match(r"R(\d+)", f.stem)
        if not m or int(m.group(1)) >= arc_start:
            continue
        try:
            other = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        others = other if isinstance(other, list) else [other]
        for o in others:
            if isinstance(o, dict) and _card_key(o) == key:
                return {"card": f.stem, "round": int(m.group(1)), "fields": list(STRUCTURED_FIELDS),
                        "claim_id": o.get("claim_id")}
    return None


# --------------------------------------------------------------------------
# The check
# --------------------------------------------------------------------------

def _logged_rows() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    rows = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def status_for(cosine: float | None, warn: float, block: float) -> str:
    if cosine is None:
        return "no_prior"
    return "block" if cosine >= block else ("warn" if cosine >= warn else "clear")


def nearest(post_path: Path, current_round: int, arc_start: int, name: str | None = None) -> dict:
    """Nearest prior Scout post and paper (cosine), without thresholds or logging.
    Shared by check_post and calibrate_diversity.py."""
    name = name or model_name()
    corpus = prior_corpus(current_round, arc_start, exclude=Path(post_path).name)
    out = {"n_prior": len(corpus), "nearest_post": None, "nearest_article": None, "max_cosine": None}
    if not corpus:
        return out
    q = embed([post_text(post_path)], name)[0]
    E = embed([c["text"] for c in corpus], name)
    sims = E @ q
    best = {"scout_post": None, "article": None}
    for c, s in zip(corpus, sims):
        k = c["kind"]
        if best[k] is None or s > best[k][0]:
            best[k] = (float(s), c["id"], c["round"])
    for k, key in (("scout_post", "nearest_post"), ("article", "nearest_article")):
        if best[k]:
            out[key] = {"cosine": round(best[k][0], 3), "id": best[k][1], "round": best[k][2]}
    out["max_cosine"] = round(max(v[0] for v in best.values() if v), 3)
    return out


def check_post(post_path: Path, log: bool = True, *, round_num: int | None = None,
               arc_start: int | None = None, run_id: str | None = None) -> dict:
    """Nearest prior Scout post and paper for a freshly written Scout post.

    The caller passes the post path its own accepted Scout run created, never
    the newest file on disk, so a failed run writes no row. At most one row is
    written per post and model."""
    cfg = _config()
    warn, block, source = thresholds(cfg)
    name = model_name(cfg)
    post_path = Path(post_path)
    current_round = round_num if round_num is not None else _post_round(post_path)
    if arc_start is None:
        arc_start = _arc_start(current_round)
    raw = post_path.read_text(encoding="utf-8")
    result = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "post": post_path.name, "round": current_round, "arc_start": arc_start,
        "run_id": run_id, "model": name, "text_version": TEXT_VERSION,
        "text_basis": "sections" if proposal_sections(raw) else "fallback_body",
        "warn": warn, "block": block, "thresholds_source": source,
        "structured_duplicate": None,
    }
    near = nearest(post_path, current_round, arc_start, name)
    result.update(near)
    result["status"] = status_for(near["max_cosine"], warn, block)
    if near["max_cosine"] is None:
        del result["max_cosine"]
    if _stage2(cfg, "prediction_cards"):
        dup = structured_duplicate(extract_card(raw), arc_start)
        if dup:
            result["structured_duplicate"] = dup
            result["status"] = "block"
    if log:
        if any(r.get("post") == result["post"] and r.get("model") == name for r in _logged_rows()):
            result["logged"] = False
        else:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
            result["logged"] = True
    return result


def latest_result(round_num: int | None = None) -> dict | None:
    rows = _logged_rows()
    if round_num is not None:
        rows = [r for r in rows if r.get("round") == round_num]
    return rows[-1] if rows else None


def format_for_prompt(round_num: int | None = None) -> str:
    """Block for Analyst and Critic prompts in the same round as the Scout post.

    Neutral lines only (the nearest prior texts, their cosines, the status).
    The thresholds are provisional and uncalibrated (D-15), so the block
    carries no scoring cap and no verdict instruction. The Critic judges a
    repeat from the texts, as its own prompt says."""
    r = latest_result(round_num)
    if not r or r.get("status") == "no_prior":
        return ""
    lines = ["\n## Topic Diversity Check (Season 2)\n"]
    np_, na = r.get("nearest_post"), r.get("nearest_article")
    if np_:
        lines.append(f"- Nearest prior Scout post: {np_['id']} (R{np_['round']}), cosine {np_['cosine']:.2f}")
    if na:
        lines.append(f"- Nearest prior article: {na['id']} (R{na['round']}), cosine {na['cosine']:.2f}")
    dup = r.get("structured_duplicate")
    if dup:
        lines.append(f"- Card duplicate: outcome, population and comparison equal card {dup['card']} "
                     f"(R{dup['round']}) after normalization")
    lines.append(f"- Thresholds (provisional, uncalibrated): warn {r['warn']:.2f}, block {r['block']:.2f}. "
                 f"Status: **{r['status'].upper()}**")
    lines.append("\nThe thresholds are not calibrated, so the status only points to the nearest prior texts. "
                 "Compare the texts themselves.")
    return "\n".join(lines) + "\n"


def prior_topics_for_scout() -> str:
    """Compact list of prior arc topics so Scout can avoid them before posting.
    Thresholds come from forum_config, never from this text."""
    warn, block, _ = thresholds()
    arc_start = _arc_start(10 ** 9)   # without an active arc every paper is prior
    lines = ["\n## Topic Diversity (Season 2): questions already taken\n",
             "After you post, your Prediction to Test and Gap Type sections are compared with every prior "
             f"arc's Scout posts and papers (cosine similarity with {model_name()}, warn {warn:.2f}, "
             f"block {block:.2f}). Restating any of these, with a new dataset or a new decade, is a duplicate. "
             "Change the quantity, the mechanism, or the population.\n"]
    for a in article_files():
        r = _article_round(a)
        if r < arc_start:
            title = tex_title(a.read_text(encoding="utf-8"))
            if title:
                lines.append(f"- R{r}: {title}")
    return "\n".join(lines) + "\n"


def matrix() -> None:
    arts = article_files()
    E = embed([article_text(a) for a in arts])
    S = E @ E.T
    ids = [f"r{_article_round(a)}" for a in arts]
    print("       " + " ".join(i.rjust(4) for i in ids))
    for i, r in enumerate(ids):
        print(r.rjust(6), " ".join(f"{S[i, j]:.2f}" if i != j else " -- " for j in range(len(ids))))


def main() -> None:
    ap = argparse.ArgumentParser(description="Season 2 topic-diversity guard")
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("check", help="Check one Scout post against prior arcs and papers")
    c.add_argument("post")
    c.add_argument("--no-log", action="store_true")
    c.add_argument("--round", type=int, default=None)
    t = sub.add_parser("text", help="Print the text the guard embeds for a post or .tex paper")
    t.add_argument("path")
    sub.add_parser("matrix", help="Paper-by-paper cosine matrix")
    args = ap.parse_args()
    if args.cmd == "check":
        r = check_post(Path(args.post), log=not args.no_log, round_num=args.round)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.cmd == "text":
        p = Path(args.path)
        print(article_text(p) if p.suffix == ".tex" else post_text(p))
    elif args.cmd == "matrix":
        matrix()
    else:
        ap.print_help()


if __name__ == "__main__":
    sys.exit(main())
