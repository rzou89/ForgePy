"""
==================================================
ForgePy
Author  : Rendy Zou
Module  : Git Builder
==================================================

Deskripsi:
- Menginisialisasi Git Repository.
- Membuat commit pertama.
"""

import shutil
import subprocess
from pathlib import Path

GIT_INIT_TIMEOUT_SECONDS = 60
GIT_ADD_TIMEOUT_SECONDS = 120
GIT_COMMIT_TIMEOUT_SECONDS = 60


class GitBuilder:
    """
    Builder untuk menginisialisasi Git Repository.
    """

    def create(self, project_root: Path) -> None:

        if shutil.which("git") is None:
            raise FileNotFoundError(
                "Git executable is required but was not found."
            )

        if (project_root / ".git").exists():
            print("[INFO] Git Repository sudah ada.")
            return

        print("\n[INFO] Inisialisasi Git Repository...")

        try:
            subprocess.run(
                ["git", "init"],
                cwd=project_root,
                check=True,
                timeout=GIT_INIT_TIMEOUT_SECONDS,
            )
        except subprocess.SubprocessError as error:
            print(f"[ERROR] Git initialization failed: {error}")
            raise

        try:
            subprocess.run(
                ["git", "add", "."],
                cwd=project_root,
                check=True,
                timeout=GIT_ADD_TIMEOUT_SECONDS,
            )
        except subprocess.SubprocessError as error:
            print(f"[ERROR] Git staging failed: {error}")
            raise

        try:

            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    "Initial project created by ForgePy",
                ],
                cwd=project_root,
                check=True,
                timeout=GIT_COMMIT_TIMEOUT_SECONDS,
            )

            print("[OK] Initial Commit berhasil dibuat.")

        except subprocess.CalledProcessError:

            print(
                "[WARNING] Initial Commit gagal.\n"
                "Pastikan Git user.name dan user.email sudah dikonfigurasi."
            )
            raise
        except subprocess.TimeoutExpired as error:
            print(f"[ERROR] Initial Git commit timed out: {error}")
            raise

        print("[OK] Git Repository berhasil dibuat.")
