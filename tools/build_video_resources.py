#!/usr/bin/env python3
"""Build a readable video resource index from structured metadata."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "meta" / "video_resources.json"
OUTPUT = ROOT / "media.videos.md"


def build() -> str:
    items = json.loads(INPUT.read_text(encoding="utf-8"))
    lines: list[str] = []
    lines.append("# Breastfeeding 教学视频资源清单")
    lines.append("")
    lines.append("## 使用方式")
    lines.append("")
    lines.append("- 优先使用官方页面，不复制视频本体。")
    lines.append("- 章号与 `docs/00-目录总表.md` 保持一致。")
    lines.append("- 先补动作类，再补概念类。")
    lines.append("")

    for item in items:
        lines.append(f"## {item['chapter']:02d} {item['title']}")
        lines.append("")
        videos = item.get("videos", [])
        if videos:
            for video in videos:
                lines.append(f"- [{video['name']}]({video['url']})")
                lines.append(f"  - 来源：{video['source']}")
                lines.append(f"  - 用途：{video['purpose']}")
        else:
            lines.append("- 暂无可用公开视频")
        for note in item.get("notes", []):
            lines.append(f"- 备注：{note}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    OUTPUT.write_text(build(), encoding="utf-8")
    print(f"written {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
