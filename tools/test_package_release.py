from pathlib import Path
import subprocess
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


class PackageReleaseTest(unittest.TestCase):
    def test_package_release_creates_zip(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "package_release.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("written", result.stdout)
        zip_path = ROOT / "dist" / "Breastfeeding-release.zip"
        self.assertTrue(zip_path.exists())
        with ZipFile(zip_path) as zf:
            names = set(zf.namelist())
        self.assertIn("Breastfeeding-release/README.md", names)
        self.assertIn("Breastfeeding-release/book.md", names)
        self.assertIn("Breastfeeding-release/meta/manifest.json", names)


if __name__ == "__main__":
    unittest.main()
