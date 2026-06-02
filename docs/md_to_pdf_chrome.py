"""Markdown -> 带中文样式的 HTML -> Chrome/Edge 无头打印 PDF。

不依赖 GTK(weasyprint 在 Windows 需要),只需本机已装 Chrome 或 Edge。
用法: python docs/md_to_pdf_chrome.py docs/某文档.md
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

CSS_STYLE = """
@page { size: A4; margin: 2cm 1.8cm; }
body {
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 10.5pt; line-height: 1.7; color: #222;
    max-width: 100%;
}
h1 { font-size: 22pt; color: #1a365d; border-bottom: 3px solid #1a365d;
     padding-bottom: 8px; margin-top: 0; }
h2 { font-size: 16pt; color: #2c5282; border-bottom: 1px solid #cbd5e0;
     padding-bottom: 5px; margin-top: 24px; }
h3 { font-size: 13pt; color: #2d3748; margin-top: 20px; }
h4 { font-size: 11.5pt; color: #4a5568; }
p, li { margin: 6px 0; }
code { background: #f0f2f5; padding: 1px 5px; border-radius: 3px;
       font-family: Consolas, monospace; font-size: 9.5pt; color: #c0392b; }
pre { background: #f7f9fb; border: 1px solid #e2e8f0; border-radius: 6px;
      padding: 12px 14px; overflow-x: auto; line-height: 1.5; }
pre code { background: none; color: #2d3748; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9.8pt; }
th, td { border: 1px solid #cbd5e0; padding: 6px 10px; text-align: left; }
th { background: #edf2f7; font-weight: 600; }
tr:nth-child(even) { background: #f9fafb; }
blockquote { border-left: 4px solid #4299e1; background: #ebf8ff;
             margin: 12px 0; padding: 8px 16px; color: #2c5282; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }
strong { color: #1a365d; }
"""


def main(md_path: str) -> None:
    src = Path(md_path)
    html_body = markdown.markdown(
        src.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code"],
    )
    html = (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{CSS_STYLE}</style></head><body>{html_body}</body></html>"
    )

    tmpdir = Path(tempfile.gettempdir())
    # 用纯 ASCII 临时名,规避 Chrome --print-to-pdf 对中文路径的兼容问题
    tmp_html = tmpdir / "_md2pdf_input.html"
    tmp_pdf = tmpdir / "_md2pdf_output.pdf"
    tmp_html.write_text(html, encoding="utf-8")
    if tmp_pdf.exists():
        tmp_pdf.unlink()

    out_pdf = src.with_suffix(".pdf")

    browsers = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    browser = next((b for b in browsers if Path(b).exists()), None)
    if browser is None:
        sys.exit("未找到 Chrome 或 Edge")

    subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={tmp_pdf}",
            tmp_html.as_uri(),
        ],
        check=True,
        timeout=120,
    )
    if not tmp_pdf.exists():
        sys.exit("PDF 生成失败:Chrome 未输出文件")
    # 移动到目标中文路径(用 Python 处理,避免 Chrome 中文路径问题)
    out_pdf.write_bytes(tmp_pdf.read_bytes())
    tmp_pdf.unlink()
    print(f"已生成: {out_pdf} ({out_pdf.stat().st_size} bytes)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法: python docs/md_to_pdf_chrome.py <markdown文件>")
    main(sys.argv[1])
