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
        self.assertNotIn("## 阅读入口", readme)
        self.assertNotIn("源文件：", readme)
        self.assertIn("## 目录", readme)
        self.assertIn("## 01 孕期认知储备", readme)


if __name__ == "__main__":
    unittest.main()
