#!/usr/bin/env python3
"""Build a single markdown book from chapter sources and manifest metadata."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "meta" / "manifest.json"
OUTPUT = ROOT / "book.generated.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_yaml_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return text
    return parts[1]


def build() -> str:
    manifest = json.loads(read_text(MANIFEST))
    lines: list[str] = []
    lines.append(f"# {manifest['title']}")
    lines.append("")
    if subtitle := manifest.get("subtitle"):
        lines.append(subtitle)
        lines.append("")

    lines.append("## 目录")
    lines.append("")
    for chapter in manifest["chapters"]:
        number = int(chapter["chapter"])
        title = chapter["title"]
        anchor = f"chapter-{number:02d}"
        lines.append(f"{number}. [{title}](#{anchor})")
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
        lines.append(chapter_text)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"written {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
