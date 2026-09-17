import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from tempfile import TemporaryDirectory

from components.base_component import BaseComponent
from components.component_context import ComponentContext
from components.component_manifest import ComponentManifest
from components.component_metadata import ComponentMetadata
from components.component_registry import ComponentRegistry


def component_metadata(name: str = "example") -> ComponentMetadata:
    return ComponentMetadata(
        name=name,
        description="Example component.",
        version="1.0.0",
        author="Example Author",
        tags=("example",),
    )


def component_manifest() -> ComponentManifest:
    return ComponentManifest()


def registered_names(registry: ComponentRegistry) -> tuple[str, ...]:
    return tuple(component.name for component in registry.list_components())


class ExampleComponent(BaseComponent):

    def __init__(
        self,
        metadata: ComponentMetadata,
        name: str | None = None,
        manifest: ComponentManifest | None = None,
    ) -> None:
        self._metadata = metadata
        self._name = metadata.name if name is None else name
        self._manifest = (
            component_manifest() if manifest is None else manifest
        )
        self.installed_contexts: list[ComponentContext] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> ComponentMetadata:
        return self._metadata

    @property
    def manifest(self) -> ComponentManifest:
        return self._manifest

    def install(self, context: ComponentContext) -> None:
        self.installed_contexts.append(context)


class InvalidMetadataComponent(BaseComponent):

    @property
    def name(self) -> str:
        return "invalid-metadata"

    @property
    def metadata(self) -> ComponentMetadata:
        return object()  # type: ignore[return-value]

    @property
    def manifest(self) -> ComponentManifest:
        return component_manifest()

    def install(self, context: ComponentContext) -> None:
        del context


class InvalidManifestComponent(ExampleComponent):

    @property
    def manifest(self) -> ComponentManifest:
        return object()  # type: ignore[return-value]


