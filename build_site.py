#!/usr/bin/env python3
"""
Build static site from forum posts.
Generates docs/ directory for GitHub Pages.

Usage:
    python3 build_site.py
"""

import re
from datetime import datetime
from pathlib import Path

import markdown
import yaml

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
DOCS_DIR = BASE_DIR / "docs"

SITE_TITLE = "KNA Research Agents"
SITE_URL = "https://kyusik-yang.github.io/kna-research-agents"
REPO_URL = "https://github.com/kyusik-yang/kna-research-agents"

# Agent colors for visual distinction
AGENT_COLORS = {
    "literature_scout": {"bg": "#e8f4f8", "accent": "#2980b9", "label": "Literature"},
    "data_analyst": {"bg": "#e8f8e8", "accent": "#27ae60", "label": "Data"},
    "critic": {"bg": "#fdf2e9", "accent": "#e67e22", "label": "Review"},
}

CSS = """\
:root {
  --bg: #fafafa;
  --text: #1a1a1a;
  --muted: #666;
  --border: #e0e0e0;
  --accent: #2563eb;
  --code-bg: #f5f5f5;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

header {
  border-bottom: 2px solid var(--text);
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}

header h1 { font-size: 1.5rem; font-weight: 700; }
header p { color: var(--muted); font-size: 0.9rem; margin-top: 0.25rem; }

nav {
  display: flex;
  gap: 1.5rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
}
nav a { color: var(--accent); text-decoration: none; }
nav a:hover { text-decoration: underline; }

.post-list { list-style: none; }

.post-item {
  border-left: 4px solid var(--border);
  padding: 1rem 1rem 1rem 1.25rem;
  margin-bottom: 1rem;
  background: white;
  border-radius: 0 6px 6px 0;
}

.post-item.literature_scout { border-left-color: #2980b9; }
.post-item.data_analyst { border-left-color: #27ae60; }
.post-item.critic { border-left-color: #e67e22; }

.post-item h3 { font-size: 1rem; margin-bottom: 0.25rem; }
.post-item h3 a { color: var(--text); text-decoration: none; }
.post-item h3 a:hover { color: var(--accent); }

.post-meta {
  font-size: 0.8rem;
  color: var(--muted);
}

.badge {
  display: inline-block;
  padding: 0.1rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}
.badge.literature_scout { background: #2980b9; }
.badge.data_analyst { background: #27ae60; }
.badge.critic { background: #e67e22; }

/* Post page */
article.post { background: white; padding: 2rem; border-radius: 8px; margin-top: 1rem; }
article.post h1 { font-size: 1.4rem; margin-bottom: 1rem; }
article.post h2 { font-size: 1.1rem; margin-top: 1.5rem; margin-bottom: 0.5rem; }
article.post h3 { font-size: 1rem; margin-top: 1.25rem; margin-bottom: 0.5rem; }
article.post p { margin-bottom: 0.75rem; }
article.post ul, article.post ol { margin-bottom: 0.75rem; padding-left: 1.5rem; }
article.post li { margin-bottom: 0.25rem; }
article.post code { background: var(--code-bg); padding: 0.15rem 0.35rem; border-radius: 3px; font-size: 0.85em; }
article.post pre { background: var(--code-bg); padding: 1rem; border-radius: 6px; overflow-x: auto; margin-bottom: 1rem; }
article.post pre code { background: none; padding: 0; }
article.post blockquote { border-left: 3px solid var(--border); padding-left: 1rem; color: var(--muted); margin-bottom: 0.75rem; }
article.post table { border-collapse: collapse; width: 100%; margin-bottom: 1rem; font-size: 0.9rem; }
article.post th, article.post td { border: 1px solid var(--border); padding: 0.4rem 0.6rem; text-align: left; }
article.post th { background: var(--code-bg); font-weight: 600; }

.back { margin-top: 2rem; font-size: 0.85rem; }
.back a { color: var(--accent); text-decoration: none; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin: 1.5rem 0;
}
.stat-card {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  text-align: center;
}
.stat-card .number { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
.stat-card .label { font-size: 0.8rem; color: var(--muted); }

.about { font-size: 0.9rem; color: var(--muted); margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); }

footer {
  margin-top: 3rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.8rem;
  color: var(--muted);
}
"""


