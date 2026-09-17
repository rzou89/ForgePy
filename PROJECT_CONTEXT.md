# ForgePy Project Context

## Project snapshot

* **Name:** ForgePy
* **Purpose:** generate structured Python projects through either a guided interactive wizard or explicit CLI arguments, then prepare their virtual environment, dependencies, VS Code configuration, and Git repository.
* **Supported platforms:** Windows and Linux on CPython.
* **Protected stable branch policy:** treat `master` as protected and stable.
* **Current stable release/tag:** `v1.1.0`.
* **Current development area:** post-v1.1.0 maintenance and incremental development.

`config/version.py` is the canonical ForgePy version source and currently reports `1.1.0`.

The `v1.1.0` tag and GitHub stable release exist.

ForgePy 1.1.0 is published to PyPI under the distribution name `forgepy-cli`. The application remains branded **ForgePy**, and the installed console command remains `forgepy`.

## ForgePy Philosophy

ForgePy favors understandable automation, explicit architectural boundaries, compatibility-conscious evolution, and generated projects that remain easy for their owners to inspect.

See [`ENGINEERING_PRINCIPLES.md`](ENGINEERING_PRINCIPLES.md) for the project-wide design and review policy.

## User interaction modes

ForgePy supports two project-creation workflows.

### Easy Mode

Easy Mode is the no-command workflow:

```text
forgepy
```

or, from the source repository:

```text
python main.py
```

Using the VS Code **Run ▶** button on `main.py` also enters this mode because no CLI command is supplied.

The flow is:

```text
Project Name
    ↓
Project Location
    ↓
Interactive Template Selection
    ↓
Confirmation
    ↓
Project Creation Lifecycle
```

If no project name is supplied, ForgePy prompts for one.

If no location is supplied, ForgePy first resolves `default_location`. If no usable configured location exists, it prompts for one.

Template selection is always presented interactively in Easy Mode when no template value is already present.

The wizard reads its available templates from `TemplateRegistry` metadata instead of maintaining a separate hard-coded template catalog.

The current menu exposes:

* `basic` — **General Application**
* `cli` — **CLI / Automation / Backend Tool**
* `library` — **Python Library**

The wizard also displays template use cases from the registered metadata.

Selection `0` cancels before generation.

After a valid template is selected, ForgePy displays a project summary containing the name, location, friendly template name, and destination folder.

Confirmation accepts `Y`, `y`, `yes`, or an empty response as approval.

`n` or `no` cancels before `ProjectGenerator` is invoked.

Invalid template selections and invalid confirmation responses are rejected and prompted again.

### Advanced Mode

Advanced Mode uses the explicit `create` command:

```text
forgepy create PROJECT_NAME --location PATH --template NAME
```

or:

```text
python main.py create PROJECT_NAME --location PATH --template NAME
```

Explicit CLI values take priority over persisted configuration.

In Advanced Mode:

* an omitted project name starts the project-name prompt;
* an omitted location uses `default_location`, then prompts if necessary;
* an omitted template uses `default_template`, then falls back to `basic`;
* an explicitly supplied `--template` is used directly and never opens the interactive template-selection menu.

This separation preserves the existing automation-friendly CLI while allowing the no-command workflow to remain approachable for general users.

## Implemented capabilities

* Publish release-facing `forgepy-cli` package metadata from `pyproject.toml`, including README long description, `rzou89/ForgePy` URLs, keywords, Production/Stable classification, and MIT License metadata.
* Derive distribution version `1.1.0` dynamically from the canonical application version source.
* Expose `main:main` as the installed `forgepy` console command.
* Define repository CI on `windows-latest` and `ubuntu-latest` for CPython 3.12, 3.13, and 3.14.
* Build and inspect distributions in CI, install the wheel in isolation, and probe the installed CLI.
* Provide `.github/workflows/publish.yml` for GitHub OIDC Trusted Publishing through the `pypi` environment without storing a PyPI credential.
* Parse and dispatch `create`, `list`, `version`, `config`, and `component` command flows through shared CLI infrastructure.
* Enter interactive project creation automatically when no command is supplied.
* Present registered templates through the interactive template-selection wizard.
* Display a project summary and require confirmation before Easy Mode begins generation.
* Support clean cancellation before project generation.
* Register the `basic`, `library`, and `cli` project templates through one validated registry path.
* Expose immutable template metadata including:

  * internal template name;
  * description;
  * template version;
  * author;
  * tags;
  * optional user-facing `display_name`;
  * user-facing `use_cases`.
