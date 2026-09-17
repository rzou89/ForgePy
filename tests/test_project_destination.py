"""Project destination validation and filesystem-safety tests."""

import ast
import os
import tempfile
import tomllib
import unittest
from contextlib import ExitStack, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from core.project_generator import ProjectGenerator
from models.project_config import ProjectConfig
from templates.template_engine.package_name import normalize_package_name


class ProjectNameContractTests(unittest.TestCase):
    """Verify names used as destination path segments."""

    def test_valid_project_name_constructs_one_direct_child(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory).resolve()
            config = ProjectConfig(name="Demo Project", location=location)

            self.assertEqual(config.root, location / "Demo Project")
            self.assertEqual(config.root.parent, location)

    def test_rejects_unsafe_project_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)
            absolute_name = str((location / "absolute").resolve())
            cases = (
                "",
                ".",
                "..",
                "group/project",
                "group\\project",
                absolute_name,
                "C:project",
            )

            for project_name in cases:
                with self.subTest(project_name=project_name), self.assertRaises(ValueError):
                    ProjectConfig(
                        name=project_name,
                        location=location,
                    )

    def test_rejects_names_unsafe_for_windows_or_generated_content(self) -> None:
        invalid_characters = '<>:"/\\|?*'
        cases = (
            "   ",
            "trailing ",
            "trailing.",
            "line\nfeed",
            "carriage\rreturn",
            "tab\tname",
            "delete\x7fname",
            "surrogate\ud800name",
            *(f"name{character}part" for character in invalid_characters),
        )

        for project_name in cases:
            with self.subTest(project_name=project_name), self.assertRaises(ValueError):
                ProjectConfig(name=project_name, location=Path("projects"))

    def test_rejects_leading_ascii_spaces(self) -> None:
        for project_name in (" Project", "  Project"):
            with self.subTest(project_name=project_name), self.assertRaises(ValueError):
                ProjectConfig(name=project_name, location=Path("projects"))

    def test_rejects_windows_reserved_device_names(self) -> None:
        cases = (
            "CON",
            "con",
            "NUL",
            "COM1",
            "COM9",
            "LPT1",
            "LPT9",
            "CON.txt",
            "aux.json",
            "COM¹",
            "COM²",
            "COM³",
            "LPT¹",
            "LPT²",
            "LPT³",
            "COM¹.txt",
            "COM².log",
            "LPT³.data",
        )

        for project_name in cases:
            with self.subTest(project_name=project_name), self.assertRaises(ValueError):
                ProjectConfig(name=project_name, location=Path("projects"))

    def test_accepts_windows_reserved_name_near_misses(self) -> None:
        for project_name in ("CONSOLE", "COM10", "LPT10", "AUXILIARY"):
            with self.subTest(project_name=project_name):
                config = ProjectConfig(
                    name=project_name,
                    location=Path("projects"),
                )

                self.assertEqual(config.name, project_name)

    def test_accepts_human_readable_names_without_rewriting(self) -> None:
        cases = (
            "my-project",
            "my_project",
            "Project 123",
            "Café App",
        )

        for project_name in cases:
            with self.subTest(project_name=project_name):
                config = ProjectConfig(
                    name=project_name,
                    location=Path("projects"),
                )

                self.assertEqual(config.name, project_name)
                self.assertEqual(config.root, Path("projects") / project_name)


