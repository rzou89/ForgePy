import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cli.command import Command
from cli.commands import create_commands
from cli.commands.component_command import ComponentCommand
from cli.dispatcher import Dispatcher
from cli.parser import Parser
from components.base_component import BaseComponent
from components.component_context import ComponentContext
from components.component_manifest import ComponentManifest
from components.component_metadata import ComponentMetadata
from components.component_registry import ComponentRegistry
from components.component_state import (
    ComponentStateIOError,
    ComponentStateStore,
)
from config.version import VERSION


class CliTestComponent(BaseComponent):

    def __init__(
        self,
        name: str,
        manifest: ComponentManifest,
    ) -> None:
        self._name = name
        self._manifest = manifest
        self.install_calls = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> ComponentMetadata:
        return ComponentMetadata(
            name=self.name,
            description="CLI test component.",
            version="1.0.0",
            author="ForgePy Tests",
            tags=("test",),
        )

    @property
    def manifest(self) -> ComponentManifest:
        return self._manifest

    def install(self, context: ComponentContext) -> None:
        self.install_calls += 1
        (context.project_path / f"{self.name}.txt").write_text(
            "installed\n",
            encoding="utf-8",
        )


class ComponentCommandTests(unittest.TestCase):

    def test_component_help_lists_supported_actions(self) -> None:
        output = StringIO()

        with patch("sys.argv", ["forgepy", "component", "--help"]):
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as context:
                    Parser().parse()

        self.assertEqual(context.exception.code, 0)
        self.assertIn("list", output.getvalue())
        self.assertIn("installed", output.getvalue())
        self.assertIn("add", output.getvalue())

    def test_component_installed_help_requires_project_path(self) -> None:
        output = StringIO()

        with patch(
            "sys.argv",
            ["forgepy", "component", "installed", "--help"],
        ):
            with redirect_stdout(output):
                with self.assertRaises(SystemExit) as context:
                    Parser().parse()

        self.assertEqual(context.exception.code, 0)
        self.assertIn("--project PATH", output.getvalue())

    def test_component_installed_reports_empty_saved_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            store = ComponentStateStore(project_path)
            store.save(())
            original_state = store.state_path.read_bytes()

            output = self._run_cli(
                "component", "installed", "--project", str(project_path)
            )

            self.assertEqual(output.strip(), "No installed components.")
            self.assertEqual(store.state_path.read_bytes(), original_state)

    def test_component_installed_treats_missing_state_as_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)

            output = self._run_cli(
                "component", "installed", "--project", str(project_path)
            )

            self.assertEqual(output.strip(), "No installed components.")
            self.assertFalse((project_path / ".forgepy").exists())

    def test_component_installed_displays_pytest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            ComponentStateStore(project_path).add("pytest")

            output = self._run_cli(
                "component", "installed", "--project", str(project_path)
            )

        self.assertEqual(output, "Installed components:\n- pytest\n")

    def test_component_installed_sorts_multiple_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            ComponentStateStore(project_path).save(("zeta", "alpha", "mid"))

            output = self._run_cli(
                "component", "installed", "--project", str(project_path)
            )

        self.assertEqual(
            output,
            "Installed components:\n- alpha\n- mid\n- zeta\n",
        )

    def test_component_installed_displays_unregistered_stored_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            ComponentStateStore(project_path).add("retired-component")

            with patch(
                "cli.commands.component_command.ComponentRegistry"
            ) as registry:
                output = self._run_cli(
                    "component", "installed", "--project", str(project_path)
                )

        registry.assert_not_called()
        self.assertIn("- retired-component", output)

    def test_component_installed_reports_malformed_state_without_writing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            store = ComponentStateStore(project_path)
            store.state_directory.mkdir()
            malformed = b'{"installed": ["broken"]'
            store.state_path.write_bytes(malformed)

            output = self._run_cli(
                "component", "installed", "--project", str(project_path)
            )

            self.assertIn("[ERROR]", output)
            self.assertIn("malformed JSON", output)
            self.assertNotIn("Traceback", output)
            self.assertEqual(store.state_path.read_bytes(), malformed)

    def test_component_installed_rejects_invalid_project_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory) / "missing"

            output = self._run_cli(
                "component", "installed", "--project", str(missing_path)
            )

        self.assertIn("[ERROR] Invalid project path", output)
        self.assertIn("must exist", output)
        self.assertNotIn("Traceback", output)

    def test_component_list_displays_name_and_description(self) -> None:
        output = self._run_cli("component", "list")

        self.assertIn("ForgePy Components", output)
        self.assertIn("pytest", output)
        self.assertIn(
            "Pytest configuration for an existing Python project.",
            output,
        )
        self.assertIn("ruff", output)
        self.assertIn(
            "Ruff configuration for an existing Python project.",
            output,
        )
        self.assertIn("github-actions", output)
        self.assertIn(
            "GitHub Actions CI for an existing Python project.",
            output,
        )

    def test_component_add_and_installed_support_github_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)

            add_output = self._run_cli(
                "component",
                "add",
                "github-actions",
                "--project",
                str(project_path),
            )
            installed_output = self._run_cli(
                "component",
                "installed",
                "--project",
                str(project_path),
            )

            self.assertIn(
                "[OK] Component 'github-actions' added",
                add_output,
            )
            self.assertTrue(
                (project_path / ".github/workflows/ci.yml").is_file()
            )
            self.assertEqual(
                installed_output,
                "Installed components:\n- github-actions\n",
            )

    def test_component_add_and_installed_support_ruff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)

            add_output = self._run_cli(
                "component",
                "add",
                "ruff",
                "--project",
                str(project_path),
            )
            installed_output = self._run_cli(
                "component",
                "installed",
                "--project",
                str(project_path),
            )

            self.assertIn("[OK] Component 'ruff' added", add_output)
            self.assertEqual(
                (project_path / "ruff.toml").read_text(encoding="utf-8"),
                'line-length = 88\ntarget-version = "py312"\n',
            )
            self.assertEqual(installed_output, "Installed components:\n- ruff\n")

    def test_component_add_installs_pytest_into_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory) / "project"
            project_path.mkdir()

            output = self._run_cli(
                "component",
                "add",
                "pytest",
                "--project",
                str(project_path),
            )

            self.assertIn("[OK] Component 'pytest' added", output)
            self.assertEqual(
                (project_path / "pytest.ini").read_text(encoding="utf-8"),
                "[pytest]\ntestpaths = tests\n",
            )
            self.assertEqual(
                ComponentStateStore(project_path).load(),
                frozenset(("pytest",)),
            )

    def test_component_add_rejects_second_install_as_already_installed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            first_output = self._run_cli(
                "component",
                "add",
                "pytest",
                "--project",
                str(project_path),
            )
            second_output = self._run_cli(
                "component",
                "add",
                "pytest",
                "--project",
                str(project_path),
            )

            self.assertIn("[OK] Component 'pytest' added", first_output)
            self.assertIn("[ERROR]", second_output)
            self.assertIn("already installed", second_output)
            self.assertNotIn("Traceback", second_output)
            self.assertEqual(
                ComponentStateStore(project_path).load(),
                frozenset(("pytest",)),
            )

    def test_component_add_rejects_unknown_component(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self._run_cli(
                "component",
                "add",
                "unknown",
                "--project",
                temporary_directory,
            )

        self.assertIn("[ERROR] Unknown ForgePy component: 'unknown'.", output)
        self.assertNotIn("Traceback", output)

    def test_component_install_hook_key_error_propagates(self) -> None:
        component = CliTestComponent(
            name="broken-hook",
            manifest=ComponentManifest(),
        )
        registry = ComponentRegistry()
        registry.register(component)
        command = ComponentCommand(registry=registry)

        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.object(
                component,
                "install",
                side_effect=KeyError("hook defect"),
            ):
                with self.assertRaisesRegex(KeyError, "hook defect"):
                    command._add(
                        component.name,
                        Path(temporary_directory),
                    )

    def test_component_add_rejects_invalid_project_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory) / "missing"
            output = self._run_cli(
                "component",
                "add",
                "pytest",
                "--project",
                str(missing_path),
            )

        self.assertIn("[ERROR] Invalid project path", output)
        self.assertIn("must exist", output)
        self.assertNotIn("Traceback", output)

    def test_component_add_refuses_existing_pytest_ini(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            target_path = project_path / "pytest.ini"
            target_path.write_text("existing\n", encoding="utf-8")

            output = self._run_cli(
                "component",
                "add",
                "pytest",
                "--project",
                str(project_path),
            )

            self.assertIn("[ERROR] Component installation refused", output)
            self.assertIn("already exists", output)
            self.assertEqual(
                target_path.read_text(encoding="utf-8"),
                "existing\n",
            )
            self.assertFalse(
                ComponentStateStore(project_path).state_path.exists()
            )

    def test_component_add_rejects_malformed_state_before_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            store = ComponentStateStore(project_path)
            store.state_directory.mkdir()
            malformed = b'{"installed": ["broken"]'
            store.state_path.write_bytes(malformed)

            output = self._run_cli(
                "component",
                "add",
                "pytest",
                "--project",
                str(project_path),
            )

            self.assertIn("[ERROR]", output)
            self.assertIn("malformed JSON", output)
            self.assertNotIn("Traceback", output)
            self.assertFalse((project_path / "pytest.ini").exists())
            self.assertEqual(store.state_path.read_bytes(), malformed)

    def test_component_add_displays_state_confinement_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            project_path = temporary_path / "project"
            outside_path = temporary_path / "outside"
            project_path.mkdir()
            outside_path.mkdir()

            try:
                os.symlink(
                    outside_path,
                    project_path / ".forgepy",
                    target_is_directory=True,
                )
            except OSError as error:
                self.skipTest(
                    "Directory symlink creation is unavailable: "
                    f"{error}"
                )

            output = self._run_cli(
                "component",
                "add",
                "pytest",
                "--project",
                str(project_path),
            )

            self.assertIn("[ERROR]", output)
            self.assertIn("resolves outside", output)
            self.assertNotIn("Traceback", output)
            self.assertFalse((project_path / "pytest.ini").exists())
            self.assertEqual(tuple(outside_path.iterdir()), ())

    def test_component_add_displays_missing_dependency_error(self) -> None:
        component = CliTestComponent(
            name="dependent",
            manifest=ComponentManifest(dependencies=("required",)),
        )

        output = self._run_custom_component(component)

        self.assertIn("[ERROR]", output)
        self.assertIn("missing dependencies: required", output)
        self.assertNotIn("Traceback", output)
        self.assertEqual(component.install_calls, 0)

    def test_component_add_displays_active_conflict_error(self) -> None:
        component = CliTestComponent(
            name="conflicting",
            manifest=ComponentManifest(conflicts=("incompatible",)),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            ComponentStateStore(project_path).add("incompatible")
            output = self._run_custom_component(
                component,
                project_path=project_path,
            )

        self.assertIn("[ERROR]", output)
        self.assertIn("active conflicts: incompatible", output)
        self.assertNotIn("Traceback", output)
        self.assertEqual(component.install_calls, 0)

    def test_component_add_displays_state_persistence_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)

            with patch.object(
                ComponentStateStore,
                "add",
                side_effect=ComponentStateIOError("state failed"),
            ):
                output = self._run_cli(
                    "component",
                    "add",
                    "pytest",
                    "--project",
                    str(project_path),
                )

            self.assertIn("[ERROR] state failed", output)
            self.assertNotIn("[OK]", output)
            self.assertNotIn("Traceback", output)
            self.assertTrue((project_path / "pytest.ini").exists())

    def test_component_add_writes_nothing_outside_supplied_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root_path = Path(temporary_directory)
            project_path = root_path / "project"
            outside_path = root_path / "outside"
            project_path.mkdir()
            outside_path.mkdir()

            self._run_cli(
                "component",
                "add",
                "pytest",
                "--project",
                str(project_path),
            )

            self.assertEqual(tuple(outside_path.iterdir()), ())
            self.assertEqual(
                sorted(path.name for path in project_path.iterdir()),
                [".forgepy", "pytest.ini"],
            )

    def test_component_list_does_not_invoke_installer(self) -> None:
        with patch(
            "cli.commands.component_command.ComponentInstaller.install"
        ) as install:
            output = self._run_cli("component", "list")

        install.assert_not_called()
        self.assertIn("pytest", output)

    def test_existing_cli_commands_remain_registered(self) -> None:
        command_names = tuple(command.name for command in create_commands())

        self.assertEqual(
            command_names,
            ("create", "version", "list", "config", "component"),
        )

    def test_forgepy_version_matches_release(self) -> None:
        self.assertEqual(VERSION, "1.1.0")

    @staticmethod
    def _run_cli(
        *arguments: str,
        commands: tuple[Command, ...] | None = None,
    ) -> str:
        output = StringIO()

        with patch("sys.argv", ["forgepy", *arguments]):
            with redirect_stdout(output):
                args = Parser(commands=commands).parse()
                Dispatcher(commands=commands).dispatch(args)

        return output.getvalue()

    def _run_custom_component(
        self,
        component: BaseComponent,
        project_path: Path | None = None,
    ) -> str:
        registry = ComponentRegistry()
        registry.register(component)
        commands = tuple(
            ComponentCommand(registry=registry)
            if isinstance(command, ComponentCommand)
            else command
            for command in create_commands()
        )

        if project_path is not None:
            return self._run_cli(
                "component",
                "add",
                component.name,
                "--project",
                str(project_path),
                commands=commands,
            )

        with tempfile.TemporaryDirectory() as temporary_directory:
            return self._run_cli(
                "component",
                "add",
                component.name,
                "--project",
                temporary_directory,
                commands=commands,
            )


if __name__ == "__main__":
    unittest.main()
