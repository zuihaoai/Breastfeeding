import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

sys.modules.setdefault("markdown", types.SimpleNamespace(Markdown=object))

import build_pdf


class BuildPdfTests(unittest.TestCase):
    def test_outputs_preview_pdf_without_overwriting_download_pdf(self) -> None:
        self.assertEqual(build_pdf.OUTPUT_PDF.name, "Breastfeeding.preview.pdf")

    def test_pdf_source_excludes_reading_entry_section(self) -> None:
        source = """# 母乳喂养电子书

开头介绍。

## 阅读入口

- [在线阅读](https://example.com)
- [下载 PDF](https://example.com/book.pdf)

## 目录

- 第一篇
"""

        prepared = build_pdf.prepare_readme_for_pdf(source)

        self.assertIn("# 母乳喂养电子书", prepared)
        self.assertIn("## 目录", prepared)
        self.assertNotIn("## 阅读入口", prepared)
        self.assertNotIn("在线阅读", prepared)

    def test_rewrite_local_readme_links_to_section_anchors(self) -> None:
        source = "[生命最初1000天](./孕期%20-%20认知储备/生命最初1000天/README.md)"

        rewritten = build_pdf.rewrite_local_readme_links(source)

        self.assertEqual(rewritten, "[生命最初1000天](#生命最初1000天奠定一生身心健康的基石)")

    def test_chapter_order_matches_current_book_outline(self) -> None:
        names = [path.parent.name for path in build_pdf.CHAPTER_READMES]

        self.assertEqual(names, ["生命最初1000天", "母乳喂养征程准备出发"])

    def test_book_css_starts_pages_on_top_level_titles(self) -> None:
        self.assertIn(".content h1:first-of-type { break-before: avoid; }", build_pdf.BOOK_CSS)
        self.assertNotIn("  .content h2:first-of-type { break-before: avoid; }", build_pdf.BOOK_CSS)

    def test_resolve_chrome_prefers_env_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            fake_chrome = Path(raw_tmp) / "chrome"
            fake_chrome.write_text("", encoding="utf-8")
            old_value = os.environ.get("CHROME_PATH")
            os.environ["CHROME_PATH"] = str(fake_chrome)
            try:
                self.assertEqual(build_pdf.resolve_chrome(), fake_chrome)
            finally:
                if old_value is None:
                    os.environ.pop("CHROME_PATH", None)
                else:
                    os.environ["CHROME_PATH"] = old_value


if __name__ == "__main__":
    unittest.main()
