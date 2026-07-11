from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BuildBookTest(unittest.TestCase):
    def test_build_book_generates_output(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "build_book.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("written", result.stdout)
        self.assertTrue((ROOT / "book.generated.md").exists())
        self.assertTrue((ROOT / "README.md").exists())
        text = (ROOT / "book.generated.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("# Breastfeeding", text)
        self.assertIn("## 01 孕期认知储备", text)
        self.assertIn("## 07 人工喂养与替代喂养", text)
        self.assertIn("## 阅读入口", readme)
        self.assertIn("[在线阅读与 PDF 下载](index.html)", readme)
        self.assertNotIn("源文件：", readme)
        self.assertIn("## 目录", readme)
        self.assertIn("## 01 孕期认知储备", readme)
        self.assertIn("[巴克假说](#point-01-005)", readme)
        self.assertIn('<a id="point-01-005"></a>', readme)
        self.assertIn("      - [怀孕即被盯上](#point-07-012)", readme)
        self.assertIn("    - [奶粉如何营销](#point-07-011)", readme)
        self.assertIn("assets/images/article-illustrations/point-01-001.png", readme)
        self.assertIn("assets/images/03-jaundice-phototherapy-thresholds.png", readme)
        self.assertIn("docs/05-权威资源下载与核验.md", readme)
        self.assertIn("docs/06-G6PD溶血触发物质清单.md", readme)


if __name__ == "__main__":
    unittest.main()
