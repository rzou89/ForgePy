# ForgePy

ForgePy is a cross-platform Python project generator for Windows and Linux. It creates structured Python projects and prepares their development tooling automatically.

ForgePy supports two ways to create projects:

* **Easy Mode** — an interactive project wizard for users who want a guided experience.
* **Advanced Mode** — command-line arguments for scripting, automation, and experienced users.

## What ForgePy Does

ForgePy can:

* generate a project from a registered template;
* create a Python virtual environment;
* update `pip`, `setuptools`, and `wheel`;
* install generated project requirements;
* create VS Code configuration;
* initialize a Git repository;
* create the initial Git commit;
* add optional project components such as pytest, Ruff, and GitHub Actions configuration.

A successful project creation leaves the new project ready for development.

## Requirements

* Windows 10 or Windows 11, or Linux
* CPython 3.12 or newer
* Git
* Git user name and email configured for the initial commit

ForgePy v1.0 officially supports Windows and Linux on CPython.

macOS and alternative Python implementations remain unsupported and unverified.

Repository CI tests ForgePy on GitHub-hosted `windows-latest` and `ubuntu-latest` runners using CPython 3.12, 3.13, and 3.14.

A full project-creation smoke test has also been completed successfully on CachyOS Linux.

Hosted runner coverage does not literally test every Windows edition or Linux distribution.

Packaging-tool updates and dependency installation may require network access during project creation.

## Installation

ForgePy is prepared for PyPI publication under the distribution name:

```text
forgepy-cli
```

After the first PyPI publication, installation will be:

```bash
python -m pip install forgepy-cli
```

The first PyPI upload is still pending.

Until publication is completed, install ForgePy from a source checkout:

```bash
python -m pip install .
```

For editable development work:

```bash
python -m pip install -e .
```

The installed command is:

```text
forgepy
```

The application itself remains named **ForgePy**.

## Quick Start

### Easy Mode — Interactive Project Wizard

Easy Mode is intended for users who want ForgePy to guide them through project creation.

If ForgePy is installed, run:

```bash
forgepy
```

From the ForgePy source repository, run:

```bash
python main.py
```

Running `main.py` from the VS Code **Run ▶** button also starts Easy Mode because no CLI command is supplied.

The interactive flow is:

```text
Run ▶
  ↓
Project Name
  ↓
Project Location
  ↓
Choose Template
  ↓
Confirmation
  ↓
Create Project
```

ForgePy displays the registered project templates:

```text
==================================================
              FORGEPY PROJECT WIZARD
==================================================

What do you want to create?

[1] General Application
    Template: basic

[2] CLI / Automation / Backend Tool
    Template: cli

[3] Python Library
    Template: library

[0] Cancel
```

After selecting a template, ForgePy displays a project summary before creating anything:

```text
Project Summary
----------------------------------------
Name     : MyProject
Location : /path/to/projects
Template : CLI / Automation / Backend Tool
Folder   : /path/to/projects/MyProject

Create this project? [Y/n]:
```

Selecting `0` or answering `n` at confirmation cancels project creation without intentionally starting the generation lifecycle.

If `default_location` is configured, ForgePy may use that location instead of prompting for one.

Template selection in Easy Mode is always presented through the interactive template menu.

### Advanced Mode — CLI Arguments

Advanced Mode allows project creation directly through CLI arguments.

Windows PowerShell:

```powershell
forgepy create MyProject `
    --location C:\Projects `
    --template cli
```

Linux:

```bash
forgepy create MyProject \
    --location ~/Projects \
    --template cli
```

The same command can be executed directly from the source repository:

```bash
python main.py create MyProject \
    --location ~/Projects \
    --template cli
```

When `--template` is explicitly supplied, ForgePy uses that template directly and does not display the interactive template-selection menu.

In Advanced Mode:

* an omitted project name starts the project-name prompt;
* an omitted location uses `default_location` when configured, otherwise ForgePy prompts for one;
* an omitted template uses `default_template` when configured, otherwise ForgePy falls back to `basic`.

