"""
==================================================
ForgePy
Author  : Rendy Zou
Module  : VSCode Builder
==================================================

Deskripsi:
- Membuat konfigurasi Visual Studio Code
- (.vscode/settings.json)
- (.vscode/launch.json)
- (.vscode/tasks.json)
- (.vscode/extensions.json)
"""

from pathlib import Path

from templates.vscode import (
    extensions_template,
    launch_template,
    settings_template,
    tasks_template,
)


class VSCodeBuilder:
    """
    Builder untuk membuat konfigurasi Visual Studio Code.
    """

    def create(
        self,
        project_root: Path,
        entry_point: str | None = "app.py",
    ) -> None:

        vscode_folder = project_root / ".vscode"
        vscode_folder.mkdir(exist_ok=True)

        self._write_settings(vscode_folder)
        self._write_launch(
            vscode_folder,
            entry_point,
        )
        self._write_tasks(
            vscode_folder,
            entry_point,
        )
        self._write_extensions(vscode_folder)

        print("[OK] VS Code configuration berhasil dibuat.")

    def _write_settings(self, vscode_folder: Path) -> None:

        path = vscode_folder / "settings.json"

        path.write_text(
            settings_template.build(),
            encoding="utf-8",
        )

        print(f"[OK] File dibuat : {path}")

    def _write_launch(
        self,
        vscode_folder: Path,
        entry_point: str | None,
    ) -> None:

        path = vscode_folder / "launch.json"

        path.write_text(
            launch_template.build(entry_point),
            encoding="utf-8",
        )

        print(f"[OK] File dibuat : {path}")

    def _write_tasks(
        self,
        vscode_folder: Path,
        entry_point: str | None,
    ) -> None:

        path = vscode_folder / "tasks.json"

        path.write_text(
            tasks_template.build(entry_point),
            encoding="utf-8",
        )

        print(f"[OK] File dibuat : {path}")

    def _write_extensions(self, vscode_folder: Path) -> None:

        path = vscode_folder / "extensions.json"

        path.write_text(
            extensions_template.build(),
            encoding="utf-8",
        )

        print(f"[OK] File dibuat : {path}")
