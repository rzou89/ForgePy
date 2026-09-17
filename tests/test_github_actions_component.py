import os
import tempfile
import unittest
from pathlib import Path

from components.component_context import ComponentContext
from components.component_installer import (
    ComponentAlreadyInstalledError,
    ComponentInstaller,
)
from components.component_registry import ComponentRegistry
from components.component_state import ComponentStateStore
from components.github_actions_component import GitHubActionsComponent

EXPECTED_WORKFLOW = (
    "name: CI\n"
    "\n"
    "on:\n"
    "  push:\n"
    "  pull_request:\n"
    "\n"
    "jobs:\n"
    "  test:\n"
    "    runs-on: ubuntu-latest\n"
    "    steps:\n"
    "      - uses: actions/checkout@v4\n"
    "      - uses: actions/setup-python@v5\n"
    "        with:\n"
    '          python-version: "3.12"\n'
    "      - name: Install CI tools\n"
    "        run: python -m pip install pytest ruff\n"
    "      - name: Run Ruff\n"
    "        run: ruff check .\n"
    "      - name: Run pytest\n"
    "        run: pytest\n"
)


class GitHubActionsComponentTests(unittest.TestCase):

    def test_metadata_describes_the_github_actions_component(self) -> None:
        metadata = GitHubActionsComponent().metadata

        self.assertEqual(metadata.name, "github-actions")
        self.assertEqual(
            metadata.description,
            "GitHub Actions CI for an existing Python project.",
        )
        self.assertEqual(metadata.version, "0.1.0")
        self.assertEqual(metadata.author, "ForgePy")
        self.assertEqual(
            metadata.tags,
            ("ci", "github-actions", "python"),
        )

    def test_manifest_declares_only_the_ci_workflow(self) -> None:
        manifest = GitHubActionsComponent().manifest

        self.assertEqual(
            manifest.files,
            (Path(".github/workflows/ci.yml"),),
        )
        self.assertEqual(manifest.dependencies, ())
        self.assertEqual(manifest.conflicts, ())

    def test_default_registry_has_the_authoritative_component_order(self) -> None:
        registry = ComponentRegistry()

        self.assertIsInstance(
            registry.get("github-actions"),
            GitHubActionsComponent,
        )
        self.assertEqual(
            tuple(component.name for component in registry.list_components()),
            ("pytest", "ruff", "github-actions"),
        )

    def test_install_creates_exact_workflow_and_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            component = GitHubActionsComponent()

            component.install(ComponentContext(project_path))

            workflow_path = project_path / ".github/workflows/ci.yml"
            self.assertTrue(workflow_path.parent.is_dir())
            self.assertEqual(
                workflow_path.read_text(encoding="utf-8"),
                EXPECTED_WORKFLOW,
            )
            self.assertNotIn(b"\r\n", workflow_path.read_bytes())
            installed_files = tuple(
                path.relative_to(project_path)
                for path in project_path.rglob("*")
                if path.is_file()
            )
            self.assertEqual(installed_files, component.manifest.files)

    def test_install_refuses_and_preserves_an_existing_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            workflow_path = project_path / ".github/workflows/ci.yml"
            workflow_path.parent.mkdir(parents=True)
            workflow_path.write_text("user workflow\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                GitHubActionsComponent().install(
                    ComponentContext(project_path)
                )

            self.assertEqual(
                workflow_path.read_text(encoding="utf-8"),
                "user workflow\n",
            )

    def test_installer_refuses_when_github_is_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            github_path = project_path / ".github"
            github_path.write_text("user content\n", encoding="utf-8")

            with self.assertRaises(OSError):
                ComponentInstaller().install("github-actions", project_path)

            self.assertEqual(
                github_path.read_text(encoding="utf-8"),
                "user content\n",
            )
            self.assertFalse(
                ComponentStateStore(project_path).state_path.exists()
            )

    def test_installer_refuses_when_workflows_is_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            github_path = project_path / ".github"
            github_path.mkdir()
            workflows_path = github_path / "workflows"
            workflows_path.write_text("user content\n", encoding="utf-8")

            with self.assertRaises(OSError):
                ComponentInstaller().install("github-actions", project_path)

            self.assertEqual(
                workflows_path.read_text(encoding="utf-8"),
                "user content\n",
            )
            self.assertFalse(
                ComponentStateStore(project_path).state_path.exists()
            )

    def test_install_rejects_parent_symlink_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root_path = Path(temporary_directory)
            project_path = root_path / "project"
            outside_path = root_path / "outside"
            project_path.mkdir()
            outside_path.mkdir()

            try:
                os.symlink(
                    outside_path,
                    project_path / ".github",
                    target_is_directory=True,
                )
            except OSError as error:
                self.skipTest(
                    "Directory symlink creation is unavailable: "
                    f"{error}"
                )

            with self.assertRaisesRegex(
                OSError,
                "resolves outside the project",
            ):
                GitHubActionsComponent().install(
                    ComponentContext(project_path)
                )

            self.assertFalse((outside_path / "workflows/ci.yml").exists())

    def test_install_preserves_unrelated_github_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            github_path = project_path / ".github"
            github_path.mkdir()
            unrelated_path = github_path / "CODEOWNERS"
            unrelated_path.write_text("* @owner\n", encoding="utf-8")

            GitHubActionsComponent().install(ComponentContext(project_path))

            self.assertEqual(
                unrelated_path.read_text(encoding="utf-8"),
                "* @owner\n",
            )
            self.assertTrue(
                (github_path / "workflows/ci.yml").is_file()
            )

    def test_repeated_direct_install_preserves_first_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            component = GitHubActionsComponent()
            context = ComponentContext(project_path)
            component.install(context)
            workflow_path = project_path / ".github/workflows/ci.yml"
            original_content = workflow_path.read_bytes()

            with self.assertRaises(FileExistsError):
                component.install(context)

            self.assertEqual(workflow_path.read_bytes(), original_content)

    def test_existing_installer_installs_records_and_rejects_repeat(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            installer = ComponentInstaller()

            installer.install("github-actions", project_path)

            self.assertEqual(
                ComponentStateStore(project_path).load(),
                frozenset(("github-actions",)),
            )
            self.assertEqual(
                (project_path / ".github/workflows/ci.yml").read_text(
                    encoding="utf-8"
                ),
                EXPECTED_WORKFLOW,
            )

            with self.assertRaises(ComponentAlreadyInstalledError):
                installer.install("github-actions", project_path)

    def test_install_writes_nothing_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root_path = Path(temporary_directory)
            project_path = root_path / "project"
            outside_path = root_path / "outside"
            project_path.mkdir()
            outside_path.mkdir()

            GitHubActionsComponent().install(ComponentContext(project_path))

            self.assertEqual(tuple(outside_path.iterdir()), ())
            self.assertEqual(
                tuple(
                    path.relative_to(project_path)
                    for path in project_path.rglob("*")
                    if path.is_file()
                ),
                (Path(".github/workflows/ci.yml"),),
            )


if __name__ == "__main__":
    unittest.main()
