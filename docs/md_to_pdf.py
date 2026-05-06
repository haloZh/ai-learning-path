"""Convert a markdown file to PDF using weasyprint, with Chinese fonts."""

import sys
from pathlib import Path

import markdown
from weasyprint import CSS, HTML

CSS_STYLE = """
@page {
    size: A4;
    margin: 2.2cm 2cm 2.2cm 2cm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: "Noto Serif CJK SC", serif;
        font-size: 9pt;
        color: #888;
    }
}

body {
    font-family: "Noto Serif CJK SC", "AR PL UMing CN", serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #222;
}

h1 {
    font-size: 22pt;
    color: #1a365d;
    border-bottom: 3px solid #2c5282;
    padding-bottom: 0.3em;
    margin-top: 1em;
    page-break-before: avoid;
}

h2 {
    font-size: 16pt;
    color: #2c5282;
    border-bottom: 1px solid #bee3f8;
    padding-bottom: 0.2em;
    margin-top: 1.6em;
    page-break-after: avoid;
}

h3 {
    font-size: 13pt;
    color: #2a4365;
    margin-top: 1.2em;
    page-break-after: avoid;
}

h4 {
    font-size: 11.5pt;
    color: #2a4365;
    margin-top: 1em;
    page-break-after: avoid;
}

p {
    margin: 0.5em 0;
    text-align: justify;
}

strong {
    color: #1a365d;
}

ul, ol {
    margin: 0.4em 0 0.6em 1.2em;
}

li {
    margin: 0.2em 0;
}

code {
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: "DejaVu Sans Mono", "Noto Serif CJK SC", monospace;
    font-size: 9.5pt;
    color: #c53030;
}

pre {
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #4299e1;
    padding: 0.8em 1em;
    border-radius: 3px;
    overflow-x: auto;
    page-break-inside: avoid;
}

pre code {
    background: transparent;
    border: none;
    padding: 0;
    color: #2d3748;
    font-size: 9pt;
    white-space: pre;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.8em 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #cbd5e0;
    padding: 0.45em 0.7em;
    text-align: left;
    vertical-align: top;
}

th {
    background: #ebf4ff;
    color: #1a365d;
    font-weight: bold;
}

tr:nth-child(even) td {
    background: #f7fafc;
}

blockquote {
    border-left: 4px solid #4299e1;
    padding: 0.3em 1em;
    background: #ebf8ff;
    margin: 0.8em 0;
    color: #2a4365;
}

hr {
    border: none;
    border-top: 1px solid #cbd5e0;
    margin: 1.5em 0;
}

a {
    color: #2b6cb0;
    text-decoration: none;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    page-break-inside: avoid;
}

figure {
    page-break-inside: avoid;
    margin: 1em 0;
}
"""


def convert(md_path: Path, pdf_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        text,
        extensions=["extra", "tables", "fenced_code", "toc", "sane_lists"],
    )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>{md_path.stem}</title></head>
<body>{html_body}</body>
</html>"""
    HTML(string=html, base_url=str(md_path.parent)).write_pdf(
        pdf_path,
        stylesheets=[CSS(string=CSS_STYLE)],
    )
    print(f"[OK] {md_path.name} -> {pdf_path.name} ({pdf_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        md_path = Path(args[0])
    else:
        md_path = Path(__file__).parent / "产品方案.md"
    pdf_path = md_path.with_suffix(".pdf")
    convert(md_path, pdf_path)
