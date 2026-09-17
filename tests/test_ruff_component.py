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
from components.ruff_component import RuffComponent

EXPECTED_CONFIGURATION = (
    'line-length = 88\n'
    'target-version = "py312"\n'
)


class RuffComponentTests(unittest.TestCase):

    def test_metadata_describes_the_ruff_component(self) -> None:
        metadata = RuffComponent().metadata

        self.assertEqual(metadata.name, "ruff")
        self.assertEqual(
            metadata.description,
            "Ruff configuration for an existing Python project.",
        )
        self.assertEqual(metadata.version, "0.1.0")
        self.assertEqual(metadata.author, "ForgePy")
        self.assertEqual(metadata.tags, ("linting", "ruff"))

    def test_manifest_declares_only_ruff_toml(self) -> None:
        manifest = RuffComponent().manifest

        self.assertEqual(manifest.files, (Path("ruff.toml"),))
        self.assertEqual(manifest.dependencies, ())
        self.assertEqual(manifest.conflicts, ())

    def test_default_registry_registers_ruff_after_pytest(self) -> None:
        registry = ComponentRegistry()

        self.assertIsInstance(registry.get("ruff"), RuffComponent)
        self.assertEqual(registry.list_components()[1].name, "ruff")

    def test_install_creates_exact_declared_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            component = RuffComponent()

            component.install(ComponentContext(project_path))

            self.assertEqual(
                (project_path / "ruff.toml").read_text(encoding="utf-8"),
                EXPECTED_CONFIGURATION,
            )
            installed_files = tuple(
                path.relative_to(project_path)
                for path in project_path.rglob("*")
                if path.is_file()
            )
            self.assertEqual(installed_files, component.manifest.files)

    def test_install_refuses_existing_ruff_toml(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            target_path = project_path / "ruff.toml"
            target_path.write_text("user content\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                RuffComponent().install(ComponentContext(project_path))

            self.assertEqual(
                target_path.read_text(encoding="utf-8"),
                "user content\n",
            )

    def test_repeated_direct_install_preserves_first_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            component = RuffComponent()
            context = ComponentContext(project_path)
            component.install(context)
            original_content = (project_path / "ruff.toml").read_bytes()

            with self.assertRaises(FileExistsError):
                component.install(context)

            self.assertEqual(
                (project_path / "ruff.toml").read_bytes(),
                original_content,
            )

    def test_install_writes_nothing_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root_path = Path(temporary_directory)
            project_path = root_path / "project"
            outside_path = root_path / "outside"
            project_path.mkdir()
            outside_path.mkdir()

            RuffComponent().install(ComponentContext(project_path))

            self.assertEqual(tuple(outside_path.iterdir()), ())
            self.assertEqual(
                tuple(path.name for path in project_path.iterdir()),
                ("ruff.toml",),
            )

    def test_existing_installer_records_ruff_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)
            installer = ComponentInstaller()

            installer.install("ruff", project_path)

            self.assertEqual(
                ComponentStateStore(project_path).load(),
                frozenset(("ruff",)),
            )
            self.assertEqual(
                (project_path / "ruff.toml").read_text(encoding="utf-8"),
                EXPECTED_CONFIGURATION,
            )

            with self.assertRaises(ComponentAlreadyInstalledError):
                installer.install("ruff", project_path)


if __name__ == "__main__":
    unittest.main()
