import subprocess
import sys
from pathlib import Path

VENV_CREATION_TIMEOUT_SECONDS = 300


class EnvironmentBuilder:
    """
    Membuat Virtual Environment Python.
    """

    def create(self, project_path: Path) -> None:

        print("\n[INFO] Membuat Virtual Environment...")

        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "venv",
                    str(project_path / ".venv")
                ],
                check=True,
                timeout=VENV_CREATION_TIMEOUT_SECONDS,
            )
        except subprocess.SubprocessError as error:
            print(f"[ERROR] Virtual environment creation failed: {error}")
            raise

        print("[OK] Virtual Environment berhasil dibuat.")
