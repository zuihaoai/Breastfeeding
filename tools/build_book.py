#!/usr/bin/env python3
"""Build a single markdown book from chapter sources and manifest metadata."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "meta" / "manifest.json"
OUTPUT = ROOT / "book.generated.md"
README_OUTPUT = ROOT / "README.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_yaml_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return text
    return parts[1]


def source_headings(text: str) -> list[tuple[int, str]]:
    """Return Markdown headings that can be exposed as direct reading targets."""
    headings: list[tuple[int, str]] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append((len(match.group(1)), match.group(2).strip()))
    return headings


def point_id(chapter_number: int, point_number: int) -> str:
    return f"point-{chapter_number:02d}-{point_number:03d}"


def chapter_outline(chapter: dict, chapter_text: str) -> list[str]:
    number = int(chapter["chapter"])
    lines: list[str] = []
    for index, (level, title) in enumerate(source_headings(chapter_text), start=1):
        # Keep every source heading visually under its chapter entry.
        indent = "  " * level
        lines.append(f"{indent}- [{title}](#{point_id(number, index)})")
    return lines


def add_point_anchors(chapter_number: int, chapter_text: str) -> str:
    """Add stable anchors before source headings without changing source prose."""
    lines: list[str] = []
    point_number = 0
    in_fence = False
    for line in chapter_text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            point_number += 1
            lines.append(f'<a id="{point_id(chapter_number, point_number)}"></a>')
        lines.append(line)
    return "\n".join(lines)


def build() -> str:
    manifest = json.loads(read_text(MANIFEST))
    lines: list[str] = []
    lines.append(f"# {manifest['title']}")
    lines.append("")
    if subtitle := manifest.get("subtitle"):
        lines.append(subtitle)
        lines.append("")

    lines.append("## 阅读入口")
    lines.append("")
    lines.append("- [在线阅读与 PDF 下载](index.html)")
    lines.append("- [目录总表（含检索标签）](docs/00-目录总表.md)")
    lines.append("- [电子书导入方案](docs/01-电子书导入方案.md)")
    lines.append("- [插图视频映射方案](docs/02-插图视频映射方案.md)")
    lines.append("")
    lines.append("## 目录")
    lines.append("")
    for chapter in manifest["chapters"]:
        number = int(chapter["chapter"])
        title = chapter["title"]
        anchor = f"chapter-{number:02d}"
        lines.append(f"{number}. [{title}](#{anchor})")
        source = ROOT / chapter["source"]
        chapter_text = strip_yaml_frontmatter(read_text(source)).strip()
        lines.extend(chapter_outline(chapter, chapter_text))
    lines.append("")
    lines.append("---")
    lines.append("")

    for chapter in manifest["chapters"]:
        number = int(chapter["chapter"])
        title = chapter["title"]
        source = ROOT / chapter["source"]
        chapter_text = strip_yaml_frontmatter(read_text(source)).strip()

        lines.append(f'<a id="chapter-{number:02d}"></a>')
        lines.append(f"## {number:02d} {title}")
        lines.append("")
        lines.append(f"- 源文件：[{source.name}]({chapter['source']})")
        lines.append("")
        lines.append(add_point_anchors(number, chapter_text))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_readme(book_text: str) -> str:
    manifest = json.loads(read_text(MANIFEST))
    title = manifest["title"]
    subtitle = manifest.get("subtitle", "")
    marker = "## 阅读入口\n\n"
    if marker not in book_text:
        return book_text

    _, body = book_text.split(marker, 1)
    body = re.sub(r"(?m)^- 源文件：.*\n?", "", body)
    body = body.split("## 目录\n\n", 1)[1]
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    if subtitle:
        lines.append(subtitle)
        lines.append("")
    lines.append("> 这是完整正文。目录中的每个条目都可以直接跳到对应知识点，适合按需查阅，也可以从头阅读。")
    lines.append("")
    lines.append("## 阅读入口")
    lines.append("")
    lines.append("- [在线阅读与 PDF 下载](index.html)")
    lines.append("- [目录总表（含检索标签）](docs/00-目录总表.md)")
    lines.append("- [电子书导入方案](docs/01-电子书导入方案.md)")
    lines.append("- [插图视频映射方案](docs/02-插图视频映射方案.md)")
    lines.append("")
    lines.append("## 目录")
    lines.append("")
    toc, content = body.split("---\n\n", 1)
    lines.append(toc.rstrip())
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(content)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    book = build()
    OUTPUT.write_text(book, encoding="utf-8")
    README_OUTPUT.write_text(build_readme(book), encoding="utf-8")
    print(f"written {OUTPUT}")
    print(f"written {README_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
