import sys
from pathlib import Path


def get_venv_python(project_path: Path) -> Path:
    """
    Mengembalikan path Python executable dari virtual environment
    sesuai platform yang sedang digunakan.
    """

    return project_path / get_venv_python_relative_path()


def get_venv_python_relative_path() -> Path:
    """
    Mengembalikan path relatif Python executable di dalam .venv
    sesuai platform yang sedang digunakan.
    """

    if sys.platform == "win32":
        return Path(".venv") / "Scripts" / "python.exe"

    return Path(".venv") / "bin" / "python"