#!/usr/bin/env python3
"""Render README.md + cover.html into Breastfeeding.preview.pdf."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import markdown
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
COVER = ROOT / "cover.html"
BOOK_HTML = ROOT / "book.html"
OUTPUT_PDF = ROOT / "Breastfeeding.preview.pdf"
PDF_ASSET_CACHE = ROOT / ".cache" / "pdf-assets"
PDF_IMAGE_MAX_WIDTH = 1400
PDF_IMAGE_JPEG_QUALITY = 82
CHAPTER_READMES = [
    ROOT / "孕期 - 认知储备" / "生命最初1000天" / "README.md",
    ROOT / "孕期 - 认知储备" / "母乳喂养征程准备出发" / "README.md",
]


def resolve_chrome() -> Path:
    env_path = os.environ.get("CHROME_PATH")
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"CHROME_PATH does not exist: {candidate}")

    path_candidates = [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
    ]
    for candidate in path_candidates:
        if candidate.exists():
            return candidate

    for command in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        found = shutil.which(command)
        if found:
            return Path(found)

    raise FileNotFoundError("未找到 Chrome/Chromium/Edge。请安装 Chrome，或通过 CHROME_PATH 指定浏览器可执行文件。")


def extract_cover() -> tuple[str, str]:
    raw = COVER.read_text(encoding="utf-8")
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    style_match = re.search(r"<style>(.*?)</style>", raw, re.S)
    body_match = re.search(r"<body>(.*?)</body>", raw, re.S)
    if not style_match or not body_match:
        raise ValueError("cover.html must contain <style> and <body> blocks")

    style = style_match.group(1)
    body = body_match.group(1)
    style = re.sub(r"@page\s*\{[^}]*\}", "", style, count=1)
    style = style.replace("* { margin: 0; padding: 0; box-sizing: border-box; }", ".cover, .cover * { margin: 0; padding: 0; box-sizing: border-box; }")
    style = style.replace("html, body {", ".cover {")
    return style, body


def prepare_readme_for_pdf(text: str) -> str:
    excluded_h2_titles = {"阅读入口"}
    output: list[str] = []
    skipping = False

    for line in text.splitlines(keepends=True):
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            title = match.group(1).strip()
            skipping = title in excluded_h2_titles
            if skipping:
                continue

        if not skipping:
            output.append(line)

    return "".join(output)


def rewrite_local_readme_links(text: str) -> str:
    """Point links to nested README files at their rendered section anchors."""
    replacements = {
        r"\]\(\./孕期%20-%20认知储备/生命最初1000天/README\.md\)": "](#生命最初1000天奠定一生身心健康的基石)",
        r"\]\(\./孕期%20-%20认知储备/母乳喂养征程准备出发/README\.md\)": "](#母乳喂养不亚于万里长征准备好了吗)",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    return text


def chapter_markdown() -> str:
    sections: list[str] = []
    for chapter in CHAPTER_READMES:
        if chapter.exists():
            sections.append(chapter.read_text(encoding="utf-8").strip())
    return "\n\n---\n\n".join(sections)


def has_inlined_chapters(text: str) -> bool:
    return (
        "生命最初1000天：奠定一生身心健康的基石" in text
        and "母乳喂养不亚于万里长征，准备好了吗？" in text
    )


def book_markdown() -> str:
    root_text = prepare_readme_for_pdf(README.read_text(encoding="utf-8"))
    root_text = rewrite_local_readme_links(root_text)
    if has_inlined_chapters(root_text):
        return root_text

    chapters = chapter_markdown()
    if not chapters:
        return root_text
    return f"{root_text.rstrip()}\n\n---\n\n{chapters}\n"


def render_readme() -> str:
    text = book_markdown()
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5",
    )
    return md.convert(text)


def _to_pdf_jpeg(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as raw_image:
        image = ImageOps.exif_transpose(raw_image)
        image.thumbnail((PDF_IMAGE_MAX_WIDTH, PDF_IMAGE_MAX_WIDTH * 4), Image.Resampling.LANCZOS)

        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            canvas = Image.new("RGB", image.size, "#ffffff")
            canvas.paste(image.convert("RGBA"), mask=image.convert("RGBA").getchannel("A"))
            image = canvas
        else:
            image = image.convert("RGB")

        image.save(output, "JPEG", quality=PDF_IMAGE_JPEG_QUALITY, optimize=True, progressive=True)


def prepare_pdf_assets(content_html: str, root: Path = ROOT) -> str:
    pattern = re.compile(
        r'(?P<prefix>\bsrc\s*=\s*["\'])(?P<src>assets/images/[^"\']+\.(?:png|jpg|jpeg|webp))(?P<suffix>["\'])',
        re.I,
    )
    converted: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        src = match.group("src")
        source = root / src
        if not source.exists():
            return match.group(0)

        output = PDF_ASSET_CACHE / Path(src).with_suffix(".jpg")
        _to_pdf_jpeg(source, output)
        rewritten = output.relative_to(root).as_posix()
        converted[src] = rewritten
        return f"{match.group('prefix')}{rewritten}{match.group('suffix')}"

    optimized_html = pattern.sub(replace, content_html)
    if converted:
        print(f"已为 PDF 优化 {len(converted)} 张图片到 {PDF_ASSET_CACHE.relative_to(root)}")
    return optimized_html


BOOK_CSS = """
  @page { size: A4; margin: 16mm 15mm 15mm 15mm; }
  @page coverpage { size: A4; margin: 0; }

  .cover-page { page: coverpage; break-after: page; }

  body {
    font-family: "PingFang SC", "Songti SC", -apple-system, "Helvetica Neue", system-ui, sans-serif;
    font-size: 10.5pt;
    line-height: 1.75;
    color: #1f1c18;
    -webkit-font-smoothing: antialiased;
  }

  .content h1, .content h2, .content h3,
  .content h4, .content h5, .content h6 {
    font-weight: 700;
    line-height: 1.35;
    break-after: avoid;
    color: #171411;
  }

  .content h1 {
    font-size: 23pt;
    margin: 0 0 8mm;
    padding-bottom: 4mm;
    border-bottom: 3px solid #d85f73;
    break-before: page;
  }

  .content h1:first-of-type { break-before: avoid; }

  .content h2 {
    font-size: 17pt;
    margin: 11mm 0 4mm;
    padding-left: 4mm;
    border-left: 6px solid #d85f73;
  }
  .content h3 { font-size: 13.5pt; margin: 7mm 0 3mm; color: #9f354a; }
  .content h4 { font-size: 11.5pt; margin: 5mm 0 2.5mm; }
  .content h5, .content h6 { font-size: 10.5pt; margin: 4mm 0 2mm; color: #5c554d; }

  .content p { margin: 0 0 2.6mm; }
  .content ul, .content ol { margin: 0 0 3mm; padding-left: 7mm; }
  .content li { margin: 0 0 1mm; }

  .content blockquote {
    margin: 3mm 0;
    padding: 2mm 4mm;
    background: #fff4f6;
    border-left: 4px solid #d85f73;
    color: #5c554d;
  }

  .content blockquote p { margin: 0; }

  .content table {
    width: 100%;
    border-collapse: collapse;
    margin: 3mm 0 4mm;
    font-size: 9.5pt;
    break-inside: auto;
  }

  .content th, .content td {
    border: 1px solid #e1d8d2;
    padding: 1.6mm 2.4mm;
    text-align: left;
    vertical-align: top;
  }

  .content thead th { background: #f9eef1; color: #171411; font-weight: 700; }
  .content tr { break-inside: avoid; }

  .content code {
    font-family: "SF Mono", Menlo, Consolas, monospace;
    font-size: 9pt;
    background: #f3eee9;
    padding: 0.4mm 1mm;
    border-radius: 2px;
  }

  .content pre {
    background: #1f1c18;
    color: #f8f1ea;
    padding: 3mm 4mm;
    border-radius: 4px;
    margin: 2.5mm 0 4mm;
    overflow: hidden;
    break-inside: avoid;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .content pre code { background: transparent; color: inherit; font-size: 8.6pt; padding: 0; }
  .content p[align="center"] { text-align: center; margin: 3mm 0; break-inside: avoid; }
  .content img { max-width: 100%; height: auto; border: 1px solid #ececec; border-radius: 3px; }
  .content hr { border: none; border-top: 1px solid #e1d8d2; margin: 5mm 0; }
  .content a { color: #9f354a; text-decoration: none; }
  .content > h2#目录 + ul, .content ul ul { font-size: 10pt; }
"""


def build() -> None:
    cover_style, cover_body = extract_cover()
    content_html = prepare_pdf_assets(render_readme())
    document = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>母乳喂养电子书</title>
<style>
{cover_style}
{BOOK_CSS}
</style>
</head>
<body>
  <div class="cover-page">
{cover_body}
  </div>
  <main class="content">
{content_html}
  </main>
</body>
</html>
"""
    BOOK_HTML.write_text(document, encoding="utf-8")
    print(f"已生成 {BOOK_HTML.relative_to(ROOT)}（{len(document)} 字节）")

    subprocess.run(
        [
            str(resolve_chrome()),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={OUTPUT_PDF}",
            BOOK_HTML.as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    size_kb = OUTPUT_PDF.stat().st_size / 1024
    print(f"已导出 {OUTPUT_PDF.name}（{size_kb:.0f} KB）")


if __name__ == "__main__":
    build()
