"""
==================================================
ForgePy
Module  : Create Command
==================================================
"""

import subprocess
from argparse import ArgumentParser, Namespace
from pathlib import Path

from cli.command import Command
from config.user_config import ConfigStore, ForgePyConfigError
from core.project_generator import (
    ProjectGenerator,
    ProjectPreflightError,
    UnknownProjectTemplateError,
)
from templates.template_engine.template_metadata import TemplateMetadata
from templates.template_engine.template_registry import TemplateRegistry


class CreateCommand(Command):
    """
    Membuat project baru melalui ProjectGenerator.
    """

    name = "create"
    summary = "Create a new Python project."
    description = (
        "Create a Python project from a registered ForgePy template. "
        "ForgePy prompts for an omitted project name and resolves omitted "
        "location or template values from user configuration before using "
        "the existing interactive or basic fallback."
    )

    def __init__(
        self,
        store: ConfigStore | None = None,
    ) -> None:
        self._store = store

    def configure_parser(
        self,
        parser: ArgumentParser,
    ) -> None:
        parser.add_argument(
            "project_name",
            nargs="?",
            metavar="PROJECT_NAME",
            help=(
                "Name of the project to create. "
                "ForgePy prompts for it when omitted."
            ),
        )

        parser.add_argument(
            "--location",
            "-l",
            metavar="PATH",
            help=(
                "Existing parent directory for the new project. "
                "When omitted, ForgePy uses configured default_location "
                "before prompting."
            ),
        )

        parser.add_argument(
            "--template",
            "-t",
            metavar="NAME",
            help=(
                "Registered project template to use. When omitted in "
                "advanced CLI mode, ForgePy uses configured "
                "default_template, then basic."
            ),
        )

    def execute(self, args: Namespace) -> int:
        interactive_mode = (
            getattr(args, "command", "create") is None
        )

        location = getattr(
            args,
            "location",
            None,
        )
        template_name = getattr(
            args,
            "template",
            None,
        )

        user_config: dict[str, str] = {}

        needs_config = (
            location is None
            or (
                not interactive_mode
                and template_name is None
            )
        )

        if needs_config:
            try:
                user_config = self._get_store().load()
            except ForgePyConfigError as error:
                print(f"[ERROR] {error}")
                print(
                    "[INFO] Run 'python main.py config reset' or supply "
                    "both --location and --template explicitly."
                )
                return 1

        project_name = getattr(
            args,
            "project_name",
            None,
        )

        if not project_name:
            project_name = input(
                "Project Name : "
            ).strip()

        if location is None:
            location = user_config.get(
                "default_location",
                "",
            )

        if not location:
            location = input(
                "Location : "
            ).strip()

        if not project_name:
            print("[ERROR] Nama project tidak boleh kosong.")
            return 1

        if not location:
            print("[ERROR] Lokasi project tidak boleh kosong.")
            return 1

        if interactive_mode and template_name is None:
            template_metadata = self._select_template(
                project_name=project_name,
                location=location,
            )

            if template_metadata is None:
                print("[INFO] Project creation cancelled.")
                return 0

            template_name = template_metadata.name

            if not self._confirm_project(
                project_name=project_name,
                location=location,
                template_metadata=template_metadata,
            ):
                print("[INFO] Project creation cancelled.")
                return 0

        elif template_name is None:
            template_name = user_config.get(
                "default_template",
                "",
            )

        template_name = template_name or "basic"

        generator = ProjectGenerator()

        try:
            generator.create(
                project_name=project_name,
                location=location,
                template_name=template_name,
            )
        except UnknownProjectTemplateError:
            print(f"[ERROR] Unknown project template: '{template_name}'.")
            return 1
        except (
            ProjectPreflightError,
            OSError,
            subprocess.SubprocessError,
        ) as error:
            print(f"[ERROR] Project creation failed: {error}")
            return 1

        return 0

    def _select_template(
        self,
        *,
        project_name: str,
        location: str,
    ) -> TemplateMetadata | None:
        registry = TemplateRegistry()

        templates = tuple(
            sorted(
                registry.list_metadata(),
                key=lambda metadata: metadata.name,
            )
        )

        print()
        print("=" * 50)
        print("              FORGEPY PROJECT WIZARD")
        print("=" * 50)
        print()
        print(f"Project Name : {project_name}")
        print(f"Location     : {location}")
        print()
        print("What do you want to create?")
        print()

        for index, metadata in enumerate(
            templates,
            start=1,
        ):
            print(
                f"[{index}] {metadata.friendly_name}"
            )
            print(
                f"    Template: {metadata.name}"
            )

            if metadata.use_cases:
                print()
                print("    Cocok untuk:")

                for use_case in metadata.use_cases:
                    print(f"    - {use_case}")

            print()

        print("[0] Cancel")
        print()

        while True:
            selection = input(
                f"Select template [0-{len(templates)}]: "
            ).strip()

            if selection == "0":
                return None

            try:
                selected_index = int(selection)
            except ValueError:
                selected_index = -1

            if 1 <= selected_index <= len(templates):
                return templates[selected_index - 1]

            print(
                "[ERROR] Invalid selection. "
                f"Choose a number from 0 to {len(templates)}."
            )

    def _confirm_project(
        self,
        *,
        project_name: str,
        location: str,
        template_metadata: TemplateMetadata,
    ) -> bool:
        project_folder = (
            Path(location).expanduser()
            / project_name
        )

        print()
        print("=" * 50)
        print("CONFIRMATION")
        print("=" * 50)
        print()
        print("Project Summary")
        print("-" * 40)
        print(f"Name     : {project_name}")
        print(f"Location : {location}")
        print(
            "Template : "
            f"{template_metadata.friendly_name}"
        )
        print(f"Folder   : {project_folder}")
        print()

        while True:
            confirmation = input(
                "Create this project? [Y/n]: "
            ).strip().lower()

            if confirmation in (
                "",
                "y",
                "yes",
            ):
                return True

            if confirmation in (
                "n",
                "no",
            ):
                return False

            print(
                "[ERROR] Invalid confirmation. "
                "Enter Y or n."
            )

    def _get_store(self) -> ConfigStore:
        if self._store is None:
            self._store = ConfigStore()

        return self._store