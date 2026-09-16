import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from core.venv_paths import get_venv_python


class TestVenvPaths(unittest.TestCase):
    def setUp(self) -> None:
        self.project_path = Path("example_project")

    def test_windows_venv_python_path(self) -> None:
        with patch.object(sys, "platform", "win32"):
            result = get_venv_python(self.project_path)

        self.assertEqual(
            result,
            self.project_path / ".venv" / "Scripts" / "python.exe",
        )

    def test_posix_venv_python_path(self) -> None:
        with patch.object(sys, "platform", "linux"):
            result = get_venv_python(self.project_path)

        self.assertEqual(
            result,
            self.project_path / ".venv" / "bin" / "python",
        )


if __name__ == "__main__":
    unittest.main()