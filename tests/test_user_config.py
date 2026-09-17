import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config.user_config import (
    CONFIG_DIRECTORY_NAME,
    CONFIG_FILENAME,
    ConfigFormatError,
    ConfigIOError,
    ConfigStore,
    InvalidConfigValueError,
    UnknownConfigSettingError,
)


class ConfigStoreTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)

        self.home_directory = Path(
            self.temporary_directory.name,
        )
        self.store = ConfigStore(
            home_directory=self.home_directory,
        )

    def test_uses_expected_path_below_injected_home(self) -> None:
        expected = (
            self.home_directory
            / CONFIG_DIRECTORY_NAME
            / CONFIG_FILENAME
        )

        self.assertEqual(self.store.config_path, expected)

    def test_load_returns_independent_defaults_when_file_is_missing(
        self,
    ) -> None:
        first = self.store.load()
        first["author"] = "Changed locally"

        self.assertEqual(
            self.store.load(),
            {
                "default_template": "basic",
                "default_location": "",
                "author": "",
                "license": "MIT",
            },
        )
        self.assertFalse(self.store.config_directory.exists())

    def test_load_wraps_file_system_read_error(self) -> None:
        self._write_raw_config(
            json.dumps(
                {
                    "author": "Existing Author",
                }
            )
        )
        original = self.store.config_path.read_bytes()

        with patch(
            "config.user_config.Path.read_text",
            side_effect=PermissionError("access denied"),
        ), self.assertRaisesRegex(
            ConfigIOError,
            "ForgePy could not read configuration",
        ):
            self.store.load()

        self.assertEqual(
            self.store.config_path.read_bytes(),
            original,
        )

    def test_save_creates_directory_and_round_trips_json(self) -> None:
        config = {
            "default_template": "basic",
            "default_location": "D:/Projects",
            "author": "ForgePy Maintainer",
            "license": "MIT",
        }

        saved = self.store.save(config)

        self.assertTrue(self.store.config_directory.is_dir())
        self.assertTrue(self.store.config_path.is_file())
        self.assertEqual(saved, config)
        self.assertEqual(self.store.load(), config)
        self.assertEqual(
            sorted(
                path.name
                for path in self.store.config_directory.iterdir()
            ),
            [CONFIG_FILENAME],
        )

        persisted = json.loads(
            self.store.config_path.read_text(
                encoding="utf-8",
            )
        )
        self.assertEqual(persisted, config)

    def test_save_fills_in_missing_settings_with_defaults(self) -> None:
        saved = self.store.save(
            {
                "author": "ForgePy Maintainer",
            }
        )

        self.assertEqual(
            saved,
            {
                "default_template": "basic",
                "default_location": "",
                "author": "ForgePy Maintainer",
                "license": "MIT",
            },
        )

    def test_failed_atomic_replace_preserves_existing_file(self) -> None:
        self.store.save(
            {
                "author": "Original Author",
            }
        )
        original = self.store.config_path.read_bytes()

        with patch(
            "config.user_config.Path.replace",
            side_effect=OSError("replace failed"),
        ), self.assertRaisesRegex(
            ConfigIOError,
            "ForgePy could not save configuration",
        ):
            self.store.update(
                "author",
                "Replacement Author",
            )

        self.assertEqual(
            self.store.config_path.read_bytes(),
            original,
        )
        self.assertEqual(
            sorted(
                path.name
                for path in self.store.config_directory.iterdir()
            ),
            [CONFIG_FILENAME],
        )

    def test_load_fills_in_missing_settings_with_defaults(self) -> None:
        self._write_raw_config(
            json.dumps(
                {
                    "author": "ForgePy Maintainer",
                }
            )
        )

        self.assertEqual(
            self.store.load(),
            {
                "default_template": "basic",
                "default_location": "",
                "author": "ForgePy Maintainer",
                "license": "MIT",
            },
        )

    def test_update_changes_supported_setting_and_preserves_others(
        self,
    ) -> None:
        self.store.save(
            {
                "author": "Initial Author",
                "default_location": "D:/Projects",
            }
        )

        updated = self.store.update(
            "author",
            "Updated Author",
        )

        self.assertEqual(updated["author"], "Updated Author")
        self.assertEqual(
            updated["default_location"],
            "D:/Projects",
        )
        self.assertEqual(self.store.load(), updated)

    def test_update_rejects_unknown_setting(self) -> None:
        with self.assertRaisesRegex(
            UnknownConfigSettingError,
            "Unknown ForgePy configuration setting",
        ):
            self.store.update(
                "unsupported",
                "value",
            )

        self.assertFalse(self.store.config_path.exists())

    def test_save_rejects_unknown_setting(self) -> None:
        with self.assertRaises(UnknownConfigSettingError):
            self.store.save(
                {
                    "unsupported": "value",
                }
            )

        self.assertFalse(self.store.config_path.exists())

    def test_save_rejects_non_string_value(self) -> None:
        with self.assertRaises(InvalidConfigValueError):
            self.store.save(
                {
                    "author": 42,
                }
            )

        self.assertFalse(self.store.config_path.exists())

    def test_malformed_json_raises_without_overwriting_file(self) -> None:
        malformed = '{"author": "Incomplete"'
        self._write_raw_config(malformed)

        with self.assertRaisesRegex(
            ConfigFormatError,
            "ForgePy configuration contains malformed JSON",
        ):
            self.store.load()

        with self.assertRaises(ConfigFormatError):
            self.store.update(
                "author",
                "Updated Author",
            )

        self.assertEqual(
            self.store.config_path.read_text(
                encoding="utf-8",
            ),
            malformed,
        )

    def test_load_rejects_json_that_is_not_an_object(self) -> None:
        self._write_raw_config("[]")

        with self.assertRaisesRegex(
            ConfigFormatError,
            "must contain a JSON object",
        ):
            self.store.load()

    def test_load_rejects_invalid_utf8(self) -> None:
        self.store.config_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.store.config_path.write_bytes(b"\xff")

        with self.assertRaisesRegex(
            ConfigFormatError,
            "not valid UTF-8",
        ):
            self.store.load()

    def test_load_rejects_unknown_setting_from_file(self) -> None:
        self._write_raw_config(
            json.dumps(
                {
                    "unsupported": "value",
                }
            )
        )

        with self.assertRaises(UnknownConfigSettingError):
            self.store.load()

    def test_reset_writes_and_returns_defaults(self) -> None:
        self.store.save(
            {
                "author": "Temporary Author",
                "license": "Custom",
            }
        )

        reset = self.store.reset()

        self.assertEqual(reset, ConfigStore.defaults())
        self.assertEqual(self.store.load(), ConfigStore.defaults())

    def test_reset_explicitly_replaces_malformed_file(self) -> None:
        self._write_raw_config('{"author":')

        reset = self.store.reset()

        self.assertEqual(reset, ConfigStore.defaults())
        self.assertEqual(self.store.load(), ConfigStore.defaults())

    def _write_raw_config(self, content: str) -> None:
        self.store.config_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.store.config_path.write_text(
            content,
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