class ComponentContextTests(unittest.TestCase):

    def test_context_accepts_an_existing_project_directory(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory)

            context = ComponentContext(project_path=project_path)

            self.assertEqual(context.project_path, project_path)

    def test_context_is_immutable(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            context = ComponentContext(Path(temporary_directory))

            with self.assertRaises(FrozenInstanceError):
                context.project_path = Path("changed")  # type: ignore[misc]

    def test_context_rejects_a_non_path_project_path(self) -> None:
        with self.assertRaisesRegex(TypeError, "must be a Path"):
            ComponentContext("project")  # type: ignore[arg-type]

    def test_context_rejects_a_missing_project_path(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory) / "missing"

            with self.assertRaisesRegex(ValueError, "must exist"):
                ComponentContext(missing_path)

    def test_context_rejects_a_file_project_path(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            file_path = Path(temporary_directory) / "not-a-project"
            file_path.write_text("", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must be a directory"):
                ComponentContext(file_path)


class ComponentContractTests(unittest.TestCase):

    def test_install_receives_the_validated_context(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            context = ComponentContext(Path(temporary_directory))
            component = ExampleComponent(component_metadata())

            component.install(context)

            self.assertEqual(component.installed_contexts, [context])

    def test_install_side_effects_can_be_confined_to_the_context(self) -> None:
        class FileComponent(ExampleComponent):

            def install(self, context: ComponentContext) -> None:
                (context.project_path / "component.txt").write_text(
                    "installed",
                    encoding="utf-8",
                )

        with TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory) / "project"
            outside_path = Path(temporary_directory) / "outside"
            project_path.mkdir()
            outside_path.mkdir()
            component = FileComponent(component_metadata())

            component.install(ComponentContext(project_path))

            self.assertEqual(
                (project_path / "component.txt").read_text(encoding="utf-8"),
                "installed",
            )
            self.assertEqual(tuple(outside_path.iterdir()), ())

    def test_component_without_install_hook_remains_abstract(self) -> None:
        class IncompleteComponent(BaseComponent):

            @property
            def name(self) -> str:
                return "incomplete"

            @property
            def metadata(self) -> ComponentMetadata:
                return component_metadata("incomplete")

            @property
            def manifest(self) -> ComponentManifest:
                return component_manifest()

        with self.assertRaises(TypeError):
            IncompleteComponent()  # type: ignore[abstract]

    def test_component_without_manifest_remains_abstract(self) -> None:
        class IncompleteComponent(BaseComponent):

            @property
            def name(self) -> str:
                return "incomplete"

            @property
            def metadata(self) -> ComponentMetadata:
                return component_metadata(self.name)

            def install(self, context: ComponentContext) -> None:
                del context

        with self.assertRaises(TypeError):
            IncompleteComponent()  # type: ignore[abstract]


class ComponentMetadataTests(unittest.TestCase):

    def test_metadata_contains_the_required_fields(self) -> None:
        metadata = component_metadata()

        self.assertEqual(metadata.name, "example")
        self.assertEqual(metadata.description, "Example component.")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.author, "Example Author")
        self.assertEqual(metadata.tags, ("example",))

    def test_metadata_is_immutable(self) -> None:
        metadata = component_metadata()

        with self.assertRaises(FrozenInstanceError):
            metadata.description = "Changed"  # type: ignore[misc]

    def test_metadata_normalizes_tags_to_an_immutable_tuple(self) -> None:
        source_tags = ["example"]
        metadata = ComponentMetadata(
            name="example",
            description="Example component.",
            version="1.0.0",
            author="Example Author",
            tags=source_tags,  # type: ignore[arg-type]
        )

        source_tags.append("changed")

        self.assertEqual(metadata.tags, ("example",))

    def test_metadata_rejects_empty_names(self) -> None:
        for name in ("", "   "):
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError,
                "name must not be empty",
            ):
                component_metadata(name)

    def test_metadata_rejects_non_string_fields(self) -> None:
        values: dict[str, object] = {
            "name": "example",
            "description": "Example component.",
            "version": "1.0.0",
            "author": "Example Author",
            "tags": (),
        }

        for field_name in ("name", "description", "version", "author"):
            with self.subTest(field=field_name):
                invalid_values = values.copy()
                invalid_values[field_name] = object()

                with self.assertRaisesRegex(
                    TypeError,
                    f"{field_name} must be a string",
                ):
                    ComponentMetadata(**invalid_values)  # type: ignore[arg-type]

    def test_metadata_rejects_invalid_tags(self) -> None:
        for tags, message in (
            ("example", "iterable of strings"),
            (b"example", "iterable of strings"),
            (1, "iterable of strings"),
            (("example", 1), "only strings"),
        ):
            with self.subTest(tags=tags), self.assertRaisesRegex(TypeError, message):
                ComponentMetadata(
                    name="example",
                    description="Example component.",
                    version="1.0.0",
                    author="Example Author",
                    tags=tags,  # type: ignore[arg-type]
                    )


class ComponentRegistryTests(unittest.TestCase):

    def test_registry_starts_with_approved_built_in_components(self) -> None:
        registry = ComponentRegistry()

        self.assertEqual(registered_names(registry)[:2], ("pytest", "ruff"))

    def test_registers_a_valid_component(self) -> None:
        registry = ComponentRegistry()
        component = ExampleComponent(component_metadata())
        initial_names = registered_names(registry)

        registry.register(component)

        self.assertEqual(
            registered_names(registry),
            (*initial_names, "example"),
        )
        self.assertEqual(component.installed_contexts, [])

    def test_get_returns_the_registered_component(self) -> None:
        registry = ComponentRegistry()
        component = ExampleComponent(component_metadata())
        registry.register(component)

        self.assertIs(registry.get("example"), component)
        self.assertEqual(component.installed_contexts, [])

    def test_list_components_preserves_registration_order(self) -> None:
        registry = ComponentRegistry()
        first = ExampleComponent(component_metadata("first"))
        second = ExampleComponent(component_metadata("second"))
        initial_names = registered_names(registry)

        registry.register(first)
        registry.register(second)

        self.assertEqual(
            registered_names(registry),
            (*initial_names, "first", "second"),
        )

    def test_registration_does_not_resolve_manifest_relationships(self) -> None:
        registry = ComponentRegistry()
        component = ExampleComponent(
            component_metadata(),
            manifest=ComponentManifest(
                dependencies=("not-registered",),
                conflicts=("also-not-registered",),
            ),
        )

        registry.register(component)

        self.assertIs(registry.get("example"), component)

    def test_rejects_duplicate_component_names(self) -> None:
        registry = ComponentRegistry()
        original = ExampleComponent(component_metadata())
        initial_names = registered_names(registry)
        registry.register(original)

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register(ExampleComponent(component_metadata()))

        self.assertIs(registry.get("example"), original)
        self.assertEqual(
            registered_names(registry),
            (*initial_names, "example"),
        )

    def test_rejects_an_object_that_is_not_a_component(self) -> None:
        registry = ComponentRegistry()
        initial_names = registered_names(registry)

        with self.assertRaisesRegex(
            TypeError,
            "must inherit from BaseComponent",
        ):
            registry.register(object())  # type: ignore[arg-type]

        self.assertEqual(registered_names(registry), initial_names)

    def test_rejects_components_with_empty_names(self) -> None:
        for name in ("", "   "):
            with self.subTest(name=name):
                registry = ComponentRegistry()
                initial_names = registered_names(registry)
                component = ExampleComponent(
                    component_metadata("metadata-name"),
                    name=name,
                )

                with self.assertRaisesRegex(
                    ValueError,
                    "name must not be empty",
                ):
                    registry.register(component)

                self.assertEqual(
                    registered_names(registry),
                    initial_names,
                )

    def test_rejects_components_with_non_string_names(self) -> None:
        registry = ComponentRegistry()
        initial_names = registered_names(registry)
        component = ExampleComponent(
            component_metadata(),
            name=object(),  # type: ignore[arg-type]
        )

        with self.assertRaisesRegex(TypeError, "name must be a string"):
            registry.register(component)

        self.assertEqual(registered_names(registry), initial_names)

    def test_rejects_invalid_component_metadata(self) -> None:
        registry = ComponentRegistry()
        initial_names = registered_names(registry)

        with self.assertRaisesRegex(
            TypeError,
            "metadata must be ComponentMetadata",
        ):
            registry.register(InvalidMetadataComponent())

        self.assertEqual(registered_names(registry), initial_names)

    def test_rejects_invalid_component_manifest(self) -> None:
        registry = ComponentRegistry()
        initial_names = registered_names(registry)

        with self.assertRaises(TypeError):
            registry.register(InvalidManifestComponent(component_metadata()))

        self.assertEqual(registered_names(registry), initial_names)

    def test_rejects_self_dependency(self) -> None:
        registry = ComponentRegistry()
        initial_names = registered_names(registry)
        component = ExampleComponent(
            component_metadata(),
            manifest=ComponentManifest(dependencies=("example",)),
        )

        with self.assertRaises(ValueError):
            registry.register(component)

        self.assertEqual(registered_names(registry), initial_names)

    def test_rejects_self_conflict(self) -> None:
        registry = ComponentRegistry()
        initial_names = registered_names(registry)
        component = ExampleComponent(
            component_metadata(),
            manifest=ComponentManifest(conflicts=("example",)),
        )

        with self.assertRaises(ValueError):
            registry.register(component)

        self.assertEqual(registered_names(registry), initial_names)

    def test_rejects_component_and_metadata_name_mismatch(self) -> None:
        registry = ComponentRegistry()
        initial_names = registered_names(registry)
        component = ExampleComponent(
            component_metadata("metadata-name"),
            name="component-name",
        )

        with self.assertRaisesRegex(ValueError, "must match"):
            registry.register(component)

        self.assertEqual(registered_names(registry), initial_names)
        with self.assertRaises(KeyError):
            registry.get("metadata-name")

    def test_unknown_component_lookup_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            ComponentRegistry().get("unknown")


if __name__ == "__main__":
    unittest.main()
