# ForgePy Project Context

## Project snapshot

- **Name:** ForgePy
- **Purpose:** generate a structured starter Python project from a CLI, then prepare its virtual environment, dependencies, Git repository, and VS Code configuration.
- **Protected stable branch policy:** treat `master` as protected and stable
- **Current stable release/tag:** `v1.0.0`
- **Current development area:** Sprint 12.8, preparing the first PyPI publication.

`config/version.py` is the canonical ForgePy version source and reports `1.0.0`. The `v1.0.0` tag and GitHub stable release exist. PyPI publication under the prepared distribution name `forgepy-cli` is pending.

## ForgePy Philosophy

ForgePy favors understandable automation, explicit architectural boundaries, compatibility-conscious evolution, and generated projects that remain easy for their owners to inspect. See [`ENGINEERING_PRINCIPLES.md`](ENGINEERING_PRINCIPLES.md) for the project-wide design and review policy.

## Implemented capabilities

- Publish release-facing `forgepy-cli` package metadata from `pyproject.toml`, including the README long description, `rzou89/ForgePy` URLs, keywords, a Production/Stable classifier, and the maintainer-selected MIT License through PEP 639 metadata.
- Derive the prepared `1.0.0` distribution version dynamically from the canonical application version source.
- Define repository CI on `windows-latest` and `ubuntu-latest` for CPython 3.12, 3.13, and 3.14, including mandatory Python 3.12 distribution inspection, isolated wheel installation, and installed CLI probes.
- Install the `forgepy-cli` distribution through standards-based setuptools metadata and expose the existing `main:main` CLI flow as the `forgepy` console command. The application remains branded ForgePy.
- Build and publish fresh distributions through `.github/workflows/publish.yml`, with separate build/publish jobs and GitHub OIDC Trusted Publishing bound to `rzou89/ForgePy`, the `pypi` environment, and no stored PyPI credential. The upload remains pending.
- Parse and dispatch `create`, `list`, `version`, and `config` commands through one shared catalog.
- Fall back to an interactive create workflow when no command is supplied.
- Register the `basic`, `library`, and `cli` project templates through one validated registration path with immutable metadata.
- Define immutable component metadata and manifest values, a validated existing-project context, an abstract identity/metadata/manifest/install contract, and an in-memory registry with deterministic built-in registration, explicit registration, lookup, and ordered listing.
- Provide built-in `pytest`, `ruff`, and `github-actions` components that exclusively create their declared standalone files in an explicitly supplied existing project.
- Generate all three built-in file templates through a shared execution layer that keeps registry metadata, project/package context, file mappings, and VS Code entry-point resolution distinct.
- List registered template names and descriptions without invoking project generation.
- Generate a minimal library layout with a normalized import-package directory, `tests/`, empty package initializers, shared README/Git-ignore/pyproject content, and an empty requirements file.
- Generate a minimal command-line package with `__main__.py`, an argparse interface, empty requirements, and executable module, help, version, and editor entry points.
- The `basic` template generates the configured folder layout and nine root files.
- Create `.venv`, upgrade `pip`, `setuptools`, and `wheel`, and install generated requirements.
- Generate four VS Code files matched to the selected template: `basic` targets `app.py`, `library` declares no application entry point, and `cli` targets its generated package `cli.py`.
- After VS Code generation, complete the required Git stage by initializing a repository, staging all generated content, and creating an initial commit; missing Git or any Git failure prevents full-success reporting.
- Load, validate, update, reset, and atomically save user configuration at `~/.forgepy/config.json` through `ConfigStore`.
- Show, set, and reset persistent values through `python main.py config` without duplicating storage logic in the CLI.
- Resolve omitted create location and template values from `default_location` and `default_template`, after explicit CLI arguments and before the existing prompt/`basic` fallback.
- Validate project names as one generated-content-safe, Windows-compatible destination segment so generated projects remain portable across supported Windows and Linux environments; require a new resolved destination directly below the selected location, and reject existing destination files, directories, symlinks, or junctions before generation writes.
- Confine component-state reads, atomic writes, and same-directory temporary files to the resolved project root so `.forgepy` or `components.json` redirection cannot escape the project.
- Test configuration behavior, create-input precedence, destination safety, metadata and registration, all built-in entries, list output, generated structures and execution, and template-aware VS Code output with `unittest`.

The component foundation is exposed by the component CLI but remains independent from configuration, templates, builders, `ProjectGenerator`, and generated-project creation. Its `pytest`, `ruff`, and `github-actions` built-ins exclusively create their declared `pytest.ini`, `ruff.toml`, and `.github/workflows/ci.yml` files inside a validated existing project and reject existing targets. Installation uses the shared orchestrator; registry lookup still does not resolve manifest relationships.

