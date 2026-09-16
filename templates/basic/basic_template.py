"""
==================================================
ForgePy
Basic Template
==================================================
"""

from config.default_structure import DEFAULT_FOLDERS
from templates.basic.basic_files import BasicFiles
from templates.template_engine.file_template import FileTemplate
from templates.template_engine.template_context import TemplateContext
from templates.template_engine.template_metadata import TemplateMetadata


class BasicTemplate(FileTemplate):

    _METADATA = TemplateMetadata(
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
    )

    _DEFAULT_VSCODE_ENTRY_POINT = "app.py"

    def _folders(self, context: TemplateContext) -> tuple[str, ...]:
        del context
        return tuple(DEFAULT_FOLDERS)

    def _files(self, context: TemplateContext) -> dict[str, str]:
        return BasicFiles.build(context.project_name)