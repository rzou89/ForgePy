import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from components.component_registry import ComponentRegistry
from components.component_state import (
    ComponentStateFormatError,
    ComponentStateIOError,
    ComponentStateStore,
)


class ComponentStateStoreTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.temporary_path = Path(self.temporary_directory.name)
        self.project_path = self.temporary_path / "project"
        self.outside_path = self.temporary_path / "outside"
        self.project_path.mkdir()
        self.outside_path.mkdir()
        self.store = ComponentStateStore(self.project_path)

    def test_missing_state_returns_empty_installed_set(self) -> None:
        self.assertEqual(self.store.load(), frozenset())
        self.assertFalse(self.store.state_directory.exists())

    def test_save_creates_state_directory(self) -> None:
        self.store.save(())

        self.assertTrue(self.store.state_directory.is_dir())
        self.assertTrue(self.store.state_path.is_file())

    def test_save_uses_existing_in_project_state_directory(self) -> None:
        self.store.state_directory.mkdir()

        self.store.save(("pytest",))

        self.assertEqual(self.store.load(), frozenset(("pytest",)))

    def test_state_directory_file_is_rejected(self) -> None:
        original = b"not a directory"
        self.store.state_directory.write_bytes(original)

        operations = (
            self.store.load,
            lambda: self.store.save(("pytest",)),
        )

        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(ComponentStateIOError):
                operation()

        self.assertEqual(self.store.state_directory.read_bytes(), original)

    def test_save_and_load_round_trip(self) -> None:
        saved = self.store.save(("pytest", "lint"))

        self.assertEqual(saved, frozenset(("pytest", "lint")))
        self.assertEqual(self.store.load(), saved)

    def test_persisted_names_have_deterministic_order(self) -> None:
        self.store.save(("zeta", "alpha", "middle"))

        data = json.loads(self.store.state_path.read_text(encoding="utf-8"))
        self.assertEqual(
            data,
            {"installed": ["alpha", "middle", "zeta"]},
        )

    def test_duplicate_names_are_normalized_on_save_and_load(self) -> None:
        self.store.save(("pytest", "pytest"))
        self.assertEqual(self.store.load(), frozenset(("pytest",)))

        self.store.state_path.write_text(
            '{"installed": ["lint", "lint"]}\n',
            encoding="utf-8",
        )
        self.assertEqual(self.store.load(), frozenset(("lint",)))

    def test_add_installed_component_preserves_existing_names(self) -> None:
        self.store.save(("pytest",))

        installed = self.store.add("lint")

        self.assertEqual(installed, frozenset(("pytest", "lint")))
        self.assertEqual(self.store.load(), installed)

    def test_membership_check_reads_installed_state(self) -> None:
        self.store.save(("pytest",))

        self.assertTrue(self.store.is_installed("pytest"))
        self.assertFalse(self.store.is_installed("lint"))

    def test_malformed_json_raises_clear_error(self) -> None:
        self._write_raw(b'{"installed": ["pytest"]')

        with self.assertRaisesRegex(
            ComponentStateFormatError,
            "malformed JSON",
        ):
            self.store.load()

    def test_invalid_top_level_structure_is_rejected(self) -> None:
        for data in ([], {"unexpected": []}, {"installed": [], "extra": 1}):
            with self.subTest(data=data):
                self._write_json(data)

                with self.assertRaises(ComponentStateFormatError):
                    self.store.load()

    def test_invalid_installed_entry_is_rejected(self) -> None:
        for entry in (None, 1, "", "   "):
            with self.subTest(entry=entry):
                self._write_json({"installed": [entry]})

                with self.assertRaises(ComponentStateFormatError):
                    self.store.load()

    def test_writes_preserve_malformed_existing_data(self) -> None:
        malformed = b'{"installed": ["pytest"]'
        self._write_raw(malformed)

        for operation in (
            lambda: self.store.save(("lint",)),
            lambda: self.store.add("lint"),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(ComponentStateFormatError):
                    operation()

                self.assertEqual(
                    self.store.state_path.read_bytes(),
                    malformed,
                )

    def test_atomic_write_failure_preserves_existing_valid_state(self) -> None:
        self.store.save(("pytest",))
        original = self.store.state_path.read_bytes()
        original_replace = Path.replace
        resolved_state_path = self.store.state_path.resolve()

        def fail_for_temporary_file(source: Path, target: Path) -> Path:
            if target.resolve() == resolved_state_path:
                raise OSError("replace failed")
            return original_replace(source, target)

        with (
            patch.object(Path, "replace", fail_for_temporary_file),
            self.assertRaisesRegex(
                ComponentStateIOError,
                "could not save",
            ),
        ):
            self.store.save(("lint",))

        self.assertEqual(self.store.state_path.read_bytes(), original)
        self.assertEqual(
            tuple(self.store.state_directory.glob("*.tmp")),
            (),
        )

    def test_atomic_temporary_file_uses_validated_state_directory(self) -> None:
        original_named_temporary_file = tempfile.NamedTemporaryFile
        temporary_directories: list[Path] = []

        def record_directory(*args: object, **kwargs: object):
            temporary_directories.append(Path(kwargs["dir"]))
            return original_named_temporary_file(*args, **kwargs)

        with patch(
            "components.component_state.tempfile.NamedTemporaryFile",
            side_effect=record_directory,
        ):
            self.store.save(("pytest",))

        self.assertEqual(
            temporary_directories,
            [self.store.state_directory.resolve()],
        )
        self.assertEqual(tuple(self.outside_path.iterdir()), ())

    def test_outside_state_directory_link_rejects_read_and_write(self) -> None:
        outside_state = self.outside_path / "state"
        outside_state.mkdir()
        outside_file = outside_state / "components.json"
        original = b'{"installed": ["outside"]}\n'
        outside_file.write_bytes(original)
        self._create_directory_symlink(
            outside_state,
            self.store.state_directory,
        )

        operations = (
            self.store.load,
            lambda: self.store.save(("pytest",)),
        )

        for operation in operations:
            with self.subTest(operation=operation), self.assertRaisesRegex(
                ComponentStateIOError,
                "resolves outside",
            ):
                operation()

        self.assertTrue(self.store.state_directory.is_symlink())
        self.assertEqual(outside_file.read_bytes(), original)
        self.assertEqual(tuple(outside_state.iterdir()), (outside_file,))

    def test_outside_state_file_link_rejects_read_and_write(self) -> None:
        self.store.state_directory.mkdir()
        outside_file = self.outside_path / "components.json"
        original = b'{"installed": ["outside"]}\n'
        outside_file.write_bytes(original)
        self._create_file_symlink(outside_file, self.store.state_path)

        operations = (
            self.store.load,
            lambda: self.store.save(("pytest",)),
        )

        for operation in operations:
            with self.subTest(operation=operation), self.assertRaisesRegex(
                ComponentStateIOError,
                "resolves outside",
            ):
                operation()

        self.assertTrue(self.store.state_path.is_symlink())
        self.assertEqual(outside_file.read_bytes(), original)
        self.assertEqual(tuple(self.outside_path.iterdir()), (outside_file,))

    def test_state_store_writes_nothing_outside_project(self) -> None:
        self.store.add("pytest")

        self.assertEqual(tuple(self.outside_path.iterdir()), ())
        self.assertEqual(
            self.store.state_path.relative_to(self.project_path),
            Path(".forgepy/components.json"),
        )

    def test_registry_remains_installation_state_agnostic(self) -> None:
        registry = ComponentRegistry()
        registered_before_state_change = tuple(
            component.name for component in registry.list_components()
        )

        self.store.add("external")

        self.assertEqual(
            tuple(component.name for component in registry.list_components()),
            registered_before_state_change,
        )
        with self.assertRaises(KeyError):
            registry.get("external")

    def _write_json(self, data: object) -> None:
        self._write_raw(
            (json.dumps(data) + "\n").encode("utf-8")
        )

    def _write_raw(self, content: bytes) -> None:
        self.store.state_directory.mkdir(parents=True, exist_ok=True)
        self.store.state_path.write_bytes(content)

    def _create_directory_symlink(self, target: Path, link: Path) -> None:
        try:
            os.symlink(target, link, target_is_directory=True)
        except OSError as error:
            self.skipTest(
                "Directory symlink creation is unavailable: "
                f"{error}"
            )

    def _create_file_symlink(self, target: Path, link: Path) -> None:
        try:
            os.symlink(target, link)
        except OSError as error:
            self.skipTest(
                f"File symlink creation is unavailable: {error}"
            )


if __name__ == "__main__":
    unittest.main()
