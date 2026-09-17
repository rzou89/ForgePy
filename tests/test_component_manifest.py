import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from components.component_manifest import ComponentManifest


class ComponentManifestTests(unittest.TestCase):

    def test_manifest_contains_valid_declarative_fields(self) -> None:
        manifest = ComponentManifest(
            files=(Path("example.toml"), Path("src/example.py")),
            dependencies=("foundation",),
            conflicts=("legacy-example",),
        )

        self.assertEqual(
            manifest.files,
            (Path("example.toml"), Path("src/example.py")),
        )
        self.assertEqual(manifest.dependencies, ("foundation",))
        self.assertEqual(manifest.conflicts, ("legacy-example",))

    def test_manifest_is_immutable(self) -> None:
        manifest = ComponentManifest()

        with self.assertRaises(FrozenInstanceError):
            manifest.files = (Path("changed"),)  # type: ignore[misc]

    def test_manifest_snapshots_collections_as_tuples(self) -> None:
        files = [Path("example.toml")]
        dependencies = ["foundation"]
        conflicts = ["legacy-example"]
        manifest = ComponentManifest(
            files=files,  # type: ignore[arg-type]
            dependencies=dependencies,  # type: ignore[arg-type]
            conflicts=conflicts,  # type: ignore[arg-type]
        )

        files.append(Path("changed.toml"))
        dependencies.append("changed")
        conflicts.append("changed")

        self.assertEqual(manifest.files, (Path("example.toml"),))
        self.assertEqual(manifest.dependencies, ("foundation",))
        self.assertEqual(manifest.conflicts, ("legacy-example",))

    def test_manifest_rejects_empty_names_and_paths(self) -> None:
        invalid_values = (
            {"files": (Path(),)},
            {"files": (Path("   "),)},
            {"dependencies": ("",)},
            {"dependencies": ("   ",)},
            {"conflicts": ("",)},
            {"conflicts": ("   ",)},
        )

        for values in invalid_values:
            with self.subTest(values=values), self.assertRaises(ValueError):
                ComponentManifest(**values)  # type: ignore[arg-type]

    def test_manifest_rejects_invalid_entry_types(self) -> None:
        invalid_values = (
            {"files": ("example.toml",)},
            {"dependencies": (1,)},
            {"conflicts": (1,)},
        )

        for values in invalid_values:
            with self.subTest(values=values), self.assertRaises(TypeError):
                ComponentManifest(**values)  # type: ignore[arg-type]

    def test_manifest_accepts_only_project_relative_file_paths(self) -> None:
        manifest = ComponentManifest(
            files=(Path("pyproject.toml"), Path("src/example.py")),
        )

        self.assertEqual(
            manifest.files,
            (Path("pyproject.toml"), Path("src/example.py")),
        )

    def test_manifest_rejects_absolute_file_paths(self) -> None:
        with self.assertRaises(ValueError):
            ComponentManifest(files=(Path.cwd() / "outside.txt",))

    def test_manifest_rejects_parent_traversal_segments(self) -> None:
        for path in (Path("../outside.txt"), Path("files/../../outside.txt")):
            with self.subTest(path=path), self.assertRaises(ValueError):
                ComponentManifest(files=(path,))

    def test_manifest_rejects_duplicates_consistently(self) -> None:
        invalid_values = (
            {"files": (Path("example.toml"), Path("example.toml"))},
            {"dependencies": ("foundation", "foundation")},
            {"conflicts": ("legacy-example", "legacy-example")},
        )

        for values in invalid_values:
            with self.subTest(values=values), self.assertRaises(ValueError):
                ComponentManifest(**values)  # type: ignore[arg-type]

    def test_manifest_allows_dependency_and_conflict_overlap(self) -> None:
        manifest = ComponentManifest(
            dependencies=("shared",),
            conflicts=("shared",),
        )

        self.assertEqual(manifest.dependencies, ("shared",))
        self.assertEqual(manifest.conflicts, ("shared",))


if __name__ == "__main__":
    unittest.main()
