"""Declarative installation properties for ForgePy components."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ComponentManifest:
    """Describe files and component relationships without resolving them."""

    files: tuple[Path, ...] = ()
    dependencies: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        files = self._normalize_files(self.files)
        dependencies = self._normalize_names(
            self.dependencies,
            "dependencies",
        )
        conflicts = self._normalize_names(self.conflicts, "conflicts")

        object.__setattr__(self, "files", files)
        object.__setattr__(self, "dependencies", dependencies)
        object.__setattr__(self, "conflicts", conflicts)

    @staticmethod
    def _normalize_files(files: Iterable[Path]) -> tuple[Path, ...]:
        if isinstance(files, (str, bytes)):
            raise TypeError(
                "Component manifest files must be an iterable of Paths."
            )

        try:
            normalized = tuple(files)
        except TypeError as error:
            raise TypeError(
                "Component manifest files must be an iterable of Paths."
            ) from error

        for path in normalized:
            if not isinstance(path, Path):
                raise TypeError(
                    "Component manifest files must contain only Paths."
                )
            if path == Path() or not str(path).strip():
                raise ValueError(
                    "Component manifest file paths must not be empty."
                )
            if path.is_absolute():
                raise ValueError(
                    "Component manifest file paths must be project-relative."
                )
            if ".." in path.parts:
                raise ValueError(
                    "Component manifest file paths must not contain '..'."
                )

        ComponentManifest._reject_duplicates(normalized, "files")
        return normalized

    @staticmethod
    def _normalize_names(
        names: Iterable[str],
        field_name: str,
    ) -> tuple[str, ...]:
        if isinstance(names, (str, bytes)):
            raise TypeError(
                f"Component manifest {field_name} must be an iterable "
                "of strings."
            )

        try:
            normalized = tuple(names)
        except TypeError as error:
            raise TypeError(
                f"Component manifest {field_name} must be an iterable "
                "of strings."
            ) from error

        for name in normalized:
            if not isinstance(name, str):
                raise TypeError(
                    f"Component manifest {field_name} must contain only "
                    "strings."
                )
            if not name.strip():
                raise ValueError(
                    f"Component manifest {field_name} entries must not be "
                    "empty."
                )

        ComponentManifest._reject_duplicates(normalized, field_name)
        return normalized

    @staticmethod
    def _reject_duplicates(values: tuple[object, ...], field_name: str) -> None:
        if len(values) != len(set(values)):
            raise ValueError(
                f"Component manifest {field_name} must not contain duplicates."
            )