`ConfigCommand` manages all persisted values. `CreateCommand` consumes only `default_location` and `default_template`; `author` and `license` remain unused. `ProjectGenerator` does not depend on `ConfigStore`. Before its established template and tooling stages, it requires a validated one-segment name and a nonexistent direct-child destination, looks up the template, and invokes its side-effect-free preflight before creating the root. `FileTemplate` preflights through the same context construction used for generation, so library and CLI reject unusable normalized package identifiers while basic retains the broader `ProjectConfig` name contract.

The CLI uses three process-status outcomes: successful commands return `0`, handled operational or user failures return `1`, and argparse syntax or usage failures retain status `2`. Command handlers translate only expected boundary failures into concise `[ERROR]` output, the dispatcher propagates their integer status, and `main` exits with it; unexpected programming errors continue to surface.

Every project-generation subprocess has a finite owner-specific timeout: 300 seconds for virtual-environment creation and each packaging-tool upgrade, 900 seconds for requirements installation, 60 seconds for Git initialization, 120 seconds for Git staging, and 60 seconds for the initial commit. Packaging upgrades and dependency installation may require network access. A timeout or non-zero exit identifies its stage, stops the remaining lifecycle, and returns CLI status `1`; the partial destination is retained and may be removed before retrying.

A successful `create` includes successful Git initialization, staging, and initial commit. If the required Git executable is unavailable when the final lifecycle stage is reached, creation returns status `1` without full-success reporting; already-generated project artifacts remain for inspection or removal.

## Repository structure

| Path | Current role |
| --- | --- |
| `.github/workflows/ci.yml` | Repository-only Windows/Linux/CPython matrix and distribution validation. |
| `.github/workflows/publish.yml` | Release-published and manually dispatched PyPI Trusted Publishing with separate build and publish jobs. |
| `CHANGELOG.md` | Release-facing Unreleased changes, prepared `1.0.0` contents, `1.0.0rc1` prerelease history, and the tagged `0.6.0` historical baseline. |
| `builders/` | Folder/file creation and packaging-tool updates. |
| `cli/` | Parser, dispatcher, command contract, and commands. |
| `components/` | Immutable component metadata and manifest, validated project context, minimal installation/state/validation contracts, the `pytest`, `ruff`, and `github-actions` built-ins, and an in-memory registry. |
| `config/` | Version metadata, generated folder defaults, and user-level JSON configuration. |
| `core/` | Project lifecycle and environment, Git, requirements, and VS Code services. |
| `models/` | `ProjectConfig` data model. |
| `templates/` | Basic, library, and CLI definitions; shared context/execution contracts; immutable metadata; template-owned file mappings; template-specific VS Code entry-point rules; registry; rendered content; and VS Code JSON. |
| `utils/` | Present but currently contains no implemented utility behavior. |
| `tests/` | Standard-library tests for component and template metadata/registries, configuration, create resolution, list output, template architecture and output snapshots, built-in structures, and VS Code compatibility. |
| `main.py` | Executable application entry point. |

The root `README.md` is the public installation and usage guide. The root `requirements.txt` remains empty because ForgePy has no third-party runtime dependencies.

## Technical constraints