The destination project directory must not already exist.

## Available Templates

ForgePy currently includes three registered project templates.

### `basic` — General Application

Designed for general Python applications.

Suitable for:

* desktop applications;
* GUI applications;
* data processing;
* Excel and reporting tools;
* general business applications.

The generated project includes a structured application directory layout, `app.py`, environment files, project metadata, and generated requirements.

### `cli` — CLI / Automation / Backend Tool

Designed for lightweight command-line and automation projects.

Suitable for:

* automation;
* trading bots;
* scanners;
* backend services;
* scheduled jobs;
* API clients.

The generated project includes a normalized Python package, `__main__.py`, an argparse-based CLI, help and version behavior, and a `tests` package.

### `library` — Python Library

Designed for reusable Python packages.

Suitable for:

* reusable Python packages;
* SDKs;
* internal libraries;
* modules used by other projects.

The generated project includes a normalized import-package directory and a `tests` package.

List the registered templates at any time with:

```bash
forgepy list
```

## Components

Components add focused configuration files to an explicitly supplied existing project directory.

ForgePy records successful component installations in project-local state.

Available components are:

* `pytest` — adds `pytest.ini`;
* `ruff` — adds `ruff.toml`;
* `github-actions` — adds a minimal `.github/workflows/ci.yml` for the generated project.

Example commands:

```bash
forgepy component list
forgepy component add pytest --project .
forgepy component installed --project .
```

Component installation refuses an owned target that already exists.

The generated-project `github-actions` component is separate from ForgePy's own repository CI workflow.

## Configuration

ForgePy stores user configuration under:

```text
~/.forgepy/config.json
```

Supported settings are:

* `default_template`
* `default_location`
* `author`
* `license`

Configuration commands:

```bash
forgepy config show
forgepy config set default_template library
forgepy config set default_location <projects-directory>
forgepy config reset
```

Currently:

* `default_location` affects project creation when no explicit location is supplied;
* `default_template` is used by Advanced Mode when `--template` is omitted;
* Easy Mode presents the interactive template menu instead of silently applying `default_template`;
* `author` and `license` are persisted but are not currently applied to generated files.

Explicit Advanced Mode `create` options take priority over stored configuration.

See all supported syntax with:

```bash
forgepy create --help
forgepy config --help
```

## Project Creation Lifecycle

After the project inputs are resolved and confirmed, ForgePy runs the project-creation lifecycle.

A successful creation performs these stages in order:

1. Generate the selected template.
2. Create `.venv`.
3. Update `pip`, `setuptools`, and `wheel`.
4. Install the generated `requirements.txt`.
5. Write VS Code configuration.
6. Run `git init`.
7. Run `git add .`.
8. Create the initial Git commit.
9. Report full success.

Git is a required part of successful project creation.

## Failure and Partial Projects

ForgePy project creation is not transactional or atomic.

If creation fails after ForgePy has created the destination directory, later lifecycle stages stop and full success is not reported.

Files generated by earlier stages may remain in the destination.

Inspect the destination and remove the partial project when appropriate before retrying.

## Development

Run the standard local validation from the repository root:

```bash
python -m unittest discover -s tests -v

python -m compileall -q \
    components \
    cli \
    templates \
    core \
    config \
    builders \
    models \
    tests
```

Repository CI runs the test suite, compilation checks, and packaging/support tests on:

* `windows-latest`
* `ubuntu-latest`

using:

* CPython 3.12
* CPython 3.13
* CPython 3.14

The Python 3.12 CI jobs also build and inspect the wheel and source distribution, install the wheel in isolation, and exercise the installed CLI.

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository workflow and review expectations.

## Current Status

ForgePy v1.0.0 is the current stable Git tag and GitHub Release.

The naming is:

```text
Application : ForgePy
CLI command : forgepy
Distribution: forgepy-cli
```

Trusted Publishing is configured in the repository, but the first PyPI upload has not yet occurred.

## License

ForgePy is licensed under the [MIT License](LICENSE).
