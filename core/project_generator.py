import os
from pathlib import Path

from builders.python_tools_builder import PythonToolsBuilder
from core.environment_builder import EnvironmentBuilder
from core.git_builder import GitBuilder
from core.requirements_installer import RequirementsInstaller
from core.vscode_builder import VSCodeBuilder
from models.project_config import ProjectConfig
from templates.template_engine.template_registry import TemplateRegistry


class ProjectPreflightError(ValueError):
    """An expected project validation failure before root creation."""


class UnknownProjectTemplateError(KeyError):
    """The requested project template is not registered."""


class ProjectGenerator:

    def create(
        self,
        project_name: str,
        location: str,
        template_name: str = "basic",
    ) -> None:

        try:
            location_path = Path(location).resolve()

            if not location_path.exists():
                raise ValueError(
                    f"Project location does not exist: '{location_path}'."
                )

            if not location_path.is_dir():
                raise ValueError(
                    f"Project location must be a directory: '{location_path}'."
                )

            config = ProjectConfig(
                name=project_name,
                location=location_path,
            )

            destination = config.root

            if os.path.lexists(destination):
                raise FileExistsError(
                    f"Project destination already exists: '{destination}'."
                )

            resolved_destination = destination.resolve(strict=False)

            if resolved_destination.parent != location_path:
                raise ValueError(
                    "Project destination must remain directly below the "
                    f"selected location: '{resolved_destination}'."
                )

            registry = TemplateRegistry()

            try:
                template = registry.get(template_name)
            except KeyError as error:
                raise UnknownProjectTemplateError(template_name) from error

            template.preflight(destination)
        except ValueError as error:
            raise ProjectPreflightError(str(error)) from error

        destination.mkdir(
            parents=True,
            exist_ok=False,
        )

        # ==========================
        # Template
        # ==========================

        template.create(config.root)

        # ==========================
        # Virtual Environment
        # ==========================

        EnvironmentBuilder().create(config.root)

        # ==========================
        # Update Python Tools
        # ==========================

        PythonToolsBuilder().update(config.root)

        # ==========================
        # Install Requirements
        # ==========================

        RequirementsInstaller().install(config.root)

        # ==========================
        # VSCode
        # ==========================

        VSCodeBuilder().create(
            config.root,
            entry_point=template.vscode_entry_point,
        )

        # ==========================
        # Git
        # ==========================

        GitBuilder().create(config.root)

        print()
        print("=" * 40)
        print("Project berhasil dibuat.")
        print(config.root)
        print("=" * 40)