- ForgePy v1.0 officially supports Windows 10, Windows 11, and Linux on CPython. The supported range is CPython 3.12+ without an upper bound; 3.12, 3.13, and 3.14 are the required v1.0 validation targets. macOS and alternative Python implementations remain unsupported and unverified.
- Full generation uses platform-aware virtual-environment executable paths: `.venv/Scripts/python.exe` on Windows and `.venv/bin/python` on POSIX systems. Generated VS Code configuration follows the same platform-aware rule. Project names intentionally retain Windows-compatible path and reserved-name semantics so generated projects remain portable across supported Windows and Linux environments.
- ForgePy itself has no declared third-party runtime dependencies. Automated coverage includes configuration, create-input resolution, metadata/registry behavior, list output, the shared template contract, exact normalized output snapshots, all built-in structures, generated CLI execution, and isolated template-aware VS Code generation through `ProjectGenerator`. The generated `basic` project requires `PySide6`, `pandas`, and `openpyxl`; `library` and `cli` have empty requirements files. The full lifecycle still upgrades packaging tools and may require network access.
- Template lookup uses direct dictionary indexing and retains `KeyError` for an unknown name, but now occurs after destination validation and before project-root creation so rejection leaves no generation artifact.
- Template metadata versioning has no release policy yet. The `basic` metadata records `0.6.0`, while `library` and `cli` start at `0.1.0`; these are independent from the ForgePy application and generated-project versions.
- Subprocess failures generally propagate because commands use `check=True`.
- Project generation rejects names that are unsafe for current generated Python/TOML strings or the supported Windows filename contract, including leading ASCII spaces and ordinary or superscript-digit reserved device stems, as well as existing targets, before template lookup or root creation. Accepted display names are preserved, while library and CLI package names remain separately normalized and preflighted after lookup but before root creation. Friendly CLI translation remains separate work.
- The root packaging metadata requires CPython `>=3.12` and advertises Python 3.12, 3.13, and 3.14 on Windows and Linux. The repository CI matrix covers both `windows-latest` and `ubuntu-latest`; a full project-creation smoke test has also passed on CachyOS Linux.
- `ComponentRegistry` is in-memory, installation-state-agnostic, and resolution-agnostic; it registers `pytest`, `ruff`, then `github-actions` by default. `ComponentInstaller` coordinates explicit project context, state, direct validation, one hook, and post-success state recording without moving those responsibilities. `component add` delegates to that installer, while `component installed --project PATH` reads the project-local store without registry filtering or filesystem inference. The component system provides no discovery, transitive resolution, installation ordering, rollback, uninstall, local package installation, template association, or generation integration.
- `config.default_structure.DEFAULT_FILES` is defined but unused. `BasicFiles`, `LibraryFiles`, and `CliFiles` own their complete mappings and call `TemplateManager` directly for rendered content; `TemplateFiles.basic()` remains a compatibility facade.

## Near-term priorities

- Keep the Sprint 10.0 GitHub Actions component within the existing catalog and CLI flows without adding rollback or resolution.
- Keep further templates beyond `basic`, `library`, and `cli` subject to separate approval and compatibility review.
- Keep persisted `author` and `license` values, and the configuration store itself, out of core generation and templates until a separate requirement explicitly defines that integration.
- Continue expanding automated coverage across supported commands, lifecycle stages, and failure handling.
- Keep the passing repository workflow green on both `windows-latest` and `ubuntu-latest` with CPython 3.12, 3.13, and 3.14. Every job runs the full unit suite, `compileall`, and packaging/support tests; Python 3.12 also validates the built artifacts and installed CLI. GitHub runner success does not literally prove every Windows edition or Linux distribution, so native-platform smoke validation may remain a release-stage manual check.
- Keep the root MIT License, SPDX package metadata, and distributed license file aligned.
- Review and merge the PyPI preparation, create/protect the GitHub `pypi` environment, then deliberately dispatch `publish.yml` from `master` for the first upload.

## Long-term v1.0 direction

The repository does not define guaranteed v1.0 features. A realistic direction is a stable, documented CLI and template contract; predictable project-generation behavior; consistent versioning; and automated verification of the existing lifecycle. New templates and commands require separate approval.

## Project Resume

Use this section as the handoff point for a new developer or AI session.

| Item | Resume state |
| --- | --- |
| Stable baseline | `v1.0.0` Git tag and GitHub Release |
| Current branch policy | Repository policy treats `master` as protected; use a feature branch for implementation |
| Active development area | Sprint 12.8 first-PyPI-publication preparation |
| Implemented CLI | `create`, `list`, `version`, `config show/set/reset`, `component list/installed/add`, plus no-command interactive create |
| Implemented templates | `basic`, `library`, and `cli`, all with descriptive metadata |
| Component state | Registry with `pytest`, `ruff`, and `github-actions` built-ins, project-local installed names, direct validation, and shared library/CLI orchestration; no generation integration |
| Distribution identity | PyPI name `forgepy-cli`; application ForgePy; console command `forgepy` |
| Version source | `config/version.py`, currently `1.0.0`; final `v1.0.0` tag and GitHub Release exist |
| Publishing state | Pending publisher expects `rzou89/ForgePy`, `publish.yml`, environment `pypi`; no PyPI upload has occurred |

To resume work:

1. Read `AGENTS.md`, this file, `ENGINEERING_PRINCIPLES.md`, `ROADMAP.md`, and `ARCHITECTURE.md`.
2. Run `git status --short`; inspect recent history and tags; preserve all uncommitted work.
3. Re-read the source modules involved in the requested change rather than relying only on this summary.
4. Confirm whether version metadata or other known limitations changed since this document was written.
5. Create a feature branch from `master` for implementation work.
6. Keep the change focused, preserve current CLI compatibility, and satisfy the Definition of Done before review.

Safe read-only resume commands:

```powershell
git status --short --branch
git log -5 --oneline --decorate
git tag --list
python main.py --help
python main.py version
python main.py list
python main.py config --help
```
