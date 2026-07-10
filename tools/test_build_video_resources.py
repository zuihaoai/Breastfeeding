from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BuildVideoResourcesTest(unittest.TestCase):
    def test_build_video_resources_generates_output(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "build_video_resources.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("written", result.stdout)
        output = ROOT / "media.videos.md"
        self.assertTrue(output.exists())
        text = output.read_text(encoding="utf-8")
        self.assertIn("# Breastfeeding 教学视频资源清单", text)
        self.assertIn("## 01 孕期认知储备", text)
        self.assertIn("## 07 人工喂养与替代喂养", text)


if __name__ == "__main__":
    unittest.main()
