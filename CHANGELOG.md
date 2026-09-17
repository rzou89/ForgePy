# Changelog

This changelog records release-facing changes without assigning versions or dates that do not exist in repository history.

## Unreleased

No unreleased changes yet.

## 1.1.0

### Added

- Added Linux project-generation support alongside Windows, including
  platform-aware virtual-environment interpreter paths and generated VS Code
  configuration.
- Expanded repository CI to validate `windows-latest` and `ubuntu-latest` on
  CPython 3.12, 3.13, and 3.14; a full project-creation smoke test also passed
  on CachyOS Linux.
- Added Easy Mode for no-command startup, guiding users through project name,
  location, registered template selection, confirmation, and creation.
- Added user-facing template `display_name` and `use_cases` metadata for the
  built-in `basic`, `cli`, and `library` templates.

### Changed

- Kept explicit `create` usage as Advanced Mode. An explicit `--template`
  bypasses the interactive template menu, while an omitted template retains
  the existing configured-default and `basic` fallback behavior.
- Published ForgePy 1.0.0 to PyPI under the `forgepy-cli` distribution through
  Trusted Publishing, establishing the public package distribution channel.
- Updated current project URLs for `rzou89/ForgePy` and retained GitHub OIDC
  Trusted Publishing for release publication.
- Updated current project documentation to distinguish Easy Mode from Advanced
  Mode and describe the post-v1.0 Windows/Linux support contract.

## 1.0.0

ForgePy 1.0.0 promotes the validated `1.0.0rc1` contents as the stable release
without additional product changes. The `v1.0.0` tag and GitHub Release exist.
The same 1.0.0 distribution was subsequently published to PyPI.

## 1.0.0rc1

This is the first ForgePy v1.0 release candidate, not the final v1.0.0
release. It was not published to PyPI.

### Added

- Added the `library` and `cli` templates alongside the existing `basic` starter.
- Added project-local components for pytest, Ruff, and GitHub Actions, with explicit listing, installation, and installed-state commands.
- Added persistent user configuration for default template and location selection.
- Added standards-based setuptools packaging and the installed `forgepy` console command.
- Added a public getting-started README and repository CI for CPython 3.12, 3.13, and 3.14 on GitHub-hosted Windows runners.
- Added the maintainer-selected MIT License and corresponding package metadata.

### Changed

- Defined Windows 10 and Windows 11 on CPython 3.12+ as the intended v1.0 support contract.
- Made Git initialization, staging, and the initial commit required for full project-creation success.
- Ordered VS Code generation before Git so editor configuration is included in the initial commit.
- Added finite timeouts and consistent operational failure reporting for external lifecycle commands.

### Fixed

- Hardened project-name, destination, symlink, junction, and component-state confinement checks.
- Added package-name preflight so unusable library and CLI package identifiers fail before destination creation.
- Stabilized CLI exit codes and handled-error output while preserving unexpected programming failures.
- Made Windows tests compare equivalent resolved paths without weakening destination or state-safety assertions.

## 0.6.0

The repository tag `v0.6.0` marks this Sprint 6 baseline. Its tagged `config/version.py` still reported `0.4.0`, which is a historical metadata mismatch.

- Established the tagged Sprint 6 baseline with the modular project generator, `basic` template, virtual-environment and requirements setup, VS Code configuration, and Git repository setup.
