from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BuildMediaBacklogTest(unittest.TestCase):
    def test_build_media_backlog_generates_output(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "build_media_backlog.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("written", result.stdout)
        output = ROOT / "media.backlog.md"
        self.assertTrue(output.exists())
        text = output.read_text(encoding="utf-8")
        self.assertIn("# Breastfeeding 媒体资源待办清单", text)
        self.assertIn("## 01 孕期认知储备 [P0]", text)
        self.assertIn("## 07 人工喂养与替代喂养 [P1]", text)


if __name__ == "__main__":
    unittest.main()