class ProjectDestinationSafetyTests(unittest.TestCase):
    """Verify generation rejects unsafe destinations before writes."""

    def test_invalid_name_does_not_create_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)

            with patch(
                "core.project_generator.TemplateRegistry"
            ) as registry, self.assertRaises(ValueError):
                ProjectGenerator().create(
                    project_name="nested/project",
                    location=str(location),
                    template_name="unknown",
                )

            self.assertEqual(tuple(location.iterdir()), ())
            registry.assert_not_called()

    def test_content_unsafe_names_are_rejected_before_generation(self) -> None:
        cases = (
            "   ",
            " Project",
            'quoted"name',
            "line\nfeed",
            "trailing.",
            "CON.txt",
            "COM¹.txt",
        )

        for project_name in cases:
            with self.subTest(project_name=project_name), tempfile.TemporaryDirectory() as temporary_directory:
                location = Path(temporary_directory)

                with patch(
                    "core.project_generator.TemplateRegistry"
                ) as registry, self.assertRaises(ValueError):
                    ProjectGenerator().create(
                        project_name=project_name,
                        location=str(location),
                        template_name="basic",
                    )

                self.assertEqual(tuple(location.iterdir()), ())
                registry.assert_not_called()

    def test_existing_directory_and_contents_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)
            destination = location / "Existing"
            destination.mkdir()
            existing_file = destination / "data.bin"
            original_content = b"\x00existing\xffcontent"
            existing_file.write_bytes(original_content)

            with patch(
                "core.project_generator.TemplateRegistry"
            ) as registry, self.assertRaises(FileExistsError):
                ProjectGenerator().create(
                    project_name="Existing",
                    location=str(location),
                    template_name="unknown",
                )

            self.assertEqual(existing_file.read_bytes(), original_content)
            self.assertEqual(tuple(destination.iterdir()), (existing_file,))
            registry.assert_not_called()

    def test_existing_destination_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)
            destination = location / "Existing"
            original_content = b"existing file"
            destination.write_bytes(original_content)

            with patch(
                "core.project_generator.TemplateRegistry"
            ) as registry, self.assertRaises(FileExistsError):
                ProjectGenerator().create(
                    project_name="Existing",
                    location=str(location),
                    template_name="unknown",
                )

            self.assertEqual(destination.read_bytes(), original_content)
            registry.assert_not_called()

    def test_existing_destination_precedes_package_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)
            destination = location / "---"
            destination.mkdir()

            with self.assertRaises(FileExistsError):
                ProjectGenerator().create(
                    project_name=destination.name,
                    location=str(location),
                    template_name="library",
                )

            self.assertEqual(tuple(destination.iterdir()), ())

    def test_existing_link_destination_is_rejected_without_outside_writes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            location = temporary_root / "projects"
            outside = temporary_root / "outside"
            location.mkdir()
            outside.mkdir()
            destination = location / "Linked"

            try:
                os.symlink(
                    outside,
                    destination,
                    target_is_directory=True,
                )
            except OSError as error:
                self.skipTest(
                    "Directory symlink creation is unavailable: "
                    f"{error}"
                )

            with patch(
                "core.project_generator.TemplateRegistry"
            ) as registry, self.assertRaises(FileExistsError):
                ProjectGenerator().create(
                    project_name="Linked",
                    location=str(location),
                    template_name="unknown",
                )

            self.assertTrue(destination.is_symlink())
            self.assertEqual(destination.resolve(), outside.resolve())
            self.assertEqual(tuple(outside.iterdir()), ())
            registry.assert_not_called()

    def test_unknown_template_creates_no_project_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)
            destination = location / "UnknownTemplate"

            with ExitStack() as stack:
                template_create = stack.enter_context(
                    patch("templates.basic.basic_template.BasicTemplate.create")
                )
                stage_calls = self._patch_generation_stages(stack)

                with self.assertRaises(KeyError):
                    ProjectGenerator().create(
                        project_name=destination.name,
                        location=str(location),
                        template_name="unknown",
                    )

            self.assertFalse(destination.exists())
            self.assertEqual(tuple(location.iterdir()), ())
            template_create.assert_not_called()
            for stage_call in stage_calls:
                stage_call.assert_not_called()

    def test_package_templates_preflight_unusable_names_before_writes(
        self,
    ) -> None:
        project_names = (
            "\u4f60\u597d",
            "\u65e5\u672c\u8a9e",
            "---",
            "___",
            "!@#$%^&()+=,;",
        )

        for template_name in ("library", "cli"):
            for project_name in project_names:
                with self.subTest(
                    template=template_name,
                    project_name=project_name,
                ), tempfile.TemporaryDirectory() as temporary_directory:
                    location = Path(temporary_directory)
                    destination = location / project_name

                    with ExitStack() as stack:
                        folder_create = stack.enter_context(
                            patch(
                                "builders.folder_builder."
                                "FolderBuilder.create"
                            )
                        )
                        file_write = stack.enter_context(
                            patch(
                                "builders.file_builder.FileBuilder.write"
                            )
                        )
                        stage_calls = self._patch_generation_stages(stack)

                        with self.assertRaises(ValueError):
                            ProjectGenerator().create(
                                project_name=project_name,
                                location=str(location),
                                template_name=template_name,
                            )

                    self.assertFalse(destination.exists())
                    self.assertEqual(tuple(location.iterdir()), ())
                    folder_create.assert_not_called()
                    file_write.assert_not_called()
                    for stage_call in stage_calls:
                        stage_call.assert_not_called()

    def test_basic_accepts_names_without_usable_package_identifiers(
        self,
    ) -> None:
        project_names = ("\u4f60\u597d", "\u65e5\u672c\u8a9e", "---", "___")

        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)

            for project_name in project_names:
                with self.subTest(project_name=project_name):
                    with ExitStack() as stack:
                        self._patch_generation_stages(stack)
                        stack.enter_context(redirect_stdout(StringIO()))
                        ProjectGenerator().create(
                            project_name=project_name,
                            location=str(location),
                            template_name="basic",
                        )

                    self.assertTrue(
                        (location / project_name / "app.py").is_file()
                    )

    def test_package_normalization_preserves_supported_identifiers(self) -> None:
        cases = {
            "My Project": "my_project",
            "my-project": "my_project",
            "my_project": "my_project",
            "Caf\u00e9 App": "caf_app",
            "123 Project": "_123_project",
        }

        for project_name, expected in cases.items():
            with self.subTest(project_name=project_name):
                package_name = normalize_package_name(
                    project_name,
                    package_label="test",
                )

                self.assertEqual(package_name, expected)
                self.assertTrue(package_name.isidentifier())

    def test_valid_templates_still_generate_their_owned_files(self) -> None:
        cases = {
            "basic": Path("app.py"),
            "library": Path("valid_library/__init__.py"),
            "cli": Path("valid_cli/cli.py"),
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)

            for template_name, expected_file in cases.items():
                with self.subTest(template=template_name):
                    project_name = f"Valid-{template_name}"
                    destination = location / project_name

                    with ExitStack() as stack:
                        stage_calls = self._patch_generation_stages(stack)
                        stack.enter_context(redirect_stdout(StringIO()))
                        ProjectGenerator().create(
                            project_name=project_name,
                            location=str(location),
                            template_name=template_name,
                        )

                    self.assertTrue((destination / expected_file).is_file())
                    for stage_call in stage_calls:
                        stage_call.assert_called_once()

    def test_representative_names_generate_valid_python_and_toml(self) -> None:
        cases = (
            ("basic", "my-project"),
            ("library", "Project 123"),
            ("cli", "Café App"),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            location = Path(temporary_directory)

            for template_name, project_name in cases:
                with self.subTest(
                    template=template_name,
                    project_name=project_name,
                ):
                    destination = location / project_name
                    with ExitStack() as stack:
                        self._patch_generation_stages(stack)
                        stack.enter_context(redirect_stdout(StringIO()))
                        ProjectGenerator().create(
                            project_name=project_name,
                            location=str(location),
                            template_name=template_name,
                        )

                    for python_file in destination.rglob("*.py"):
                        ast.parse(
                            python_file.read_text(encoding="utf-8"),
                            filename=str(python_file),
                        )

                    pyproject = destination / "pyproject.toml"
                    parsed = tomllib.loads(
                        pyproject.read_text(encoding="utf-8")
                    )
                    self.assertEqual(parsed["project"]["name"], project_name)

    @staticmethod
    def _patch_generation_stages(stack: ExitStack) -> tuple[Mock, ...]:
        stage_paths = (
            "core.project_generator.EnvironmentBuilder.create",
            "core.project_generator.PythonToolsBuilder.update",
            "core.project_generator.RequirementsInstaller.install",
            "core.project_generator.GitBuilder.create",
            "core.project_generator.VSCodeBuilder.create",
        )

        return tuple(
            stack.enter_context(patch(stage_path))
            for stage_path in stage_paths
        )


if __name__ == "__main__":
    unittest.main()
