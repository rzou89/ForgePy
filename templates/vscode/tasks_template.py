"""
==================================================
ForgePy
Author  : Rendy Zou
Module  : VSCode Tasks Template
==================================================

Deskripsi:
- Template tasks.json untuk Visual Studio Code.
- Menyediakan task aplikasi jika tersedia dan install dependencies.
"""

import json

from core.venv_paths import get_venv_python_relative_path


def build(entry_point: str | None = "app.py") -> str:

    python_path = get_venv_python_relative_path().as_posix()
    workspace_python = f"${{workspaceFolder}}/{python_path}"

    tasks = []

    if entry_point is not None:
        tasks.append(
            {
                "label": "Run Application",
                "type": "shell",
                "command": workspace_python,
                "args": [
                    entry_point
                ],
                "group": {
                    "kind": "build",
                    "isDefault": True
                },
                "presentation": {
                    "reveal": "always"
                },
                "problemMatcher": []
            }
        )

    tasks.append(
        {
            "label": "Install Requirements",
            "type": "shell",
            "command": workspace_python,
            "args": [
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt"
            ],
            "presentation": {
                "reveal": "always"
            },
            "problemMatcher": []
        }
    )

    task_configuration = {
        "version": "2.0.0",
        "tasks": tasks,
    }

    return json.dumps(
        task_configuration,
        indent=4,
        ensure_ascii=False,
    )