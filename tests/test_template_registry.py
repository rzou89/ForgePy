import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from dataclasses import FrozenInstanceError
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cli.commands.list_command import ListCommand
from cli.dispatcher import Dispatcher
from cli.parser import Parser
from templates.basic.basic_template import BasicTemplate
from templates.cli.cli_template import CliTemplate
from templates.library.library_template import LibraryTemplate
from templates.template_engine.base_template import BaseTemplate
from templates.template_engine.template_metadata import TemplateMetadata
from templates.template_engine.template_registry import TemplateRegistry


class ExampleTemplate(BaseTemplate):

    def __init__(
        self,
        metadata: TemplateMetadata,
        name: str | None = None,
    ) -> None:
        self._metadata = metadata
        self._name = metadata.name if name is None else name

    @property
    def metadata(self) -> TemplateMetadata:
        return self._metadata

    @property
    def name(self) -> str:
        return self._name

    def create(self, project_path: Path) -> None:
        del project_path
        raise AssertionError("Metadata operations must not generate a project.")


class LegacyTemplate(BaseTemplate):

    @property
    def name(self) -> str:
        return "legacy"

    def create(self, project_path: Path) -> None:
        del project_path
        raise AssertionError("Metadata operations must not generate a project.")


class EmptyNameTemplate(LegacyTemplate):

    @property
    def name(self) -> str:
        return "   "


class InvalidMetadataTemplate(LegacyTemplate):

    @property
    def name(self) -> str:
        return "invalid-metadata"

    @property
    def metadata(self) -> TemplateMetadata:
        return object()  # type: ignore[return-value]


class TemplateMetadataTests(unittest.TestCase):

    def test_basic_template_exposes_complete_metadata(self) -> None:
        template = BasicTemplate()

        self.assertEqual(
            template.metadata,
            TemplateMetadata(
                name="basic",
                description="Basic Python project starter template.",
                version="0.6.0",
                author="Rendy Zou",
                tags=("python", "basic"),
                display_name="General Application",
                use_cases=(
                    "desktop application",
                    "GUI",
                    "data processing",
                    "Excel/reporting",
                    "general business application",
                ),
            ),
        )
        self.assertEqual(template.name, template.metadata.name)
        self.assertEqual(
            template.metadata.friendly_name,
            "General Application",
        )

    def test_metadata_is_immutable(self) -> None:
        metadata = BasicTemplate().metadata

        with self.assertRaises(FrozenInstanceError):
            metadata.description = "Changed"  # type: ignore[misc]

    def test_metadata_normalizes_tags_to_an_immutable_tuple(self) -> None:
        source_tags = ["python"]
        metadata = TemplateMetadata(
            name="example",
            description="Example template.",
            version="1.0.0",
            author="Example Author",
            tags=source_tags,  # type: ignore[arg-type]
        )

        source_tags.append("changed")

        self.assertEqual(metadata.tags, ("python",))

    def test_metadata_normalizes_use_cases_to_an_immutable_tuple(self) -> None:
        source_use_cases = ["automation"]
        metadata = TemplateMetadata(
            name="example",
            description="Example template.",
            version="1.0.0",
            author="Example Author",
            tags=("example",),
            use_cases=source_use_cases,  # type: ignore[arg-type]
        )

        source_use_cases.append("changed")

        self.assertEqual(
            metadata.use_cases,
            ("automation",),
        )

    def test_metadata_uses_name_as_friendly_name_by_default(self) -> None:
        metadata = TemplateMetadata(
            name="example",
            description="Example template.",
            version="1.0.0",
            author="Example Author",
            tags=("example",),
        )

        self.assertEqual(
            metadata.friendly_name,
            "example",
        )

    def test_metadata_rejects_a_string_as_tags(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "iterable of strings",
        ):
            TemplateMetadata(
                name="example",
                description="Example template.",
                version="1.0.0",
                author="Example Author",
                tags="python",  # type: ignore[arg-type]
            )

    def test_metadata_rejects_a_string_as_use_cases(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "iterable of strings",
        ):
            TemplateMetadata(
                name="example",
                description="Example template.",
                version="1.0.0",
                author="Example Author",
                tags=("example",),
                use_cases="automation",  # type: ignore[arg-type]
            )

    def test_metadata_rejects_empty_names(self) -> None:
        for name in ("", "   "):
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    ValueError,
                    "name must not be empty",
                ):
                    TemplateMetadata(
                        name=name,
                        description="Example template.",
                        version="1.0.0",
                        author="Example Author",
                        tags=(),
                    )

    def test_metadata_rejects_empty_display_name(self) -> None:
        for display_name in ("", "   "):
            with self.subTest(display_name=display_name):
                with self.assertRaisesRegex(
                    ValueError,
                    "display_name must not be empty",
                ):
                    TemplateMetadata(
                        name="example",
                        description="Example template.",
                        version="1.0.0",
                        author="Example Author",
                        tags=(),
                        display_name=display_name,
                    )

    def test_legacy_template_receives_compatibility_metadata(self) -> None:
        metadata = LegacyTemplate().metadata

        self.assertEqual(metadata.name, "legacy")
        self.assertEqual(metadata.description, "")
        self.assertEqual(metadata.version, "")
        self.assertEqual(metadata.author, "")
        self.assertEqual(metadata.tags, ())
        self.assertIsNone(metadata.display_name)
        self.assertEqual(metadata.use_cases, ())
        self.assertEqual(metadata.friendly_name, "legacy")

    def test_legacy_template_preflight_is_harmless(self) -> None:
        self.assertIsNone(LegacyTemplate().preflight(Path("LegacyProject")))


