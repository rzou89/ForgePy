from pathlib import Path

from templates.cli.cli_files import CliFiles
from templates.template_engine.file_template import FileTemplate
from templates.template_engine.package_name import normalize_package_name
from templates.template_engine.template_context import TemplateContext
from templates.template_engine.template_metadata import TemplateMetadata


class CliTemplate(FileTemplate):
    """Generate a minimal standard-library command-line application."""

    _METADATA = TemplateMetadata(
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
        return CliFiles.build(
            project_name=context.project_name,
            package_name=context.require_package_name(),
        )

    def _vscode_entry_point_for(
        self,
        context: TemplateContext,
    ) -> str | None:
        return f"{context.require_package_name()}/cli.py"

    @staticmethod
    def _normalize_package_name(project_name: str) -> str:
        return normalize_package_name(
            project_name,
            package_label="CLI",
        )