* Use the template registry as the source of truth for interactive template discovery.
* Generate all three built-in file templates through a shared execution layer that keeps registry metadata, project/package context, file mappings, and VS Code entry-point resolution distinct.
* List registered template names and descriptions without invoking project generation.
* Generate a `basic` application project with the configured structured directory layout and root files.
* Generate a minimal reusable `library` package with a normalized import-package directory, `tests/`, package initializers, shared project files, and empty requirements.
* Generate a minimal `cli` package with `__main__.py`, an argparse interface, executable module behavior, help/version support, tests, and a VS Code entry point.
* Create `.venv`.
* Upgrade `pip`, `setuptools`, and `wheel`.
* Install generated project requirements.
* Generate template-aware VS Code configuration.
* Initialize the generated project as a Git repository.
* Stage generated content and create an initial Git commit.
* Treat Git failure as a failed project-creation lifecycle rather than reporting full success.
* Load, validate, update, reset, and atomically save user configuration at `~/.forgepy/config.json`.
* Persist `default_location`, `default_template`, `author`, and `license`.
* Keep `author` and `license` persisted but currently unused by generation.
* Validate project names as one generated-content-safe, Windows-compatible destination segment so accepted projects remain portable across supported Windows and Linux environments.
* Reject an existing destination file, directory, symlink, or junction before generation writes.
* Run template preflight before creating the project root.
* Provide built-in `pytest`, `ruff`, and `github-actions` components for explicitly supplied existing projects.
* Record component installation state locally inside the target project.
* Confine component-state operations to the resolved project root.

## Configuration behavior

`ConfigCommand` owns persisted configuration behavior.

`ProjectGenerator` does not depend on `ConfigStore`.

`CreateCommand` is responsible for translating user input and stored configuration into resolved project-generation arguments.

Current configuration behavior is:

* `default_location` is used when no explicit location is supplied;
* in Easy Mode, template choice is presented through the interactive wizard;
* in Advanced Mode, an omitted template uses `default_template`, then `basic`;
* explicit Advanced Mode CLI options override stored values;
* `author` and `license` remain persisted but are not applied to generated files.

This separation keeps user-level configuration concerns outside the core project-generation lifecycle.

## Project generation lifecycle

Before generation begins, ForgePy requires:

* a valid project name;
* a valid parent location;
* a nonexistent direct-child destination;
* a registered template;
* successful template preflight.

After those checks, the successful lifecycle is:

1. Generate the selected template.
2. Create `.venv`.
3. Update `pip`.
4. Update `setuptools`.
5. Update `wheel`.
6. Install generated requirements.
7. Generate VS Code configuration.
8. Initialize Git.
9. Stage generated content.
10. Create the initial Git commit.
11. Report full project-creation success.

`FileTemplate` preflights through the same context-construction path used during generation.

This allows `library` and `cli` to reject unusable normalized package identifiers before writing project files, while `basic` retains the broader `ProjectConfig` naming contract.

## Failure behavior

The CLI uses three process-status outcomes:

* `0` — successful command or deliberate interactive cancellation;
* `1` — handled operational or user-facing failure;
* `2` — argparse syntax or usage failure.

Expected boundary failures are translated into concise `[ERROR]` output.

Unexpected programming errors continue to surface rather than being silently converted into generic failures.

