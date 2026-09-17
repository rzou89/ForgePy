import json
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from io import StringIO
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

from core.project_generator import ProjectGenerator
from core.venv_paths import get_venv_python_relative_path
from core.vscode_builder import VSCodeBuilder
from templates.basic.basic_template import BasicTemplate
from templates.library.library_template import LibraryTemplate


class VSCodeBuilderTests(unittest.TestCase):

    _VSCODE_FILENAMES: ClassVar = {
        "extensions.json",
        "launch.json",
        "settings.json",
        "tasks.json",
    }

    _WORKSPACE_PYTHON = (
        f"${{workspaceFolder}}/"
        f"{get_venv_python_relative_path().as_posix()}"
    )

    _INSTALL_REQUIREMENTS_TASK: ClassVar = {
        "label": "Install Requirements",
        "type": "shell",
        "command": _WORKSPACE_PYTHON,
        "args": [
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt",
        ],
        "presentation": {
            "reveal": "always",
        },
        "problemMatcher": [],
    }

    def test_builder_default_preserves_basic_vscode_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "BasicDemo"
            project_root.mkdir()

            with redirect_stdout(StringIO()):
                VSCodeBuilder().create(project_root)

            configuration = self._load_configuration(project_root)

            self.assertEqual(
                configuration["launch.json"],
                self._basic_launch_configuration(),
            )
            self.assertEqual(
                configuration["tasks.json"],
                self._basic_task_configuration(),
            )

    def test_basic_project_keeps_existing_vscode_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = self._generate_project(
                parent=Path(temporary_directory),
                project_name="BasicDemo",
                template_name="basic",
            )
            configuration = self._load_configuration(project_root)

            self.assertEqual(
                BasicTemplate().vscode_entry_point,
                "app.py",
            )
            self.assertTrue((project_root / "app.py").is_file())

            self.assertEqual(
                configuration["launch.json"],
                self._basic_launch_configuration(),
            )

            self.assertEqual(
                configuration["tasks.json"],
                self._basic_task_configuration(),
            )

            self.assertEqual(
                configuration["settings.json"],
                {
                    "python.defaultInterpreterPath": (
                        get_venv_python_relative_path().as_posix()
                    ),
                    "python.analysis.typeCheckingMode": "basic",
                    "python.analysis.autoImportCompletions": True,
                    "editor.formatOnSave": True,
                    "editor.tabSize": 4,
                    "files.trimTrailingWhitespace": True,
                    "files.insertFinalNewline": True,
                },
            )

            self.assertEqual(
                configuration["extensions.json"],
                {
                    "recommendations": [
                        "ms-python.python",
                        "ms-python.debugpy",
                        "ms-python.vscode-pylance",
                        "ms-python.black-formatter",
                        "charliermarsh.ruff",
                        "eamodio.gitlens",
                    ],
                },
            )

    def test_library_project_has_no_missing_entry_point_references(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = self._generate_project(
                parent=Path(temporary_directory),
                project_name="DemoLib",
                template_name="library",
            )
            configuration = self._load_configuration(project_root)

            self.assertIsNone(LibraryTemplate().vscode_entry_point)
            self.assertFalse((project_root / "app.py").exists())

            self.assertEqual(
                configuration["launch.json"],
                {
                    "version": "0.2.0",
                    "configurations": [],
                },
            )

            self.assertEqual(
                configuration["tasks.json"],
                {
                    "version": "2.0.0",
                    "tasks": [
                        self._INSTALL_REQUIREMENTS_TASK,
                    ],
                },
            )

            self.assertTrue(
                (project_root / "requirements.txt").is_file()
            )

            vscode_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in (project_root / ".vscode").iterdir()
                if path.is_file()
            )

            self.assertNotIn("app.py", vscode_text)
            self.assertNotIn('"program"', vscode_text)

    def test_cli_project_targets_generated_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = self._generate_project(
                parent=Path(temporary_directory),
                project_name="Demo-CLI",
                template_name="cli",
            )

            configuration = self._load_configuration(project_root)
            entry_point = "demo_cli/cli.py"

            self.assertTrue(
                (project_root / entry_point).is_file()
            )

            self.assertEqual(
                configuration["launch.json"],
                {
                    "version": "0.2.0",
                    "configurations": [
                        {
                            "name": f"Python: {entry_point}",
                            "type": "debugpy",
                            "request": "launch",
                            "program": (
                                "${workspaceFolder}/"
                                f"{entry_point}"
                            ),
                            "console": "integratedTerminal",
                            "justMyCode": True,
                        },
                    ],
                },
            )

            self.assertEqual(
                configuration["tasks.json"],
                {
                    "version": "2.0.0",
                    "tasks": [
                        {
                            "label": "Run Application",
                            "type": "shell",
                            "command": self._WORKSPACE_PYTHON,
                            "args": [
                                entry_point,
                            ],
                            "group": {
                                "kind": "build",
                                "isDefault": True,
                            },
                            "presentation": {
                                "reveal": "always",
                            },
                            "problemMatcher": [],
                        },
                        self._INSTALL_REQUIREMENTS_TASK,
                    ],
                },
            )

            vscode_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in (project_root / ".vscode").iterdir()
                if path.is_file()
            )

            self.assertNotIn("app.py", vscode_text)

    def _generate_project(
        self,
        parent: Path,
        project_name: str,
        template_name: str,
    ) -> Path:

        with ExitStack() as stack:
            stack.enter_context(
                patch(
                    "core.project_generator.EnvironmentBuilder.create",
                )
            )

            stack.enter_context(
                patch(
                    "core.project_generator.PythonToolsBuilder.update",
                )
            )

            stack.enter_context(
                patch(
                    "core.project_generator.RequirementsInstaller.install",
                )
            )

            stack.enter_context(
                patch(
                    "core.project_generator.GitBuilder.create",
                )
            )

            stack.enter_context(
                redirect_stdout(StringIO())
            )

            ProjectGenerator().create(
                project_name=project_name,
                location=str(parent),
                template_name=template_name,
            )

        return parent / project_name

    def _load_configuration(
        self,
        project_root: Path,
    ) -> dict[str, object]:

        vscode_folder = project_root / ".vscode"

        paths = {
            path.name: path
            for path in vscode_folder.iterdir()
            if path.is_file()
        }

        self.assertEqual(
            set(paths),
            self._VSCODE_FILENAMES,
        )

        return {
            filename: json.loads(
                path.read_text(encoding="utf-8")
            )
            for filename, path in paths.items()
        }

    def _basic_launch_configuration(
        self,
    ) -> dict[str, object]:

        return {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Python: app.py",
                    "type": "debugpy",
                    "request": "launch",
                    "program": "${workspaceFolder}/app.py",
                    "console": "integratedTerminal",
                    "justMyCode": True,
                },
            ],
        }

    def _basic_task_configuration(
        self,
    ) -> dict[str, object]:

        return {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "Run Application",
                    "type": "shell",
                    "command": self._WORKSPACE_PYTHON,
                    "args": [
                        "app.py",
                    ],
                    "group": {
                        "kind": "build",
                        "isDefault": True,
                    },
                    "presentation": {
                        "reveal": "always",
                    },
                    "problemMatcher": [],
                },
                self._INSTALL_REQUIREMENTS_TASK,
            ],
        }


if __name__ == "__main__":
    unittest.main()