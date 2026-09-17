"""
ForgePy Commands

Seluruh command bawaan didaftarkan pada module ini.
"""

from cli.command import Command
from cli.commands.component_command import ComponentCommand
from cli.commands.config_command import ConfigCommand
from cli.commands.create_command import CreateCommand
from cli.commands.list_command import ListCommand
from cli.commands.version_command import VersionCommand

DEFAULT_COMMAND = "create"


def create_commands() -> tuple[Command, ...]:
    """
    Membuat seluruh command bawaan dalam urutan tampilan CLI.

    Command baru hanya perlu ditambahkan pada catalog ini agar parser
    dan dispatcher menggunakan registrasi yang sama.
    """

    return (
        CreateCommand(),
        VersionCommand(),
        ListCommand(),
        ConfigCommand(),
        ComponentCommand(),
    )
