#!/usr/bin/env python3
"""Package the breastfeeding ebook staging repo into a release zip."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
STAGE = DIST / "Breastfeeding-release"
ZIP_PATH = DIST / "Breastfeeding-release.zip"


def run_builders() -> None:
    subprocess.run(["python3", str(ROOT / "tools" / "build_book.py")], cwd=ROOT, check=True)
    subprocess.run(["python3", str(ROOT / "tools" / "build_media_backlog.py")], cwd=ROOT, check=True)


def should_copy(path: Path) -> bool:
    if path.name in {".git", "__pycache__"}:
        return False
    if path.suffix in {".pyc", ".tmp"}:
        return False
    if path.name in {"book.generated.md", "media.backlog.md"}:
        return False
    return True


def copy_tree(src: Path, dst: Path) -> None:
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            if should_copy(child):
                copy_tree(child, dst / child.name)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_release_tree() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    STAGE.mkdir(parents=True, exist_ok=True)

    for name in [
        "README.md",
        "book.md",
        ".gitignore",
        "chapters",
        "docs",
        "meta",
        "assets",
        "tools",
    ]:
        copy_tree(ROOT / name, STAGE / name)


def make_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with ZipFile(ZIP_PATH, "w", compression=ZIP_DEFLATED) as zf:
        for path in STAGE.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(DIST))


def main() -> int:
    run_builders()
    build_release_tree()
    make_zip()
    print(f"written {ZIP_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