Project generation is not transactional.

If a lifecycle stage fails after the destination has been created, earlier generated files may remain for inspection or manual removal.

ForgePy does not automatically roll back a partial project.

## Subprocess boundaries

Every project-generation subprocess has a finite stage-specific timeout.

Current ownership includes:

* virtual-environment creation — 300 seconds;
* each packaging-tool update — 300 seconds;
* requirements installation — 900 seconds;
* Git initialization — 60 seconds;
* Git staging — 120 seconds;
* initial Git commit — 60 seconds.

Packaging-tool updates and dependency installation may require network access.

A timeout or non-zero subprocess exit stops the remaining lifecycle and prevents full-success reporting.

## Repository structure

| Path                            | Current role                                                                                                                                                         |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.github/workflows/ci.yml`      | Repository-only Windows/Linux/CPython test and distribution validation.                                                                                              |
| `.github/workflows/publish.yml` | PyPI Trusted Publishing workflow with separate build and publish jobs.                                                                                               |
| `builders/`                     | Folder/file creation and packaging-tool updates.                                                                                                                     |
| `cli/`                          | Parser, dispatcher, command contract, command implementations, and interactive create behavior.                                                                      |
| `components/`                   | Component metadata, manifests, project context, validation, state, registry, installation orchestration, and built-ins.                                              |
| `config/`                       | Application version, generated folder defaults, and user-level JSON configuration.                                                                                   |
| `core/`                         | Project lifecycle plus environment, requirements, VS Code, and Git services.                                                                                         |
| `models/`                       | `ProjectConfig` data model.                                                                                                                                          |
| `templates/`                    | Basic, library, and CLI templates; metadata; registry; context/execution contracts; file mappings; rendered content; and VS Code template content.                   |
| `tests/`                        | Standard-library unit and integration-style tests for CLI, templates, configuration, components, lifecycle, platform compatibility, packaging, and failure behavior. |
| `main.py`                       | Executable application entry point.                                                                                                                                  |

The root `README.md` is the public installation and usage guide.

The root `requirements.txt` remains empty because ForgePy itself has no third-party runtime dependencies.

## Technical constraints

* ForgePy officially supports Windows 10, Windows 11, and Linux on CPython.
* The supported Python range is CPython 3.12+ without an upper bound.
* CPython 3.12, 3.13, and 3.14 are the required current repository CI validation targets.
* macOS and alternative Python implementations remain unsupported and unverified.
* Full generation uses platform-aware virtual-environment executable paths:

  * `.venv/Scripts/python.exe` on Windows;
  * `.venv/bin/python` on POSIX systems.
* Generated VS Code configuration follows the same platform-aware interpreter rule.
* Project names retain Windows-compatible path and reserved-name semantics so generated projects remain portable across supported Windows and Linux environments.
* ForgePy itself has no declared third-party runtime dependencies.
* The generated `basic` project requires `PySide6`, `pandas`, and `openpyxl`.
* Generated `library` and `cli` requirements files are empty.
* Template lookup uses registry dictionary lookup and preserves `KeyError` internally for unknown names.
* Template lookup occurs before project-root creation.
* Template metadata version numbers are independent from the ForgePy application version.
* `basic` template metadata currently records version `0.6.0`.
* `library` and `cli` template metadata currently record version `0.1.0`.
* Component discovery, transitive resolution, installation ordering, rollback, uninstall, local package installation, template association, and generation integration are not currently implemented.
* `config.default_structure.DEFAULT_FILES` remains defined but unused.
* `BasicFiles`, `LibraryFiles`, and `CliFiles` own their complete generated-file mappings.
* `TemplateFiles.basic()` remains a compatibility facade.

## Automated validation

Current automated coverage includes:

* configuration behavior;
* Easy Mode and Advanced Mode create-input behavior;
* interactive template selection;
* `basic`, `cli`, and `library` selection;
* invalid interactive selection retry;
* interactive cancellation;
* confirmation approval and rejection;
* preservation of explicit `--template` behavior;
* template metadata and registration;
* template-friendly names and use cases;
* component metadata and registration;
* destination safety;
* generated project structures;
* generated CLI execution;
* template-aware VS Code configuration;
* lifecycle ordering;
* subprocess timeouts;
* packaging and installed CLI behavior;
* Windows/Linux compatibility contracts.

Repository CI runs on:

* `windows-latest`;
* `ubuntu-latest`;

with:

* CPython 3.12;
* CPython 3.13;
* CPython 3.14.

A full project-creation smoke test has also completed successfully on CachyOS Linux.

Hosted runner coverage does not literally validate every Windows edition or Linux distribution.

## Near-term priorities

* Keep documentation aligned with the actual Easy Mode and Advanced Mode behavior.
* Keep further templates beyond `basic`, `library`, and `cli` subject to separate approval and compatibility review.
* Keep persisted `author` and `license` values outside core generation until a separate requirement explicitly defines their integration.
* Continue expanding automated coverage for supported commands, lifecycle stages, and failure handling.
* Keep repository CI green on Windows and Linux across the supported CPython matrix.
* Keep the root MIT License, SPDX package metadata, and distributed license file aligned.
* Keep release tags, GitHub Releases, PyPI publication state, package metadata, and documentation synchronized.

## Post-v1.0 direction

ForgePy v1.0.0 is already released.

Post-v1.0 development should favor incremental, compatibility-conscious improvements rather than broad architectural expansion.

Current direction includes:

* maintaining a stable and documented CLI contract;
* keeping Easy Mode approachable for non-programmers;
* preserving automation-friendly Advanced Mode behavior;
* improving project-generation usability and failure handling;
* keeping template metadata and documentation synchronized;
* maintaining predictable lifecycle behavior;
* keeping Windows and Linux support validated;
* introducing new templates or commands only through focused, separately reviewed changes.

## Project Resume

Use this section as the handoff point for a new developer or AI session.

| Item                          | Resume state                                                                                                    |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Stable baseline               | `v1.1.0` Git tag and GitHub Release                                                                             |
| Current branch policy         | Treat `master` as protected; use a focused branch for changes                                                   |
| Current maintenance area      | Post-v1.1.0 maintenance and incremental development                                                             |
| Implemented interaction modes | Easy Mode interactive wizard and Advanced Mode CLI                                                              |
| Implemented CLI               | `create`, `list`, `version`, `config show/set/reset`, `component list/installed/add`, plus no-command Easy Mode |
| Implemented templates         | `basic`, `library`, and `cli`                                                                                   |
| Template UX metadata          | `display_name`, `description`, and `use_cases` are available through registered metadata                        |
| Component state               | `pytest`, `ruff`, and `github-actions` built-ins with project-local installation state                          |
| Distribution identity         | PyPI name `forgepy-cli`; application ForgePy; console command `forgepy`                                         |
| Version source                | `config/version.py`, currently `1.1.0`                                                                          |
| Publishing state              | `forgepy-cli` 1.1.0 is published on PyPI                                                                        |

To resume work:

1. Read `AGENTS.md`, this file, `ENGINEERING_PRINCIPLES.md`, `ROADMAP.md`, and `ARCHITECTURE.md`.
2. Run `git status --short --branch`.
3. Inspect recent history and tags.
4. Preserve any uncommitted work.
5. Re-read the source modules involved in the requested change rather than relying only on summaries.
6. Confirm whether release, publishing, or known limitations have changed since this document was written.
7. Create a focused branch from `master` for implementation work.
8. Preserve CLI compatibility and satisfy the project Definition of Done before review.

Safe read-only resume commands:

```bash
git status --short --branch
git log -5 --oneline --decorate
git tag --list
python main.py --help
python main.py version
python main.py list
python main.py config --help
```
