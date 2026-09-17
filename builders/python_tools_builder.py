"""
==================================================
ForgePy
Module  : Python Tools Builder
==================================================
"""

import subprocess
from pathlib import Path

from builders.base_builder import BaseBuilder
from core.venv_paths import get_venv_python

PACKAGE_TOOL_UPDATE_TIMEOUT_SECONDS = 300


class PythonToolsBuilder(BaseBuilder):
    """
    Mengupdate pip, setuptools, dan wheel
    pada Virtual Environment.
    """

    def update(
        self,
        project_path: Path,
    ) -> None:

        python = get_venv_python(project_path)

        if not python.exists():
            print("[WARNING] Virtual Environment belum tersedia.")
            return

        packages = [
            "pip",
            "setuptools",
            "wheel",
        ]

        for package in packages:

            print(f"[INFO] Mengupdate {package}...")

            try:
                subprocess.run(
                    [
                        str(python),
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        package,
                    ],
                    check=True,
                    timeout=PACKAGE_TOOL_UPDATE_TIMEOUT_SECONDS,
                )
            except subprocess.SubprocessError as error:
                print(
                    "[ERROR] Packaging-tool update failed for "
                    f"'{package}': {error}"
                )
                raise

            print(f"[OK] {package} berhasil diupdate.")