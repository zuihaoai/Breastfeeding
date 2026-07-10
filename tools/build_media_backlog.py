#!/usr/bin/env python3
"""Build a readable media backlog from media map metadata."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "meta" / "media_backlog.json"
OUTPUT = ROOT / "media.backlog.md"


def build() -> str:
    items = json.loads(INPUT.read_text(encoding="utf-8"))
    lines: list[str] = []
    lines.append("# Breastfeeding 媒体资源待办清单")
    lines.append("")
    lines.append("## 使用方式")
    lines.append("")
    lines.append("- P0：先做，直接影响阅读理解和 AI 调取。")
    lines.append("- P1：第二批做，补足长期检索与教学资源。")
    lines.append("")

    for item in items:
        lines.append(f"## {item['chapter']:02d} {item['title']} [{item['priority']}]")
        lines.append("")
        lines.append("### 插图")
        for image in item["images"]:
            lines.append(f"- {image}")
        lines.append("")
        lines.append("### 视频")
        for video in item["videos"]:
            lines.append(f"- {video}")
        lines.append("")
        lines.append("### 备注")
        for note in item["source_notes"]:
            lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"written {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
