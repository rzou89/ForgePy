"""Bounded subprocess and failure-stage regression tests."""

import subprocess
import tempfile
import unittest
from argparse import Namespace
from contextlib import ExitStack, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from builders.python_tools_builder import (
    PACKAGE_TOOL_UPDATE_TIMEOUT_SECONDS,
    PythonToolsBuilder,
)
from cli.commands.create_command import CreateCommand
from core.environment_builder import (
    VENV_CREATION_TIMEOUT_SECONDS,
    EnvironmentBuilder,
)
from core.git_builder import (
    GIT_ADD_TIMEOUT_SECONDS,
    GIT_COMMIT_TIMEOUT_SECONDS,
    GIT_INIT_TIMEOUT_SECONDS,
    GitBuilder,
)
from core.project_generator import ProjectGenerator
from core.requirements_installer import (
    REQUIREMENTS_INSTALL_TIMEOUT_SECONDS,
    RequirementsInstaller,
)
from core.venv_paths import get_venv_python


class LifecycleSubprocessTimeoutTests(unittest.TestCase):

    def test_venv_timeout_is_identified_and_propagated(self) -> None:
        failure = subprocess.TimeoutExpired("venv", 1)
        output = StringIO()

        with patch(
            "core.environment_builder.subprocess.run",
            side_effect=failure,
        ) as run, redirect_stdout(output), self.assertRaises(subprocess.TimeoutExpired):
            EnvironmentBuilder().create(Path("project"))

        self.assertEqual(
            run.call_args.kwargs["timeout"],
            VENV_CREATION_TIMEOUT_SECONDS,
        )
        self.assertIn("Virtual environment creation failed", output.getvalue())

    def test_packaging_tool_timeout_is_identified_and_propagated(self) -> None:
        failure = subprocess.TimeoutExpired("pip upgrade", 1)
        output = StringIO()

        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            python = get_venv_python(project_root)
            python.parent.mkdir(parents=True)
            python.touch()

            with patch(
                "builders.python_tools_builder.subprocess.run",
                side_effect=failure,
            ) as run, redirect_stdout(output), self.assertRaises(subprocess.TimeoutExpired):
                PythonToolsBuilder().update(project_root)

        self.assertEqual(
            run.call_args.kwargs["timeout"],
            PACKAGE_TOOL_UPDATE_TIMEOUT_SECONDS,
        )
        self.assertIn("Packaging-tool update failed", output.getvalue())
        self.assertIn("'pip'", output.getvalue())

    def test_requirements_timeout_is_identified_and_propagated(self) -> None:
        failure = subprocess.TimeoutExpired("pip install", 1)
        output = StringIO()

        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            (project_root / "requirements.txt").write_text(
                "example\n",
                encoding="utf-8",
            )
            python = get_venv_python(project_root)
            python.parent.mkdir(parents=True)
            python.touch()

            with patch(
                "core.requirements_installer.subprocess.run",
                side_effect=failure,
            ) as run, redirect_stdout(output), self.assertRaises(subprocess.TimeoutExpired):
                RequirementsInstaller().install(project_root)

        self.assertEqual(
            run.call_args.kwargs["timeout"],
            REQUIREMENTS_INSTALL_TIMEOUT_SECONDS,
        )
        self.assertIn("Requirements installation failed", output.getvalue())

    def test_git_stage_timeouts_are_identified_and_propagated(self) -> None:
        cases = (
            (0, GIT_INIT_TIMEOUT_SECONDS, "Git initialization failed"),
            (1, GIT_ADD_TIMEOUT_SECONDS, "Git staging failed"),
            (2, GIT_COMMIT_TIMEOUT_SECONDS, "Initial Git commit timed out"),
        )

        for failure_index, timeout, expected_text in cases:
            with self.subTest(stage=failure_index):
                failure = subprocess.TimeoutExpired("git", timeout)
                side_effects: list[object] = [None, None, None]
                side_effects[failure_index] = failure
                output = StringIO()

                with tempfile.TemporaryDirectory() as temporary_directory, patch(
                    "core.git_builder.shutil.which",
                    return_value="git",
                ), patch(
                    "core.git_builder.subprocess.run",
                    side_effect=side_effects,
                ) as run, redirect_stdout(output), self.assertRaises(
                    subprocess.TimeoutExpired
                ):
                    GitBuilder().create(
                        Path(temporary_directory)
                    )

                self.assertEqual(
                    run.call_args_list[failure_index].kwargs["timeout"],
                    timeout,
                )
                self.assertEqual(run.call_count, failure_index + 1)
                self.assertIn(expected_text, output.getvalue())
                self.assertNotIn(
                    "Git Repository berhasil dibuat",
                    output.getvalue(),
                )

    def test_called_process_error_remains_unchanged(self) -> None:
        failure = subprocess.CalledProcessError(2, ["python", "-m", "venv"])

        with patch(
            "core.environment_builder.subprocess.run",
            side_effect=failure,
        ), redirect_stdout(StringIO()), self.assertRaises(subprocess.CalledProcessError) as context:
            EnvironmentBuilder().create(Path("project"))

        self.assertIs(context.exception, failure)

    def test_timeout_stops_later_lifecycle_stages_and_success(self) -> None:
        failure = subprocess.TimeoutExpired("venv", 1)
        output = StringIO()

        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)

            with ExitStack() as stack:
                stack.enter_context(
                    patch(
                        "core.project_generator.EnvironmentBuilder.create",
                        side_effect=failure,
                    )
                )
                python_tools = stack.enter_context(
                    patch("core.project_generator.PythonToolsBuilder.update")
                )
                requirements = stack.enter_context(
                    patch(
                        "core.project_generator.RequirementsInstaller.install"
                    )
                )
                vscode = stack.enter_context(
                    patch("core.project_generator.VSCodeBuilder.create")
                )
                git = stack.enter_context(
                    patch("core.project_generator.GitBuilder.create")
                )

                with redirect_stdout(output), self.assertRaises(subprocess.TimeoutExpired):
                    ProjectGenerator().create(
                        project_name="TimeoutDemo",
                        location=str(parent),
                        template_name="basic",
                    )

            python_tools.assert_not_called()
            requirements.assert_not_called()
            vscode.assert_not_called()
            git.assert_not_called()
            self.assertNotIn("Project berhasil dibuat", output.getvalue())


class CliTimeoutTranslationTests(unittest.TestCase):

    def test_create_command_translates_missing_git_to_status_one(self) -> None:
        failure = FileNotFoundError(
            "Git executable is required but was not found."
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as temporary_directory, patch(
            "cli.commands.create_command.ProjectGenerator.create",
            side_effect=failure,
        ), redirect_stdout(output):
            status = CreateCommand().execute(
                Namespace(
                    project_name="MissingGit",
                    location=temporary_directory,
                    template="basic",
                )
            )

        self.assertEqual(status, 1)
        self.assertIn("[ERROR] Project creation failed", output.getvalue())
        self.assertIn("Git executable is required", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_create_command_translates_timeout_to_status_one(self) -> None:
        failure = subprocess.TimeoutExpired("venv", 300)
        output = StringIO()

        with tempfile.TemporaryDirectory() as temporary_directory, patch(
            "cli.commands.create_command.ProjectGenerator.create",
            side_effect=failure,
        ), redirect_stdout(output):
            status = CreateCommand().execute(
                Namespace(
                    project_name="TimeoutDemo",
                    location=temporary_directory,
                    template="basic",
                )
            )

        self.assertEqual(status, 1)
        self.assertIn("[ERROR] Project creation failed", output.getvalue())
        self.assertIn("timed out", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())


if __name__ == "__main__":
    unittest.main()
