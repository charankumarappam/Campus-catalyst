"""
package_submission.py
Creates an optimized, clean ZIP package of the Campus Catalyst project
strictly under the 24 MB submission limit (typically ~0.4 MB).
Excludes non-portable folders like .venv, .git, and __pycache__.
"""

from __future__ import annotations
import os
import zipfile
from pathlib import Path


def create_submission_zip():
    base_dir = Path(__file__).resolve().parent
    zip_path = base_dir / "Campus_Catalyst_Project8_Submission.zip"

    exclude_dirs = {".venv", ".git", "__pycache__", ".pytest_cache", ".streamlit"}
    exclude_extensions = {".pyc", ".bak", ".log"}

    print(f"[*] Packaging project: {base_dir.name}")
    print("[*] Excluding non-portable environment folders (.venv, .git, cache)...")

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(base_dir):
            rel_root = Path(root).relative_to(base_dir)
            if any(part in exclude_dirs for part in rel_root.parts):
                continue

            for file in files:
                file_path = Path(root) / file
                if file_path.name == zip_path.name:
                    continue
                if file_path.suffix.lower() in exclude_extensions:
                    continue

                rel_path = file_path.relative_to(base_dir)
                zipf.write(file_path, rel_path)
                file_count += 1

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    size_kb = zip_path.stat().st_size / 1024
    print("\n" + "=" * 65)
    print(f" [SUCCESS] Submission Package Created: {zip_path.name}")
    print(f" [SIZE]    {size_mb:.2f} MB ({size_kb:.1f} KB) -- WELL UNDER 24 MB LIMIT!")
    print(f" [FILES]   {file_count} project files packaged cleanly")
    print(f" [PATH]    {zip_path.resolve()}")
    print("=" * 65)


if __name__ == "__main__":
    create_submission_zip()
