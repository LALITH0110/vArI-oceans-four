"""
File Summary:
- Converts project Markdown documentation into static HTML in the site/ folder.
- Uses the markdown library with basic extensions and copies static assets.
- Invoked via `make docs` for lightweight documentation builds.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import markdown

DOCS_DIR = Path("docs")
SITE_DIR = Path("site")


def render_markdown(md_path: Path) -> str:
    """Render a markdown file to HTML text."""
    text = md_path.read_text(encoding="utf8")
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "toc"],
        extension_configs={"toc": {"permalink": True}},
    )


def build_docs() -> None:
    """Render all docs/*.md files into site/*.html."""
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    for md_file in DOCS_DIR.glob("*.md"):
        html = render_markdown(md_file)
        out_path = SITE_DIR / f"{md_file.stem}.html"
        out_path.write_text(html, encoding="utf8")
    assets_src = DOCS_DIR / "assets"
    assets_dst = SITE_DIR / "assets"
    if assets_src.exists():
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)


if __name__ == "__main__":
    build_docs()