class TemplateRegistryTests(unittest.TestCase):

    def test_registers_and_looks_up_template_metadata(self) -> None:
        registry = TemplateRegistry()
        metadata = TemplateMetadata(
            name="example",
            description="Example template.",
            version="1.0.0",
            author="Example Author",
            tags=("example",),
        )
        template = ExampleTemplate(metadata)

        registry.register(template)

        self.assertIs(registry.get("example"), template)
        self.assertIs(registry.get_metadata("example"), metadata)
        self.assertEqual(
            registry.list_metadata(),
            (
                BasicTemplate().metadata,
                LibraryTemplate().metadata,
                CliTemplate().metadata,
                metadata,
            ),
        )

    def test_preserves_legacy_template_listing_contract(self) -> None:
        registry = TemplateRegistry()

        templates = registry.list_templates()

        self.assertEqual(
            tuple(templates),
            ("basic", "library", "cli"),
        )
        self.assertIsInstance(templates["basic"], BasicTemplate)
        self.assertIsInstance(templates["library"], LibraryTemplate)
        self.assertIsInstance(templates["cli"], CliTemplate)
        self.assertIs(registry.get("basic"), templates["basic"])
        self.assertIs(registry.get("library"), templates["library"])
        self.assertIs(registry.get("cli"), templates["cli"])

    def test_template_views_cannot_desynchronize_registry_state(self) -> None:
        registry = TemplateRegistry()

        registry.list_templates().clear()
        registry.templates.clear()

        self.assertIsInstance(registry.get("basic"), BasicTemplate)
        self.assertEqual(
            registry.get_metadata("basic"),
            BasicTemplate().metadata,
        )
        self.assertEqual(
            tuple(registry.list_templates()),
            ("basic", "library", "cli"),
        )
        self.assertEqual(len(registry.list_metadata()), 3)

    def test_rejects_duplicate_metadata_name(self) -> None:
        registry = TemplateRegistry()
        original = registry.get("basic")

        with self.assertRaisesRegex(
            ValueError,
            "already registered",
        ):
            registry.register(
                ExampleTemplate(BasicTemplate().metadata)
            )

        self.assertIs(registry.get("basic"), original)
        self.assertEqual(len(registry.list_metadata()), 3)

    def test_rejects_template_with_empty_name(self) -> None:
        registry = TemplateRegistry()

        with self.assertRaisesRegex(
            ValueError,
            "name must not be empty",
        ):
            registry.register(EmptyNameTemplate())

        self.assertEqual(
            tuple(registry.list_templates()),
            ("basic", "library", "cli"),
        )

    def test_rejects_invalid_metadata_registration(self) -> None:
        registry = TemplateRegistry()

        with self.assertRaisesRegex(
            TypeError,
            "metadata must be TemplateMetadata",
        ):
            registry.register(InvalidMetadataTemplate())

        self.assertEqual(
            tuple(registry.list_templates()),
            ("basic", "library", "cli"),
        )

    def test_rejects_object_that_is_not_a_template(self) -> None:
        registry = TemplateRegistry()

        with self.assertRaisesRegex(
            TypeError,
            "must inherit from BaseTemplate",
        ):
            registry.register(object())  # type: ignore[arg-type]

        self.assertEqual(
            tuple(registry.list_templates()),
            ("basic", "library", "cli"),
        )

    def test_rejects_template_and_metadata_name_mismatch(self) -> None:
        registry = TemplateRegistry()
        template = ExampleTemplate(
            TemplateMetadata(
                name="metadata-name",
                description="Example template.",
                version="1.0.0",
                author="Example Author",
                tags=(),
            ),
            name="template-name",
        )

        with self.assertRaisesRegex(
            ValueError,
            "must match",
        ):
            registry.register(template)

        with self.assertRaises(KeyError):
            registry.get("metadata-name")

    def test_unknown_metadata_lookup_preserves_key_error(self) -> None:
        registry = TemplateRegistry()

        with self.assertRaises(KeyError):
            registry.get("unknown")

        with self.assertRaises(KeyError):
            registry.get_metadata("unknown")


class ListCommandMetadataTests(unittest.TestCase):

    def test_list_command_displays_name_and_description(self) -> None:
        output = StringIO()

        with redirect_stdout(output):
            ListCommand().execute(Namespace())

        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "=" * 40,
                " ForgePy Templates ",
                "=" * 40,
                "- basic: Basic Python project starter template.",
                "- library: Reusable Python package template.",
                "- cli: Minimal command-line application template.",
            ],
        )

    def test_list_dispatch_does_not_access_config_or_generation(self) -> None:
        output = StringIO()

        with patch(
            "config.user_config.Path.home",
            side_effect=AssertionError(
                "Listing templates must not access user configuration."
            ),
        ):
            with patch(
                "cli.commands.create_command.ProjectGenerator",
                side_effect=AssertionError(
                    "Listing templates must not generate a project."
                ),
            ):
                with patch("sys.argv", ["forgepy", "list"]):
                    with redirect_stdout(output):
                        args = Parser().parse()
                        Dispatcher().dispatch(args)

        self.assertIn(
            "- basic: Basic Python project starter template.",
            output.getvalue(),
        )
        self.assertIn(
            "- library: Reusable Python package template.",
            output.getvalue(),
        )
        self.assertIn(
            "- cli: Minimal command-line application template.",
            output.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()