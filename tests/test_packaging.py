"""Regression tests for ForgePy distribution metadata."""

import tomllib
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import main as application_entry
from components.component_registry import ComponentRegistry
from config.version import VERSION
from templates.template_engine.template_registry import TemplateRegistry


class PackagingMetadataTests(unittest.TestCase):

    project_root = Path(__file__).resolve().parents[1]
    pyproject_path = project_root / "pyproject.toml"
    manifest_path = project_root / "MANIFEST.in"
    changelog_path = project_root / "CHANGELOG.md"
    license_path = project_root / "LICENSE"
    required_packages = (
        "builders",
        "cli",
        "components",
        "config",
        "core",
        "models",
        "templates",
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = tomllib.loads(
            cls.pyproject_path.read_text(encoding="utf-8")
        )

    def test_packaging_metadata_is_parseable_and_standard(self) -> None:
        project = self.metadata["project"]

        self.assertEqual(
            self.metadata["build-system"]["build-backend"],
            "setuptools.build_meta",
        )
        self.assertEqual(project["name"], "forgepy-cli")
        self.assertEqual(
            project["readme"],
            {"file": "README.md", "content-type": "text/markdown"},
        )

    def test_release_metadata_uses_verified_repository_facts(self) -> None:
        project = self.metadata["project"]

        self.assertEqual(
            project["urls"],
            {
                "Homepage": "https://github.com/rzou89/ForgePy",
                "Repository": "https://github.com/rzou89/ForgePy",
                "Issues": "https://github.com/rzou89/ForgePy/issues",
            },
        )
        self.assertIn(
            "Development Status :: 5 - Production/Stable",
            project["classifiers"],
        )
        self.assertNotIn(
            "Development Status :: 4 - Beta",
            project["classifiers"],
        )
        self.assertEqual(project["license"], "MIT")
        self.assertEqual(project["license-files"], ["LICENSE"])
        self.assertFalse(
            any(
                classifier.startswith("License ::")
                for classifier in project["classifiers"]
            )
        )

    def test_repository_license_is_the_maintainer_selected_mit_license(
        self,
    ) -> None:
        license_text = self.license_path.read_text(encoding="utf-8")

        self.assertTrue(self.license_path.is_file())
        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 Rendy Zou", license_text)
        self.assertIn(
            "Permission is hereby granted, free of charge",
            license_text,
        )
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"', license_text)

    def test_changelog_has_an_unreleased_release_section(self) -> None:
        changelog = self.changelog_path.read_text(encoding="utf-8")

        self.assertIn("# Changelog", changelog)
        self.assertIn("## Unreleased", changelog)
        self.assertRegex(changelog, r"(?m)^## 1\.1\.0$")
        self.assertRegex(changelog, r"(?m)^## 1\.0\.0$")
        self.assertIn("## 1.0.0rc1", changelog)

    def test_required_runtime_packages_are_discovered_exclusively(self) -> None:
        discovery = self.metadata["tool"]["setuptools"]["packages"]["find"]

        self.assertEqual(
            discovery["include"],
            [f"{package}*" for package in self.required_packages],
        )
        self.assertIn("tests*", discovery["exclude"])

        for package in self.required_packages:
            with self.subTest(package=package):
                self.assertTrue(
                    (self.project_root / package / "__init__.py").is_file()
                )

    def test_distribution_uses_the_canonical_application_version(self) -> None:
        project = self.metadata["project"]
        dynamic_version = self.metadata["tool"]["setuptools"]["dynamic"]

        self.assertIn("version", project["dynamic"])
        self.assertEqual(
            dynamic_version["version"]["attr"],
            "config.version.VERSION",
        )
        self.assertEqual(VERSION, "1.1.0")

    def test_console_script_delegates_to_existing_main(self) -> None:
        self.assertEqual(
            self.metadata["project"]["scripts"]["forgepy"],
            "main:main",
        )

        arguments = object()
        parser = Mock()
        parser.parse.return_value = arguments
        dispatcher = Mock()
        dispatcher.dispatch.return_value = 7

        with patch("main.Parser", return_value=parser):
            with patch("main.Dispatcher", return_value=dispatcher):
                self.assertEqual(application_entry.main(), 7)

        dispatcher.dispatch.assert_called_once_with(arguments)

    def test_built_ins_remain_available_from_packaged_modules(self) -> None:
        self.assertEqual(
            tuple(TemplateRegistry().list_templates()),
            ("basic", "library", "cli"),
        )
        self.assertEqual(
            tuple(
                component.name
                for component in ComponentRegistry().list_components()
            ),
            ("pytest", "ruff", "github-actions"),
        )

    def test_distribution_declares_no_python_runtime_dependencies(self) -> None:
        self.assertEqual(self.metadata["project"]["dependencies"], [])

    def test_support_metadata_declares_the_python_contract(self) -> None:
        project = self.metadata["project"]

        self.assertEqual(project["requires-python"], ">=3.12")
        self.assertNotIn(",", project["requires-python"])
        self.assertTrue(
            {
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3 :: Only",
                "Programming Language :: Python :: 3.12",
                "Programming Language :: Python :: 3.13",
                "Programming Language :: Python :: 3.14",
                "Programming Language :: Python :: Implementation :: CPython",
            }.issubset(project["classifiers"])
        )

    def test_support_metadata_declares_windows_and_linux(self) -> None:
        project = self.metadata["project"]
        classifiers = project["classifiers"]

        self.assertIn("Operating System :: Microsoft :: Windows", classifiers)
        self.assertIn("Operating System :: POSIX :: Linux", classifiers)
        self.assertFalse(
            any(
                "MacOS" in classifier
                for classifier in classifiers
            )
        )
        self.assertEqual(project["license"], "MIT")
        self.assertEqual(project["license-files"], ["LICENSE"])
        self.assertFalse(
            any(
                classifier.startswith("License ::")
                for classifier in classifiers
            )
        )

    def test_support_documentation_matches_packaging_metadata(self) -> None:
        for document_name in (
            "ARCHITECTURE.md",
            "PROJECT_CONTEXT.md",
            "CONTRIBUTING.md",
        ):
            with self.subTest(document=document_name):
                document = (self.project_root / document_name).read_text(
                    encoding="utf-8"
                )
                normalized_document = document.casefold()

                self.assertIn("officially supports windows", normalized_document)
                self.assertIn("linux", normalized_document)
                self.assertIn("cpython 3.12+", normalized_document)
                for python_version in ("3.12", "3.13", "3.14"):
                    self.assertIn(python_version, normalized_document)
                self.assertIn("macos", normalized_document)
                self.assertTrue(
                    "unsupported" in normalized_document
                    or "unverified" in normalized_document
                )

    def test_sdist_manifest_excludes_only_repository_packages(self) -> None:
        directives = self.manifest_path.read_text(
            encoding="utf-8"
        ).splitlines()

        self.assertEqual(
            directives,
            ["include CHANGELOG.md", "prune tests", "prune utils"],
        )
        self.assertTrue((self.project_root / "main.py").is_file())
        self.assertTrue(self.pyproject_path.is_file())
        self.assertTrue(self.changelog_path.is_file())

        for package in self.required_packages:
            with self.subTest(package=package):
                self.assertTrue((self.project_root / package).is_dir())


if __name__ == "__main__":
    unittest.main()
