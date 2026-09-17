import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cli.commands import create_commands
from cli.commands.config_command import ConfigCommand
from cli.dispatcher import Dispatcher
from cli.parser import Parser
from config.user_config import ConfigStore


class ConfigCommandTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)

        self.home_directory = Path(
            self.temporary_directory.name,
        )
        self.store = ConfigStore(
            home_directory=self.home_directory,
        )
        self.commands = tuple(
            ConfigCommand(store=self.store)
            if isinstance(command, ConfigCommand)
            else command
            for command in create_commands()
        )

    def test_config_help_lists_supported_actions(self) -> None:
        output = StringIO()

        with patch(
            "sys.argv",
            [
                "forgepy",
                "config",
                "--help",
            ],
        ), redirect_stdout(output), self.assertRaises(SystemExit) as context:
            Parser(
                commands=self.commands,
            ).parse()

        self.assertEqual(context.exception.code, 0)
        help_text = output.getvalue()
        self.assertIn("show", help_text)
        self.assertIn("set", help_text)
        self.assertIn("reset", help_text)

    def test_config_show_displays_all_defaults_without_saving(self) -> None:
        output = self._run_cli(
            "config",
            "show",
        )

        self.assertIn("ForgePy Configuration", output)
        self.assertIn(
            'default_template = "basic"',
            output,
        )
        self.assertIn(
            'default_location = ""',
            output,
        )
        self.assertIn(
            'author = ""',
            output,
        )
        self.assertIn(
            'license = "MIT"',
            output,
        )
        self.assertFalse(self.store.config_directory.exists())

    def test_default_catalog_resolves_home_only_during_execution(
        self,
    ) -> None:
        output = StringIO()

        with patch(
            "config.user_config.Path.home",
            return_value=self.home_directory,
        ) as home, patch(
            "sys.argv",
            [
                "forgepy",
                "config",
                "show",
            ],
        ), redirect_stdout(output):
            args = Parser().parse()
            dispatcher = Dispatcher()

            home.assert_not_called()
            dispatcher.dispatch(args)

        home.assert_called_once_with()
        self.assertIn(
            'default_template = "basic"',
            output.getvalue(),
        )

    def test_config_set_persists_one_setting_and_show_reads_it(
        self,
    ) -> None:
        set_output = self._run_cli(
            "config",
            "set",
            "author",
            "Test User",
        )

        self.assertIn(
            'author = "Test User"',
            set_output,
        )
        self.assertEqual(
            self.store.load(),
            {
                "default_template": "basic",
                "default_location": "",
                "author": "Test User",
                "license": "MIT",
            },
        )

        show_output = self._run_cli(
            "config",
            "show",
        )
        self.assertIn(
            'author = "Test User"',
            show_output,
        )

    def test_config_set_rejects_unknown_setting(self) -> None:
        self.store.save(
            {
                "author": "Existing Author",
            }
        )
        original = self.store.config_path.read_bytes()

        output = self._run_cli(
            "config",
            "set",
            "unsupported",
            "value",
        )

        self.assertIn(
            "[ERROR] Unknown ForgePy configuration setting",
            output,
        )
        self.assertIn(
            "Supported settings:",
            output,
        )
        self.assertEqual(
            self.store.config_path.read_bytes(),
            original,
        )

    def test_config_reset_persists_defaults(self) -> None:
        self.store.save(
            {
                "author": "Temporary Author",
                "license": "Custom",
            }
        )

        output = self._run_cli(
            "config",
            "reset",
        )

        self.assertIn(
            "ForgePy configuration reset to defaults.",
            output,
        )
        self.assertEqual(
            self.store.load(),
            ConfigStore.defaults(),
        )

    def test_config_set_surfaces_malformed_json_without_overwrite(
        self,
    ) -> None:
        malformed = b'{"author": "Incomplete"'
        self.store.config_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.store.config_path.write_bytes(malformed)

        output = self._run_cli(
            "config",
            "set",
            "author",
            "Updated Author",
        )

        self.assertIn(
            "[ERROR] ForgePy configuration contains malformed JSON",
            output,
        )
        self.assertNotIn("Traceback", output)
        self.assertEqual(
            self.store.config_path.read_bytes(),
            malformed,
        )

    def _run_cli(
        self,
        *arguments: str,
    ) -> str:
        output = StringIO()

        with patch(
            "sys.argv",
            [
                "forgepy",
                *arguments,
            ],
        ), redirect_stdout(output):
            args = Parser(
                commands=self.commands,
            ).parse()
            Dispatcher(
                commands=self.commands,
            ).dispatch(args)

        return output.getvalue()


if __name__ == "__main__":
    unittest.main()
