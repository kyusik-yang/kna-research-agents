"""Corrected articles carry a 'Version N · corrected <date>' label on the
articles page, read from the .md companion frontmatter."""
from html import escape

import build_site


def _md(path, fm):
    path.write_text("---\n" + "".join(f"{k}: {v}\n" for k, v in fm.items()) + "---\n\n# T\n",
                    encoding="utf-8")


def test_badge_only_for_corrected_articles(tmp_path, monkeypatch):
    monkeypatch.setattr(build_site, "ARTICLES_DIR", tmp_path)
    _md(tmp_path / "2026-01-01_r1.md", {"version": 2, "corrected": '"2026-09-26"'})
    _md(tmp_path / "2026-01-02_r2.md", {"title": '"Original"'})
    _md(tmp_path / "2026-01-03_r3.md", {"version": 2})
    assert build_site._article_correction("2026-01-01_r1") == (2, "2026-09-26")
    assert build_site._article_correction("2026-01-02_r2") is None
    assert build_site._article_correction("2026-01-03_r3") is None
    assert build_site._article_correction("missing") is None
    badge = build_site._correction_badge_html("2026-01-01_r1", escape)
    assert "Version 2 · corrected 2026-09-26" in badge
    assert build_site._correction_badge_html("2026-01-02_r2", escape) == ""


def test_published_corrections_are_labeled():
    html = build_site._build_article_list()
    for date in ("corrected 2026-09-26", "corrected 2026-09-27"):
        assert date in html
    assert html.count("Version 2 · corrected") == 3