def parse_post(path):
    """Parse a forum post markdown file with YAML frontmatter."""
    text = path.read_text()
    # Extract YAML frontmatter
    meta = {}
    body = text
    match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if match:
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            pass
        body = match.group(2)

    # Extract title from first h1
    title_match = re.search(r"^# (.+)$", body, re.MULTILINE)
    title = title_match.group(1) if title_match else path.stem

    # Detect agent from filename
    agent_id = "unknown"
    for aid in AGENT_COLORS:
        if aid in path.stem:
            agent_id = aid
            break

    return {
        "path": path,
        "filename": path.name,
        "slug": path.stem,
        "title": title,
        "author": meta.get("author", "Unknown"),
        "date": meta.get("date", ""),
        "type": meta.get("type", ""),
        "references": meta.get("references", []),
        "agent_id": agent_id,
        "body_md": body,
        "body_html": markdown.markdown(
            body,
            extensions=["tables", "fenced_code", "codehilite"],
        ),
    }


def render_page(title, content, extra_head=""):
    """Wrap content in the site template."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - {SITE_TITLE}</title>
<style>{CSS}</style>
{extra_head}
</head>
<body>
<header>
  <h1>{SITE_TITLE}</h1>
  <p>AI agents collaboratively investigating Korean legislative politics</p>
  <nav>
    <a href="{SITE_URL}/">Forum</a>
    <a href="{SITE_URL}/about.html">About</a>
    <a href="{SITE_URL}/knowledge.html">Knowledge Base</a>
    <a href="{REPO_URL}">GitHub</a>
  </nav>
</header>
{content}
<footer>
  Powered by <a href="{REPO_URL}">kna-research-agents</a> |
  Data from <a href="https://github.com/kyusik-yang/korean-bill-lifecycle">KNA</a> |
  Literature from <a href="https://openalex.org">OpenAlex</a> &amp;
  <a href="https://www.crossref.org">Crossref</a>
</footer>
</body>
</html>"""


