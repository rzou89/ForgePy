import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from core.project_generator import ProjectGenerator
from main import main
from templates.basic.basic_template import BasicTemplate
from templates.library.library_template import LibraryTemplate
from templates.template_engine.template_files import TemplateFiles
from templates.template_engine.template_metadata import TemplateMetadata
from templates.template_engine.template_registry import TemplateRegistry


class LibraryTemplateTests(unittest.TestCase):

    def test_library_metadata_is_complete(self) -> None:
        template = LibraryTemplate()

        self.assertEqual(
            template.metadata,
            TemplateMetadata(
                name="library",
                description="Reusable Python package template.",
                version="0.1.0",
                author="Rendy Zou",
                tags=("python", "library", "package"),
                display_name="Python Library",
                use_cases=(
                    "reusable Python package",
                    "SDK",
                    "internal library",
                    "module used by other projects",
                ),
            ),
        )
        self.assertEqual(template.name, "library")
        self.assertEqual(
            template.metadata.friendly_name,
            "Python Library",
        )

    def test_default_registry_registers_library_after_basic(self) -> None:
        registry = TemplateRegistry()

        self.assertEqual(
            tuple(registry.list_templates())[:2],
            ("basic", "library"),
        )
        self.assertIsInstance(registry.get("basic"), BasicTemplate)
        self.assertIsInstance(registry.get("library"), LibraryTemplate)
        self.assertEqual(
            registry.get_metadata("library"),
            LibraryTemplate().metadata,
        )

    def test_library_generates_minimal_package_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "Demo-Lib"

            with redirect_stdout(StringIO()):
                LibraryTemplate().create(project_root)

            directories = {
                path.relative_to(project_root).as_posix()
                for path in project_root.rglob("*")
                if path.is_dir()
            }
            files = {
                path.relative_to(project_root).as_posix()
                for path in project_root.rglob("*")
                if path.is_file()
            }

            self.assertEqual(
                directories,
                {
                    "demo_lib",
                    "tests",
                },
            )
            self.assertEqual(
                files,
                {
                    ".gitignore",
                    "README.md",
                    "demo_lib/__init__.py",
                    "pyproject.toml",
                    "requirements.txt",
                    "tests/__init__.py",
                },
            )

            self.assertEqual(
                (project_root / "demo_lib" / "__init__.py").read_text(
                    encoding="utf-8",
                ),
                "",
            )
            self.assertEqual(
                (project_root / "tests" / "__init__.py").read_text(
                    encoding="utf-8",
                ),
                "",
            )
            self.assertEqual(
                (project_root / "requirements.txt").read_text(
                    encoding="utf-8",
                ),
                "",
            )

            shared_files = TemplateFiles.basic(project_root.name)

            for filename in (
                "README.md",
                ".gitignore",
                "pyproject.toml",
            ):
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (project_root / filename).read_text(
                            encoding="utf-8",
                        ),
                        shared_files[filename],
                    )

            compile(
                (project_root / "demo_lib" / "__init__.py").read_text(
                    encoding="utf-8",
                ),
                "demo_lib/__init__.py",
                "exec",
            )
            compile(
                (project_root / "tests" / "__init__.py").read_text(
                    encoding="utf-8",
                ),
                "tests/__init__.py",
                "exec",
            )

            self.assertFalse((project_root / ".venv").exists())
            self.assertFalse((project_root / ".git").exists())
            self.assertFalse((project_root / ".vscode").exists())

    def test_package_name_is_normalized_to_a_python_identifier(self) -> None:
        cases = {
            "DemoLib": "demolib",
            "Demo-Lib": "demo_lib",
            "123 Library": "_123_library",
            "class": "class_",
        }

        for project_name, expected in cases.items():
            with self.subTest(project_name=project_name):
                self.assertEqual(
                    LibraryTemplate._normalize_package_name(project_name),
                    expected,
                )

    def test_package_name_rejects_names_without_ascii_letters_or_digits(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "must contain letters or digits",
        ):
            LibraryTemplate._normalize_package_name("---")

    def test_basic_generated_structure_remains_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory) / "BasicDemo"

            with redirect_stdout(StringIO()):
                BasicTemplate().create(project_root)

            directories = {
                path.relative_to(project_root).as_posix()
                for path in project_root.rglob("*")
                if path.is_dir()
            }
            files = {
                path.relative_to(project_root).as_posix()
                for path in project_root.rglob("*")
                if path.is_file()
            }

            self.assertEqual(
                directories,
                {
                    "assets",
                    "config",
                    "database",
                    "exports",
                    "logs",
                    "models",
                    "services",
                    "tests",
                    "ui",
                },
            )
            self.assertEqual(
                files,
                {
                    ".env",
                    ".env.example",
                    ".gitignore",
                    "CHANGELOG.md",
                    "LICENSE",
                    "README.md",
                    "app.py",
                    "pyproject.toml",
                    "requirements.txt",
                },
            )
            self.assertEqual(
                (project_root / "requirements.txt").read_text(
                    encoding="utf-8",
                ),
                "PySide6\npandas\nopenpyxl\n",
            )

    def test_project_generator_selects_library_without_pipeline_changes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            project_root = parent / "DemoLib"

            with patch(
                "core.project_generator.EnvironmentBuilder.create",
            ) as environment, patch(
                "core.project_generator.PythonToolsBuilder.update",
            ) as python_tools, patch(
                "core.project_generator.RequirementsInstaller.install",
            ) as requirements, patch(
                "core.project_generator.GitBuilder.create",
            ) as git, patch(
                "core.project_generator.VSCodeBuilder.create",
            ) as vscode, redirect_stdout(StringIO()):
                ProjectGenerator().create(
                    project_name="DemoLib",
                    location=str(parent),
                    template_name="library",
                )

            resolved_project_root = project_root.resolve()
            self.assertEqual(resolved_project_root.parent, parent.resolve())
            self.assertTrue(
                (
                    resolved_project_root / "demolib" / "__init__.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    resolved_project_root / "tests" / "__init__.py"
                ).is_file()
            )
            environment.assert_called_once_with(resolved_project_root)
            python_tools.assert_called_once_with(resolved_project_root)
            requirements.assert_called_once_with(resolved_project_root)
            git.assert_called_once_with(resolved_project_root)
            vscode.assert_called_once_with(
                resolved_project_root,
                entry_point=None,
            )

    def test_cli_create_selects_library_with_isolated_prompted_location(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            isolated_home = parent / "home"
            project_root = parent / "DemoLib"

            with ExitStack() as stack:
                stack.enter_context(
                    patch(
                        "config.user_config.Path.home",
                        return_value=isolated_home,
                    )
                )
                prompt = stack.enter_context(
                    patch(
                        "builtins.input",
                        return_value=str(parent),
                    )
                )
                stack.enter_context(
                    patch(
                        "sys.argv",
                        [
                            "forgepy",
                            "create",
                            "DemoLib",
                            "--template",
                            "library",
                        ],
                    )
                )
                environment = stack.enter_context(
                    patch(
                        "core.project_generator.EnvironmentBuilder.create",
                    )
                )
                python_tools = stack.enter_context(
                    patch(
                        "core.project_generator.PythonToolsBuilder.update",
                    )
                )
                requirements = stack.enter_context(
                    patch(
                        "core.project_generator.RequirementsInstaller.install",
                    )
                )
                git = stack.enter_context(
                    patch(
                        "core.project_generator.GitBuilder.create",
                    )
                )
                vscode = stack.enter_context(
                    patch(
                        "core.project_generator.VSCodeBuilder.create",
                    )
                )
                stack.enter_context(redirect_stdout(StringIO()))

                main()

            prompt.assert_called_once_with("Location : ")
            resolved_project_root = project_root.resolve()
            self.assertEqual(resolved_project_root.parent, parent.resolve())
            self.assertTrue(
                (
                    resolved_project_root / "demolib" / "__init__.py"
                ).is_file()
            )
            self.assertTrue(
                (
                    resolved_project_root / "tests" / "__init__.py"
                ).is_file()
            )
            self.assertFalse(isolated_home.exists())
            environment.assert_called_once_with(resolved_project_root)
            python_tools.assert_called_once_with(resolved_project_root)
            requirements.assert_called_once_with(resolved_project_root)
            git.assert_called_once_with(resolved_project_root)
            vscode.assert_called_once_with(
                resolved_project_root,
                entry_point=None,
            )


if __name__ == "__main__":
    unittest.main()