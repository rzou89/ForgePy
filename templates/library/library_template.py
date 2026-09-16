"""
==================================================
ForgePy
Library Template
==================================================
"""

from pathlib import Path

from templates.library.library_files import LibraryFiles
from templates.template_engine.file_template import FileTemplate
from templates.template_engine.package_name import normalize_package_name
from templates.template_engine.template_context import TemplateContext
from templates.template_engine.template_metadata import TemplateMetadata


class LibraryTemplate(FileTemplate):
    """Generate a minimal reusable Python package project."""

    _METADATA = TemplateMetadata(
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
    )

    _DEFAULT_VSCODE_ENTRY_POINT = None

    def _build_context(
        self,
        project_path: Path,
    ) -> TemplateContext:
        return TemplateContext(
            project_path=project_path,
            package_name=self._normalize_package_name(project_path.name),
        )

    def _folders(self, context: TemplateContext) -> tuple[str, ...]:
        return (
            context.require_package_name(),
            "tests",
        )

    def _files(self, context: TemplateContext) -> dict[str, str]:
        return LibraryFiles.build(
            project_name=context.project_name,
            package_name=context.require_package_name(),
        )

    @staticmethod
    def _normalize_package_name(project_name: str) -> str:
        return normalize_package_name(
            project_name,
            package_label="library",
        )