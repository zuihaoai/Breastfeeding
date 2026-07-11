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

NESTED_RAW_GROUPS = {
    "chapters/认知与备孕.md": {
        "孕期 - 认知储备 - 生命最初1000天": {
            "生命最初1000天：奠定一生身心健康的基石",
        },
        "生命最初1000天：奠定一生身心健康的基石": {
            "第一部分，震撼父母的数据",
            "第二部分，健康和疾病的发育起源",
            "营养错配",
            "心血管系统对生命早期营养不足非常敏感",
            "第三部分，营养是基因表观的“开关”",
            "给您的建议",
        },
        "孕期 - 认知储备 - 哺乳征程": {
            "母乳喂养不亚于万里长征，准备好了吗？",
            "第一部分，孤立无援的母乳喂养大环境",
            "中国的实施情况分析",
            "第二部分，为什么你应该坚持",
            "第三部分，成为母乳喂养的倡导者",
        },
    },
    "chapters/人工喂养.md": {
        "奶粉如何营销": {
            "怀孕即被盯上",
            "谎言无处不在",
            "医务参与其中",
            "大V收割粉丝",
            "代价极其惨烈",
            "营养都是虚构",
            "颠覆价值信仰",
            "坚守母乳喂养",
        },
    },
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_yaml_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return text
    return parts[1]


def heading_records(
    text: str,
    nested_groups: dict[str, set[str]] | None = None,
) -> list[tuple[int, int, str]]:
    """Return raw and normalized heading levels for generated book views."""
    records: list[tuple[int, int, str]] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            raw_level = len(match.group(1))
            title = match.group(2).strip()
            if not records:
                normalized_level = 1
            elif raw_level == 1:
                parent = next(
                    (
                        record
                        for parent_title, children in (nested_groups or {}).items()
                        if title in children
                        for record in reversed(records)
                        if record[2] == parent_title
                    ),
                    None,
                )
                normalized_level = parent[1] + 1 if parent else 2
            elif raw_level == 2 and not any(raw == 1 for raw, _, _ in records[1:]):
                # Some articles begin with ## topics directly below the title.
                normalized_level = 2
            else:
                parent = next(
                    (record for record in reversed(records) if record[0] < raw_level),
                    None,
                )
                normalized_level = parent[1] + 1 if parent else 2
            records.append((raw_level, normalized_level, title))
    return records


def source_headings(
    text: str,
    nested_groups: dict[str, set[str]] | None = None,
) -> list[tuple[int, str]]:
    """Return normalized headings for the direct-reading table of contents."""
    return [
        (normalized, title)
        for _, normalized, title in heading_records(text, nested_groups)
    ]


def point_id(chapter_number: int, point_number: int) -> str:
    return f"point-{chapter_number:02d}-{point_number:03d}"


def chapter_outline(chapter: dict, chapter_text: str) -> list[str]:
    number = int(chapter["chapter"])
    nested_groups = NESTED_RAW_GROUPS.get(chapter["source"], {})
    lines: list[str] = []
    for index, (level, title) in enumerate(
        source_headings(chapter_text, nested_groups), start=1
    ):
        # Keep every source heading visually under its chapter entry.
        # The numbered chapter is the list root; every source heading belongs
        # underneath it, including the source article title.
        indent = "  " * level
        lines.append(f"{indent}- [{title}](#{point_id(number, index)})")
    return lines


def add_point_anchors(
    chapter_number: int,
    chapter_text: str,
    nested_groups: dict[str, set[str]] | None = None,
) -> str:
    """Add anchors and normalize heading levels in the generated article."""
    lines: list[str] = []
    point_number = 0
    in_fence = False
    records = iter(heading_records(chapter_text, nested_groups))
    for line in chapter_text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            point_number += 1
            lines.append(f'<a id="{point_id(chapter_number, point_number)}"></a>')
            _, normalized_level, title = next(records)
            display_level = 3 if normalized_level <= 2 else normalized_level + 1
            lines.append(f"{'#' * display_level} {title}")
            illustration = ROOT / "assets" / "images" / "article-illustrations" / f"{point_id(chapter_number, point_number)}.png"
            if illustration.exists():
                lines.append("")
                lines.append(
                    f"![{title}配图](assets/images/article-illustrations/{illustration.name})"
                )
            continue
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
    lines.append("- [权威资源下载与核验](docs/05-权威资源下载与核验.md)")
    lines.append("- [G6PD 溶血触发物质清单](docs/06-G6PD溶血触发物质清单.md)")
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
        chapter_text = chapter_text.replace("../assets/", "assets/").replace("../docs/", "docs/")
        lines.extend(chapter_outline(chapter, chapter_text))
    lines.append("")
    lines.append("---")
    lines.append("")

    for chapter in manifest["chapters"]:
        number = int(chapter["chapter"])
        title = chapter["title"]
        source = ROOT / chapter["source"]
        chapter_text = strip_yaml_frontmatter(read_text(source)).strip()
        chapter_text = chapter_text.replace("../assets/", "assets/").replace("../docs/", "docs/")

        lines.append(f'<a id="chapter-{number:02d}"></a>')
        lines.append(f"## {number:02d} {title}")
        lines.append("")
        lines.append(f"- 源文件：[{source.name}]({chapter['source']})")
        lines.append("")
        lines.append(
            add_point_anchors(
                number,
                chapter_text,
                NESTED_RAW_GROUPS.get(chapter["source"], {}),
            )
        )
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
    lines.append("- [权威资源下载与核验](docs/05-权威资源下载与核验.md)")
    lines.append("- [G6PD 溶血触发物质清单](docs/06-G6PD溶血触发物质清单.md)")
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
