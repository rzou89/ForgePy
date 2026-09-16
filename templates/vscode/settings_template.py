"""
==================================================
ForgePy
Author  : Rendy Zou
Module  : VSCode Settings Template
==================================================

Deskripsi:
- Template settings.json untuk Visual Studio Code.
"""

import json

from core.venv_paths import get_venv_python_relative_path


def build() -> str:

    interpreter_path = get_venv_python_relative_path().as_posix()

    settings = {
        "python.defaultInterpreterPath": interpreter_path,

        "python.analysis.typeCheckingMode": "basic",

        "python.analysis.autoImportCompletions": True,

        "editor.formatOnSave": True,

        "editor.tabSize": 4,

        "files.trimTrailingWhitespace": True,

        "files.insertFinalNewline": True,
    }

    return json.dumps(
        settings,
        indent=4,
        ensure_ascii=False,
    )