"""
Persistent user-level configuration for ForgePy.
"""

import json
import os
import tempfile
from collections.abc import Mapping
from json import JSONDecodeError
from pathlib import Path
from types import MappingProxyType

CONFIG_DIRECTORY_NAME = ".forgepy"
CONFIG_FILENAME = "config.json"

DEFAULT_CONFIG: Mapping[str, str] = MappingProxyType(
    {
        "default_template": "basic",
        "default_location": "",
        "author": "",
        "license": "MIT",
    }
)

SUPPORTED_SETTINGS = frozenset(DEFAULT_CONFIG)


class ForgePyConfigError(Exception):
    """
    Base error for ForgePy user configuration operations.
    """


class ConfigFormatError(ForgePyConfigError):
    """
    Raised when the configuration file is not valid ForgePy JSON data.
    """


class ConfigIOError(ForgePyConfigError):
    """
    Raised when the configuration file cannot be read or written.
    """


class UnknownConfigSettingError(ForgePyConfigError):
    """
    Raised when a setting is not supported by ForgePy.
    """


class InvalidConfigValueError(ForgePyConfigError):
    """
    Raised when a supported setting has an invalid value.
    """


class ConfigStore:
    """
    Load and persist ForgePy user configuration as JSON.

    A custom home directory can be provided for tests and isolated callers.
    """

    def __init__(
        self,
        home_directory: Path | None = None,
    ) -> None:
        self.home_directory = (
            Path.home()
            if home_directory is None
            else Path(home_directory)
        )
        self.config_directory = (
            self.home_directory
            / CONFIG_DIRECTORY_NAME
        )
        self.config_path = (
            self.config_directory
            / CONFIG_FILENAME
        )

    @staticmethod
    def defaults() -> dict[str, str]:
        """
        Return a new dictionary containing the safe defaults.
        """

        return dict(DEFAULT_CONFIG)

    def load(self) -> dict[str, str]:
        """
        Load configuration or return defaults when no file exists.
        """

        try:
            content = self.config_path.read_text(
                encoding="utf-8",
            )
            data = json.loads(content)
        except FileNotFoundError:
            return self.defaults()
        except UnicodeDecodeError as error:
            raise ConfigFormatError(
                "ForgePy configuration is not valid UTF-8 at "
                f"'{self.config_path}'."
            ) from error
        except JSONDecodeError as error:
            raise ConfigFormatError(
                "ForgePy configuration contains malformed JSON "
                f"at '{self.config_path}' "
                f"(line {error.lineno}, column {error.colno})."
            ) from error
        except OSError as error:
            raise ConfigIOError(
                "ForgePy could not read configuration from "
                f"'{self.config_path}': {error}"
            ) from error

        return self._normalize(data)

    def save(
        self,
        config: Mapping[str, str],
    ) -> dict[str, str]:
        """
        Validate and save configuration, creating its directory as needed.
        """

        normalized = self._normalize(config)
        serialized = json.dumps(
            normalized,
            indent=4,
            ensure_ascii=False,
        ) + "\n"

        try:
            self.config_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            temporary_path: Path | None = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    newline="\n",
                    dir=self.config_directory,
                    prefix=f".{CONFIG_FILENAME}.",
                    suffix=".tmp",
                    delete=False,
                ) as temporary_file:
                    temporary_path = Path(
                        temporary_file.name,
                    )
                    temporary_file.write(serialized)
                    temporary_file.flush()
                    os.fsync(temporary_file.fileno())

                temporary_path.replace(
                    self.config_path,
                )
            finally:
                if (
                    temporary_path is not None
                    and temporary_path.exists()
                ):
                    temporary_path.unlink()
        except OSError as error:
            raise ConfigIOError(
                "ForgePy could not save configuration to "
                f"'{self.config_path}': {error}"
            ) from error

        return normalized.copy()

    def reset(self) -> dict[str, str]:
        """
        Explicitly replace persisted configuration with the safe defaults.
        """

        return self.save(self.defaults())

    def update(
        self,
        setting: str,
        value: str,
    ) -> dict[str, str]:
        """
        Update one supported setting while preserving all other values.
        """

        self._validate_setting(setting)
        self._validate_value(setting, value)

        config = self.load()
        config[setting] = value

        return self.save(config)

    def _normalize(
        self,
        data: object,
    ) -> dict[str, str]:
        if not isinstance(data, Mapping):
            raise ConfigFormatError(
                "ForgePy configuration must contain a JSON object."
            )

        normalized = self.defaults()

        for setting, value in data.items():
            self._validate_setting(setting)
            self._validate_value(setting, value)
            normalized[setting] = value

        return normalized

    @staticmethod
    def _validate_setting(setting: object) -> None:
        if setting not in SUPPORTED_SETTINGS:
            raise UnknownConfigSettingError(
                f"Unknown ForgePy configuration setting: '{setting}'."
            )

    @staticmethod
    def _validate_value(
        setting: object,
        value: object,
    ) -> None:
        if not isinstance(value, str):
            raise InvalidConfigValueError(
                "ForgePy configuration setting "
                f"'{setting}' must be a string."
            )
