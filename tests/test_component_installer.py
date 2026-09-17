import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from components.base_component import BaseComponent
from components.component_context import ComponentContext
from components.component_installer import (
    ComponentAlreadyInstalledError,
    ComponentInstaller,
)
from components.component_manifest import ComponentManifest
from components.component_metadata import ComponentMetadata
from components.component_registry import ComponentRegistry
from components.component_state import (
    ComponentStateFormatError,
    ComponentStateIOError,
    ComponentStateStore,
)
from components.component_validation import ComponentValidationError


class InstallerTestComponent(BaseComponent):

    def __init__(
        self,
        name: str = "example",
        manifest: ComponentManifest | None = None,
        install_error: Exception | None = None,
    ) -> None:
        self._name = name
        self._manifest = manifest or ComponentManifest()
        self._install_error = install_error
        self.install_calls = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> ComponentMetadata:
        return ComponentMetadata(
            name=self.name,
            description="Installer test component.",
            version="1.0.0",
            author="ForgePy Tests",
            tags=("test",),
        )

    @property
    def manifest(self) -> ComponentManifest:
        return self._manifest

    def install(self, context: ComponentContext) -> None:
        self.install_calls += 1

        if self._install_error is not None:
            raise self._install_error

        (context.project_path / f"{self.name}.txt").write_text(
            "installed\n",
            encoding="utf-8",
        )


class ComponentInstallerTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.temporary_path = Path(self.temporary_directory.name)
        self.project_path = self.temporary_path / "project"
        self.outside_path = self.temporary_path / "outside"
        self.project_path.mkdir()
        self.outside_path.mkdir()
        self.registry = ComponentRegistry()

    def test_successful_orchestration_installs_and_records_component(
        self,
    ) -> None:
        component = self._register()

        self._installer().install(component.name, self.project_path)

        self.assertEqual(component.install_calls, 1)
        self.assertTrue((self.project_path / "example.txt").is_file())
        self.assertEqual(
            ComponentStateStore(self.project_path).load(),
            frozenset(("example",)),
        )

    def test_already_installed_component_is_rejected_before_install(
        self,
    ) -> None:
        component = self._register()
        store = ComponentStateStore(self.project_path)
        store.add(component.name)
        original = store.state_path.read_bytes()

        with self.assertRaises(ComponentAlreadyInstalledError):
            self._installer().install(component.name, self.project_path)

        self.assertEqual(component.install_calls, 0)
        self.assertEqual(store.state_path.read_bytes(), original)

    def test_missing_dependency_is_rejected_before_install(self) -> None:
        component = self._register(
            manifest=ComponentManifest(dependencies=("required",))
        )

        with self.assertRaises(ComponentValidationError):
            self._installer().install(component.name, self.project_path)

        self.assertEqual(component.install_calls, 0)
        self.assertFalse(
            ComponentStateStore(self.project_path).state_path.exists()
        )

    def test_active_conflict_is_rejected_before_install(self) -> None:
        component = self._register(
            manifest=ComponentManifest(conflicts=("incompatible",))
        )
        store = ComponentStateStore(self.project_path)
        store.add("incompatible")
        original = store.state_path.read_bytes()

        with self.assertRaises(ComponentValidationError):
            self._installer().install(component.name, self.project_path)

        self.assertEqual(component.install_calls, 0)
        self.assertEqual(store.state_path.read_bytes(), original)

    def test_malformed_state_aborts_before_install(self) -> None:
        component = self._register()
        store = ComponentStateStore(self.project_path)
        store.state_directory.mkdir()
        malformed = b'{"installed": ["broken"]'
        store.state_path.write_bytes(malformed)

        with self.assertRaises(ComponentStateFormatError):
            self._installer().install(component.name, self.project_path)

        self.assertEqual(component.install_calls, 0)
        self.assertEqual(store.state_path.read_bytes(), malformed)

    def test_state_confinement_failure_aborts_before_install(self) -> None:
        component = self._register()
        state_directory = self.project_path / ".forgepy"

        try:
            os.symlink(
                self.outside_path,
                state_directory,
                target_is_directory=True,
            )
        except OSError as error:
            self.skipTest(
                "Directory symlink creation is unavailable: "
                f"{error}"
            )

        with self.assertRaisesRegex(
            ComponentStateIOError,
            "resolves outside",
        ):
            self._installer().install(component.name, self.project_path)

        self.assertEqual(component.install_calls, 0)
        self.assertFalse((self.project_path / "example.txt").exists())
        self.assertEqual(tuple(self.outside_path.iterdir()), ())

    def test_component_install_failure_leaves_state_unchanged(self) -> None:
        component = self._register(install_error=RuntimeError("failed"))
        store = ComponentStateStore(self.project_path)
        store.add("existing")
        original = store.state_path.read_bytes()

        with self.assertRaisesRegex(RuntimeError, "failed"):
            self._installer().install(component.name, self.project_path)

        self.assertEqual(component.install_calls, 1)
        self.assertEqual(store.state_path.read_bytes(), original)

    def test_existing_pytest_target_leaves_state_unchanged(self) -> None:
        target = self.project_path / "pytest.ini"
        target.write_text("existing\n", encoding="utf-8")

        with self.assertRaises(FileExistsError):
            self._installer().install("pytest", self.project_path)

        self.assertEqual(target.read_text(encoding="utf-8"), "existing\n")
        self.assertFalse(
            ComponentStateStore(self.project_path).state_path.exists()
        )

    def test_state_save_failure_after_install_is_surfaced(self) -> None:
        component = self._register()

        with patch.object(
            ComponentStateStore,
            "add",
            side_effect=ComponentStateIOError("state failed"),
        ), self.assertRaisesRegex(
            ComponentStateIOError,
            "state failed",
        ):
            self._installer().install(component.name, self.project_path)

        self.assertEqual(component.install_calls, 1)
        self.assertTrue((self.project_path / "example.txt").is_file())
        self.assertFalse(
            ComponentStateStore(self.project_path).state_path.exists()
        )

    def test_registry_remains_installation_agnostic(self) -> None:
        component = self._register()
        registered_before_install = tuple(
            item.name for item in self.registry.list_components()
        )

        self._installer().install(component.name, self.project_path)

        self.assertIs(self.registry.get(component.name), component)
        self.assertEqual(
            tuple(item.name for item in self.registry.list_components()),
            registered_before_install,
        )

    def test_orchestration_writes_nothing_outside_project(self) -> None:
        component = self._register()

        self._installer().install(component.name, self.project_path)

        self.assertEqual(tuple(self.outside_path.iterdir()), ())
        self.assertEqual(
            sorted(
                path.relative_to(self.project_path).as_posix()
                for path in self.project_path.rglob("*")
                if path.is_file()
            ),
            [".forgepy/components.json", "example.txt"],
        )

    def test_state_document_records_only_successful_component(self) -> None:
        component = self._register()

        self._installer().install(component.name, self.project_path)

        state_path = ComponentStateStore(self.project_path).state_path
        self.assertEqual(
            json.loads(state_path.read_text(encoding="utf-8")),
            {"installed": ["example"]},
        )

    def _register(
        self,
        manifest: ComponentManifest | None = None,
        install_error: Exception | None = None,
    ) -> InstallerTestComponent:
        component = InstallerTestComponent(
            manifest=manifest,
            install_error=install_error,
        )
        self.registry.register(component)
        return component

    def _installer(self) -> ComponentInstaller:
        return ComponentInstaller(registry=self.registry)


if __name__ == "__main__":
    unittest.main()
