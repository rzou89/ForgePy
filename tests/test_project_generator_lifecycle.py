"""Project generation lifecycle-order regression tests."""

import subprocess
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from core.git_builder import GitBuilder
from core.project_generator import ProjectGenerator
from core.vscode_builder import VSCodeBuilder


class ProjectGeneratorLifecycleTests(unittest.TestCase):

    def test_vscode_files_exist_before_git_after_prior_stages(self) -> None:
        events: list[str] = []
        vscode_create = VSCodeBuilder.create

        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            project_root = parent / "LifecycleDemo"

            def environment(root: Path) -> None:
                self.assertTrue((root / "app.py").is_file())
                events.append("environment")

            def vscode(
                builder: VSCodeBuilder,
                root: Path,
                entry_point: str | None = "app.py",
            ) -> None:
                events.append("vscode")
                vscode_create(builder, root, entry_point)

            def git(root: Path) -> None:
                self.assertEqual(
                    {
                        path.name
                        for path in (root / ".vscode").iterdir()
                        if path.is_file()
                    },
                    {
                        "extensions.json",
                        "launch.json",
                        "settings.json",
                        "tasks.json",
                    },
                )
                events.append("git")

            with ExitStack() as stack:
                stack.enter_context(
                    patch(
                        "core.project_generator.EnvironmentBuilder.create",
                        side_effect=environment,
                    )
                )
                stack.enter_context(
                    patch(
                        "core.project_generator.PythonToolsBuilder.update",
                        side_effect=lambda root: events.append("python-tools"),
                    )
                )
                stack.enter_context(
                    patch(
                        "core.project_generator.RequirementsInstaller.install",
                        side_effect=lambda root: events.append("requirements"),
                    )
                )
                stack.enter_context(
                    patch(
                        "core.project_generator.VSCodeBuilder.create",
                        autospec=True,
                        side_effect=vscode,
                    )
                )
                stack.enter_context(
                    patch(
                        "core.project_generator.GitBuilder.create",
                        side_effect=git,
                    )
                )
                stack.enter_context(redirect_stdout(StringIO()))

                ProjectGenerator().create(
                    project_name=project_root.name,
                    location=str(parent),
                    template_name="basic",
                )

            self.assertEqual(
                events,
                [
                    "environment",
                    "python-tools",
                    "requirements",
                    "vscode",
                    "git",
                ],
            )

    def test_vscode_failure_prevents_git_and_success_reporting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            output = StringIO()

            with ExitStack() as stack:
                stack.enter_context(
                    patch("core.project_generator.EnvironmentBuilder.create")
                )
                stack.enter_context(
                    patch("core.project_generator.PythonToolsBuilder.update")
                )
                stack.enter_context(
                    patch(
                        "core.project_generator.RequirementsInstaller.install"
                    )
                )
                stack.enter_context(
                    patch(
                        "core.project_generator.VSCodeBuilder.create",
                        side_effect=OSError("VS Code write failed"),
                    )
                )
                git = stack.enter_context(
                    patch("core.project_generator.GitBuilder.create")
                )

                with redirect_stdout(output), self.assertRaisesRegex(OSError, "VS Code write failed"):
                    ProjectGenerator().create(
                        project_name="VSCodeFailure",
                        location=str(parent),
                        template_name="basic",
                    )

            git.assert_not_called()
            self.assertNotIn("Project berhasil dibuat", output.getvalue())

    def test_git_failure_prevents_success_reporting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            output = StringIO()
            failure = subprocess.CalledProcessError(1, ["git", "commit"])

            with ExitStack() as stack:
                stack.enter_context(
                    patch("core.project_generator.EnvironmentBuilder.create")
                )
                stack.enter_context(
                    patch("core.project_generator.PythonToolsBuilder.update")
                )
                stack.enter_context(
                    patch(
                        "core.project_generator.RequirementsInstaller.install"
                    )
                )
                stack.enter_context(
                    patch("core.project_generator.VSCodeBuilder.create")
                )
                stack.enter_context(
                    patch(
                        "core.project_generator.GitBuilder.create",
                        side_effect=failure,
                    )
                )

                with redirect_stdout(output), self.assertRaises(subprocess.CalledProcessError):
                    ProjectGenerator().create(
                        project_name="GitFailure",
                        location=str(parent),
                        template_name="basic",
                    )

            self.assertNotIn("Project berhasil dibuat", output.getvalue())

    def test_missing_git_preserves_partial_project_without_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            project_root = parent / "MissingGit"
            output = StringIO()

            with ExitStack() as stack:
                stack.enter_context(
                    patch("core.project_generator.EnvironmentBuilder.create")
                )
                stack.enter_context(
                    patch("core.project_generator.PythonToolsBuilder.update")
                )
                stack.enter_context(
                    patch(
                        "core.project_generator.RequirementsInstaller.install"
                    )
                )
                stack.enter_context(
                    patch("core.git_builder.shutil.which", return_value=None)
                )

                with redirect_stdout(output), self.assertRaisesRegex(
                    FileNotFoundError,
                    "Git executable is required",
                ):
                    ProjectGenerator().create(
                        project_name=project_root.name,
                        location=str(parent),
                        template_name="basic",
                    )

            self.assertTrue((project_root / "app.py").is_file())
            self.assertTrue((project_root / ".vscode").is_dir())
            self.assertNotIn("Project berhasil dibuat", output.getvalue())


class GitBuilderFailureTests(unittest.TestCase):

    def test_missing_git_is_reported_as_required_without_subprocess(self) -> None:
        output = StringIO()

        with patch("core.git_builder.shutil.which", return_value=None), patch("core.git_builder.subprocess.run") as run, redirect_stdout(output), self.assertRaisesRegex(
            FileNotFoundError,
            "Git executable is required but was not found",
        ):
            GitBuilder().create(Path("project"))

        run.assert_not_called()
        self.assertNotIn("Git Repository berhasil dibuat", output.getvalue())

    def test_commit_failure_is_reported_and_propagated(self) -> None:
        failure = subprocess.CalledProcessError(1, ["git", "commit"])

        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            output = StringIO()

            with patch("core.git_builder.shutil.which", return_value="git"), patch(
                "core.git_builder.subprocess.run",
                side_effect=[None, None, failure],
            ), redirect_stdout(output), self.assertRaises(subprocess.CalledProcessError):
                GitBuilder().create(project_root)

        self.assertIn("Initial Commit gagal", output.getvalue())
        self.assertNotIn("Git Repository berhasil dibuat", output.getvalue())


if __name__ == "__main__":
    unittest.main()
