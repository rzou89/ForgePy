import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from templates.basic.basic_template import BasicTemplate
from templates.cli.cli_template import CliTemplate
from templates.library.library_template import LibraryTemplate
from templates.template_engine.template_files import TemplateFiles
from templates.template_engine.template_metadata import TemplateMetadata
from templates.template_engine.template_registry import TemplateRegistry


class CliTemplateTests(unittest.TestCase):

    def test_cli_metadata_is_complete(self) -> None:
        template = CliTemplate()

        self.assertEqual(
            template.metadata,
            TemplateMetadata(
                name="cli",
                description="Minimal command-line application template.",
                version="0.1.0",
                author="Rendy Zou",
                tags=("python", "cli", "argparse"),
                display_name="CLI / Automation / Backend Tool",
                use_cases=(
                    "automation",
                    "trading bot",
                    "scanner",
                    "backend service",
                    "scheduled jobs",
                    "API clients",
                ),
            ),
        )
        self.assertEqual(template.name, "cli")
        self.assertEqual(
            template.metadata.friendly_name,
            "CLI / Automation / Backend Tool",
        )

    def test_default_registry_registers_cli_after_existing_templates(
        self,
    ) -> None:
        registry = TemplateRegistry()

        self.assertEqual(
            tuple(registry.list_templates()),
            ("basic", "library", "cli"),
        )
        self.assertIsInstance(registry.get("basic"), BasicTemplate)
        self.assertIsInstance(registry.get("library"), LibraryTemplate)
        self.assertIsInstance(registry.get("cli"), CliTemplate)
        self.assertEqual(
            registry.get_metadata("cli"),
            CliTemplate().metadata,
        )

    def test_cli_generates_minimal_package_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root, package_name, template = self._create_project(
                Path(temporary_directory),
                project_name="Demo-CLI",
            )

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
                    "demo_cli",
                    "tests",
                },
            )
            self.assertEqual(
                files,
                {
                    ".gitignore",
                    "README.md",
                    "demo_cli/__init__.py",
                    "demo_cli/__main__.py",
                    "demo_cli/cli.py",
                    "pyproject.toml",
                    "requirements.txt",
                    "tests/__init__.py",
                },
            )
            self.assertEqual(package_name, "demo_cli")
            self.assertEqual(
                template.vscode_entry_point,
                "demo_cli/cli.py",
            )
            self.assertTrue(
                (project_root / template.vscode_entry_point).is_file()
            )

            for filename in (
                "requirements.txt",
                "demo_cli/__init__.py",
                "tests/__init__.py",
            ):
                with self.subTest(filename=filename):
                    self.assertEqual(
                        (project_root / filename).read_text(
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

            for filename in (
                "demo_cli/__init__.py",
                "demo_cli/__main__.py",
                "demo_cli/cli.py",
            ):
                with self.subTest(filename=filename):
                    compile(
                        (project_root / filename).read_text(
                            encoding="utf-8",
                        ),
                        filename,
                        "exec",
                    )

            self.assertFalse((project_root / ".venv").exists())
            self.assertFalse((project_root / ".git").exists())
            self.assertFalse((project_root / ".vscode").exists())

    def test_package_name_is_normalized_to_a_python_identifier(self) -> None:
        cases = {
            "DemoCLI": "democli",
            "Demo-CLI": "demo_cli",
            "123 CLI": "_123_cli",
            "class": "class_",
        }

        for project_name, expected in cases.items():
            with self.subTest(project_name=project_name):
                self.assertEqual(
                    CliTemplate._normalize_package_name(project_name),
                    expected,
                )

    def test_package_name_rejects_names_without_ascii_letters_or_digits(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "must contain letters or digits",
        ):
            CliTemplate._normalize_package_name("---")

    def test_generated_module_runs_without_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root, package_name, _ = self._create_project(
                Path(temporary_directory),
            )

            result = self._run_module(project_root, package_name)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")

    def test_generated_module_displays_help(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root, package_name, _ = self._create_project(
                Path(temporary_directory),
            )

            result = self._run_module(
                project_root,
                package_name,
                "--help",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"usage: {package_name}", result.stdout)
            self.assertIn("--help", result.stdout)
            self.assertIn("--version", result.stdout)
            self.assertEqual(result.stderr, "")

    def test_generated_module_displays_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root, package_name, _ = self._create_project(
                Path(temporary_directory),
            )

            result = self._run_module(
                project_root,
                package_name,
                "--version",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout,
                f"{package_name} 0.1.0\n",
            )
            self.assertEqual(result.stderr, "")

    def test_generated_vscode_entry_point_runs_as_a_script(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root, package_name, template = self._create_project(
                Path(temporary_directory),
            )
            entry_point = template.vscode_entry_point

            if entry_point is None:
                self.fail("CLI template did not publish a VS Code entry point.")

            result = self._run_python(
                project_root,
                entry_point,
                "--version",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout,
                f"{package_name} 0.1.0\n",
            )
            self.assertEqual(result.stderr, "")

    def _create_project(
        self,
        parent: Path,
        project_name: str = "Demo-CLI",
    ) -> tuple[Path, str, CliTemplate]:
        project_root = parent / project_name
        package_name = CliTemplate._normalize_package_name(project_name)
        template = CliTemplate()

        with redirect_stdout(StringIO()):
            template.create(project_root)

        return project_root, package_name, template

    def _run_module(
        self,
        project_root: Path,
        package_name: str,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        return self._run_python(
            project_root,
            "-m",
            package_name,
            *arguments,
        )

    def _run_python(
        self,
        project_root: Path,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.pop("PYTHONHOME", None)
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONSAFEPATH", None)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"

        return subprocess.run(
            [
                sys.executable,
                *arguments,
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=environment,
            timeout=10,
            check=False,
        )


if __name__ == "__main__":
    unittest.main()