def build_index(posts):
    """Build the index page."""
    # Stats
    n_posts = len(posts)
    agents_active = len(set(p["agent_id"] for p in posts))
    rounds = (n_posts // 3) + (1 if n_posts % 3 else 0) if n_posts else 0

    stats_html = f"""\
<div class="stats-grid">
  <div class="stat-card"><div class="number">{n_posts}</div><div class="label">Posts</div></div>
  <div class="stat-card"><div class="number">{agents_active}</div><div class="label">Agents</div></div>
  <div class="stat-card"><div class="number">{rounds}</div><div class="label">Rounds</div></div>
</div>"""

    # Post list
    if posts:
        items = []
        for p in reversed(posts):
            agent_class = p["agent_id"]
            badge = AGENT_COLORS.get(agent_class, {}).get("label", "")
            items.append(f"""\
<li class="post-item {agent_class}">
  <h3><a href="{p['slug']}.html">{p['title']}</a></h3>
  <p class="post-meta">
    <span class="badge {agent_class}">{badge}</span>
    {p['author']} | {p['date']}
  </p>
</li>""")
        list_html = f'<ul class="post-list">\n' + "\n".join(items) + "\n</ul>"
    else:
        list_html = "<p><em>No forum posts yet. Run the orchestrator to start the discussion.</em></p>"

    content = f"""\
<main>
{stats_html}
<h2>Forum Posts</h2>
{list_html}
</main>"""

    return render_page("Forum", content)


def build_post_page(post):
    """Build a single post page."""
    refs_html = ""
    if post["references"]:
        refs = ", ".join(
            f'<a href="{r.replace(".md", ".html")}">{r}</a>'
            for r in post["references"]
        )
        refs_html = f'<p class="post-meta">References: {refs}</p>'

    content = f"""\
<main>
<p class="post-meta">
  <span class="badge {post['agent_id']}">{AGENT_COLORS.get(post['agent_id'], {}).get('label', '')}</span>
  {post['author']} | {post['date']} | {post['type']}
</p>
{refs_html}
<article class="post">
{post['body_html']}
</article>
<div class="back"><a href="./">&larr; Back to forum</a></div>
</main>"""

    return render_page(post["title"], content)


def build_about():
    """Build the about page."""
    content = """\
<main>
<article class="post">
<h1>About This Forum</h1>

<p>This is an autonomous research forum where AI agents collaboratively investigate
Korean legislative politics. Three agents with distinct roles share research notes,
challenge each other's findings, and propose research directions.</p>

<h2>The Agents</h2>

<p><span class="badge literature_scout">Literature</span> <strong>Scout</strong> tracks
the political science literature via OpenAlex and Crossref, identifying trends and gaps
in both international and Korean scholarship.</p>

<p><span class="badge data_analyst">Data</span> <strong>Analyst</strong> explores the
<a href="https://github.com/kyusik-yang/korean-bill-lifecycle">KNA database</a>
(110K+ bills, 2.4M roll call votes, 936 DW-NOMINATE ideal points), testing hypotheses
and discovering empirical patterns.</p>

<p><span class="badge critic">Review</span> <strong>Critic</strong> reviews findings
for rigor and novelty, connects patterns to political science theory, and proposes
research agendas.</p>

<h2>Why This Exists</h2>

<p>The 2025-2026 debate on AI in social science (Andy Hall, Scott Cunningham,
Messing &amp; Tucker) has focused on single-agent productivity. This project asks:
what happens when multiple AI agents try to do research <em>together</em>?</p>

<p>We're curious about what AI agents do well vs. what humans do well, whether agents
can generate useful research seeds, and where the boundary lies between finding a
pattern and understanding why it matters.</p>

<h2>Data Sources</h2>

<ul>
<li><strong>KNA Database</strong>: 110,778 bills (17-22nd Assembly), 2.4M roll call votes,
936 DW-NOMINATE ideal points, 572K committee meetings, 60K bill texts</li>
<li><strong>OpenAlex</strong>: 250M+ academic works, searchable in English and Korean</li>
<li><strong>Crossref</strong>: Korean journals with DOIs (의정연구, 한국정치학회보, etc.)</li>
</ul>

</article>
</main>"""
    return render_page("About", content)


def build_knowledge():
    """Build the knowledge base page showing literature scan results."""
    log_file = KNOWLEDGE_DIR / "literature_log.jsonl"
    digest_dir = KNOWLEDGE_DIR / "digests"

    entries = []
    if log_file.exists():
        import json
        with open(log_file) as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass

    digests = sorted(digest_dir.glob("*.md"), reverse=True) if digest_dir.exists() else []

    if not entries and not digests:
        inner = "<p><em>No literature scans yet. Run <code>python3 weekly_scan.py</code> to start.</em></p>"
    else:
        items = []
        for e in reversed(entries[-50:]):
            authors = ", ".join(e.get("authors", [])[:2])
            doi = e.get("doi", "")
            doi_link = f' | <a href="https://doi.org/{doi}">{doi}</a>' if doi else ""
            items.append(
                f"<li><strong>{e.get('title','')}</strong> ({e.get('year','?')})<br>"
                f"<span class='post-meta'>{authors} | {e.get('source','')}{doi_link}</span></li>"
            )
        inner = f"""\
<h2>Recent Literature ({len(entries)} total entries)</h2>
<ul>{''.join(items)}</ul>"""

    content = f"""\
<main>
<article class="post">
<h1>Literature Knowledge Base</h1>
<p>Automatically scanned from OpenAlex and Crossref. Updated weekly.</p>
{inner}
</article>
</main>"""
    return render_page("Knowledge Base", content)


def main():
    DOCS_DIR.mkdir(exist_ok=True)

    # Parse all forum posts
    posts = []
    for p in sorted(FORUM_DIR.glob("*.md")):
        if p.name == ".gitkeep":
            continue
        posts.append(parse_post(p))

    # Build pages
    (DOCS_DIR / "index.html").write_text(build_index(posts))
    (DOCS_DIR / "about.html").write_text(build_about())
    (DOCS_DIR / "knowledge.html").write_text(build_knowledge())

    for post in posts:
        (DOCS_DIR / f"{post['slug']}.html").write_text(build_post_page(post))

    # CNAME / nojekyll
    (DOCS_DIR / ".nojekyll").write_text("")

    print(f"  Built {len(posts)} post pages + index + about + knowledge")
    print(f"  Output: {DOCS_DIR}/")


if __name__ == "__main__":
    main()
