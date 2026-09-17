import unicodedata
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

WINDOWS_INVALID_NAME_CHARACTERS = frozenset('<>:"/\\|?*')
WINDOWS_RESERVED_NAME_STEMS = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{number}" for number in range(1, 10)}
    | {f"LPT{number}" for number in range(1, 10)}
    | {f"COM{number}" for number in ("¹", "²", "³")}
    | {f"LPT{number}" for number in ("¹", "²", "³")}
)


@dataclass(slots=True)
class ProjectConfig:
    """
    Menyimpan konfigurasi project.
    """

    name: str
    location: Path

    def __post_init__(self) -> None:
        """Validate the name used to construct the project destination."""

        if not isinstance(self.name, str):
            raise TypeError("Project name must be a string.")

        if not self.name:
            raise ValueError("Project name must not be empty.")

        if not self.name.strip():
            raise ValueError("Project name must not contain only whitespace.")

        if self.name.startswith(" "):
            raise ValueError("Project name must not begin with an ASCII space.")

        if self.name in {".", ".."}:
            raise ValueError("Project name must be one filesystem path segment.")

        if any(
            character in WINDOWS_INVALID_NAME_CHARACTERS
            for character in self.name
        ):
            raise ValueError(
                "Project name contains a Windows-invalid filename character."
            )

        if any(
            unicodedata.category(character) == "Cc"
            for character in self.name
        ):
            raise ValueError("Project name must not contain control characters.")

        try:
            self.name.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ValueError(
                "Project name must be valid Unicode for UTF-8 output."
            ) from error

        if self.name.endswith((" ", ".")):
            raise ValueError("Project name must not end with a space or dot.")

        reserved_stem = self.name.split(".", maxsplit=1)[0].upper()
        if reserved_stem in WINDOWS_RESERVED_NAME_STEMS:
            raise ValueError(
                "Project name must not use a Windows reserved device name."
            )

        path_name = Path(self.name)
        windows_name = PureWindowsPath(self.name)

        if path_name.is_absolute() or windows_name.is_absolute():
            raise ValueError("Project name must not be an absolute path.")

        if windows_name.drive:
            raise ValueError("Project name must not be drive-qualified.")

        if len(path_name.parts) != 1 or len(windows_name.parts) != 1:
            raise ValueError("Project name must be one filesystem path segment.")

    @property
    def root(self) -> Path:
        return self.location / self.name
