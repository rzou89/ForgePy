import hashlib
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import ClassVar

from templates.basic.basic_files import BasicFiles
from templates.basic.basic_template import BasicTemplate
from templates.cli.cli_template import CliTemplate
from templates.library.library_template import LibraryTemplate
from templates.template_engine.template_context import TemplateContext
from templates.template_engine.template_files import TemplateFiles


class TemplateArchitectureTests(unittest.TestCase):

    maxDiff = None

    _EXPECTED_DIRECTORIES: ClassVar = {
        "basic": {
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
        "library": {
            "demo_lib",
            "tests",
        },
        "cli": {
            "demo_cli",
            "tests",
        },
    }

    # SHA-256 values pin the normalized UTF-8 text produced before the
    # architecture refactor, independently of the production renderers.
    _EXPECTED_TEMPLATE_FILES: ClassVar = {
        "basic": {
            ".env": (
                "d4eeb664f84278ae0f07b0065cd04d1f"
                "23dcd20a9aca47a2be9355e263198c25"
            ),
            ".env.example": (
                "2c83de155477ca71d7d74018e00bf659"
                "6ba2322b4bc413beb094c56d8473e927"
            ),
            ".gitignore": (
                "df8b12f527ad69fc27b602838efe6fe9"
                "9e47ff72d9eda0cfeb9dbb05a345119a"
            ),
            "CHANGELOG.md": (
                "e7c8c5012e26e2fe4258e77adcca4d0a"
                "9cc54838ee1ebf4cfd7f8e3fb63a5237"
            ),
            "LICENSE": (
                "b120536aadd0b21e256cad2487292a86"
                "a87c9a9d8c8992ff320ccb020120b573"
            ),
            "README.md": (
                "6648c116097766b11b14783a95294996"
                "9cc31744bb2d6e64df12c9db753a365f"
            ),
            "app.py": (
                "767efdf39597895de115d5adb945a4f9"
                "8bebff02855a18fea62c868942301589"
            ),
            "pyproject.toml": (
                "968bc1f396b65c358a8ef2c80113d5ef"
                "9e339bf45a6f9fee6ba326342e9074e6"
            ),
            "requirements.txt": (
                "ced372f3f49cf662fa8851d9189050a8"
                "b0e04083b0ffc278bbb568d9b9e0c927"
            ),
        },
        "library": {
            ".gitignore": (
                "df8b12f527ad69fc27b602838efe6fe9"
                "9e47ff72d9eda0cfeb9dbb05a345119a"
            ),
            "README.md": (
                "2d635e470f59dcc468aa7531135d85f1"
                "603ef85440a2a1f70c9829e9d1b5141d"
            ),
            "demo_lib/__init__.py": (
                "e3b0c44298fc1c149afbf4c8996fb924"
                "27ae41e4649b934ca495991b7852b855"
            ),
            "pyproject.toml": (
                "6d96c8cfce401bd431d5950224e8311c"
                "7c9ae5d099f791f879a8f66dcd31cad3"
            ),
            "requirements.txt": (
                "e3b0c44298fc1c149afbf4c8996fb924"
                "27ae41e4649b934ca495991b7852b855"
            ),
            "tests/__init__.py": (
                "e3b0c44298fc1c149afbf4c8996fb924"
                "27ae41e4649b934ca495991b7852b855"
            ),
        },
        "cli": {
            ".gitignore": (
                "df8b12f527ad69fc27b602838efe6fe9"
                "9e47ff72d9eda0cfeb9dbb05a345119a"
            ),
            "README.md": (
                "ca3731503d6998b23861678e5609f470"
                "d72320c14f14ef428e6f591ec210c72f"
            ),
            "demo_cli/__init__.py": (
                "e3b0c44298fc1c149afbf4c8996fb924"
                "27ae41e4649b934ca495991b7852b855"
            ),
            "demo_cli/__main__.py": (
                "1bee254006ed1d55fc5accd1b586300c"
                "0b2cef38b6db5862fece037ecef625aa"
            ),
            "demo_cli/cli.py": (
                "dc6b0433b0333e2288f08fe7f4411158"
                "b3e772328653189937dc6afa61476587"
            ),
            "pyproject.toml": (
                "e58930f7d434ab9599ca92a521850303"
                "6a6377798d87f690d445d29374e08484"
            ),
            "requirements.txt": (
                "e3b0c44298fc1c149afbf4c8996fb924"
                "27ae41e4649b934ca495991b7852b855"
            ),
            "tests/__init__.py": (
                "e3b0c44298fc1c149afbf4c8996fb924"
                "27ae41e4649b934ca495991b7852b855"
            ),
        },
    }

    def test_context_separates_project_and_package_names(self) -> None:
        context = TemplateContext(
            project_path=Path("Demo-Lib"),
            package_name="demo_lib",
        )

        self.assertEqual(context.project_name, "Demo-Lib")
        self.assertEqual(context.require_package_name(), "demo_lib")

        with self.assertRaisesRegex(ValueError, "does not define"):
            TemplateContext(Path("BasicDemo")).require_package_name()

    def test_basic_file_facade_preserves_existing_mapping_api(self) -> None:
        self.assertEqual(
            TemplateFiles.basic("CompatibilityDemo"),
            BasicFiles.build("CompatibilityDemo"),
        )

    def test_built_in_vscode_entry_points_are_explicit(self) -> None:
        self.assertEqual(BasicTemplate().vscode_entry_point, "app.py")
        self.assertIsNone(LibraryTemplate().vscode_entry_point)
        self.assertIsNone(CliTemplate().vscode_entry_point)

    def test_generated_outputs_match_pre_refactor_contract(self) -> None:
        cases = (
            ("basic", "BasicDemo", BasicTemplate),
            ("library", "Demo-Lib", LibraryTemplate),
            ("cli", "Demo-CLI", CliTemplate),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)

            for template_name, project_name, template_type in cases:
                with self.subTest(template=template_name):
                    project_root = parent / project_name
                    template = template_type()

                    with redirect_stdout(StringIO()):
                        template.create(project_root)

                    self.assertEqual(
                        self._directory_manifest(project_root),
                        self._EXPECTED_DIRECTORIES[template_name],
                    )
                    self.assertEqual(
                        self._file_manifest(project_root),
                        self._EXPECTED_TEMPLATE_FILES[template_name],
                    )

    def test_cli_vscode_entry_point_is_resolved_for_each_context(self) -> None:
        template = CliTemplate()

        self.assertIsNone(template.vscode_entry_point)

        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)

            for project_name, entry_point in (
                ("First-CLI", "first_cli/cli.py"),
                ("Second CLI", "second_cli/cli.py"),
            ):
                with self.subTest(project_name=project_name):
                    with redirect_stdout(StringIO()):
                        template.create(parent / project_name)

                    self.assertEqual(
                        template.vscode_entry_point,
                        entry_point,
                    )

    @staticmethod
    def _directory_manifest(project_root: Path) -> set[str]:
        return {
            path.relative_to(project_root).as_posix()
            for path in project_root.rglob("*")
            if path.is_dir()
        }

    @staticmethod
    def _file_manifest(project_root: Path) -> dict[str, str]:
        return {
            path.relative_to(project_root).as_posix(): hashlib.sha256(
                path.read_text(encoding="utf-8").encode("utf-8")
            ).hexdigest()
            for path in sorted(project_root.rglob("*"))
            if path.is_file()
        }


if __name__ == "__main__":
    unittest.main()
