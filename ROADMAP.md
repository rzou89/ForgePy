# ForgePy Roadmap

This roadmap separates shipped work, active development, planned stabilization, and uncommitted ideas. It defines no guaranteed dates or features.

## Status Model

| Status | Meaning |
| --- | --- |
| Implemented | Confirmed by code and repository history. |
| In progress | Present after the stable tag and identified as the current development area. |
| Planned | A high-level readiness outcome inferred from documented gaps; scope still requires approval. |
| Idea | Exploratory only; not approved or scheduled. |

## Implemented — Stable Baseline Through v1.0.0

The latest stable tag is `v1.0.0`; the v0.6.0 Sprint 6 baseline remains part of
the repository's historical milestone evidence.

### Milestone Evidence

| Repository point | Evidence |
| --- | --- |
| Modular generator foundation | Commit `0697387` has the subject `v0.2.5 - Modular project generator with template system`; `v0.2.5` is not present as a Git tag. |
| Stable Sprint 6 baseline | Tag `v0.6.0` points to commit `78c9924`, `Sprint 6 Stable`. |
| Stable v1.0 release | Tag `v1.0.0` points to merge commit `0257417`; the GitHub stable Release exists. |

| Milestone | Confirmed outcome |
| --- | --- |
| Project-generation foundation | `ProjectConfig` and `ProjectGenerator` create and coordinate a starter project. |
| Builder separation | Folder, file, and packaging-tool operations have focused builders. |
| Template system | `BaseTemplate`, `TemplateRegistry`, `TemplateFiles`, and the `basic` template are implemented. |
| Environment tooling | ForgePy creates `.venv`, upgrades packaging tools, and installs non-empty generated requirements. |
| Repository setup | ForgePy initializes Git, stages content, and attempts an initial commit. |
| Editor setup | ForgePy generates VS Code settings, launch, tasks, and extension recommendations. |

## Implemented — Sprint 7 CLI and User Configuration

The Sprint 7 CLI architecture, persistent configuration, its CLI command, and configuration-backed create defaults are present on `master` in commits after `v0.6.0`. No newer release tag exists.

| Area | Current implementation |
| --- | --- |
| Command model | Shared `Command` contract and one explicit command catalog used by parsing and dispatch. |
| Commands | `create`, `list`, `version`, and `config` with `show`, `set`, and `reset` actions. |
| Invocation | Creation resolves explicit arguments, persisted location/template defaults, and existing prompt/`basic` fallbacks in that order. |
| Compatibility | No subcommand continues to open the create workflow. |
| Version reporting | `config/version.py` is the canonical source and matches the `v0.6.0` release tag. |
| User configuration | `ConfigCommand` manages all four settings; `CreateCommand` consumes only `default_location` and `default_template`, while `author` and `license` remain unused. |

Sprint 7 behavior is covered by focused configuration and create-resolution tests; this document does not assign an unrecorded release number.

## Implemented — Sprint 8.1 Template Metadata

Sprint 8.1 introduced descriptive metadata as the registry and listing foundation for future templates. Commit `484278a` records the implementation, and merge commit `41de327` incorporates it into `master`; no newer release tag was created.

| Area | Sprint 8.1 outcome |
| --- | --- |
| Metadata model | Immutable `TemplateMetadata` values contain name, description, template version, author, and tags. |
| Registration | `TemplateRegistry.register()` validates template and metadata types, non-empty matching names, and uniqueness before preserving a registration. |
| Listing | `list` reads registry metadata and displays each template name and description. |
| Compatibility | That milestone added no template: `basic` remained the only template, its selector stayed stable, and its generated output was unchanged. |

Sprint 8.1 includes focused metadata, registry, and list-output tests plus the existing CLI regression suite.

## Implemented — Sprint 8.2 Library Template

Sprint 8.2 added the first additional built-in template without changing the shared generator lifecycle. Merge commit `72b8359` incorporates the work into `master`; no newer release tag was created.

| Area | Sprint 8.2 outcome |
| --- | --- |
| Built-in catalog | `TemplateRegistry` registers `basic` first and `library` second through the existing validated API. |
| Library metadata | `library` has its own name, description, template revision, author, and tags. |
| Generated layout | A normalized import-package directory and `tests/` each contain `__init__.py`, alongside a minimal set of shared root files. |
| Editor compatibility | Built-in templates explicitly declare an `app.py` entry point or no entry point; library VS Code JSON no longer references an absent application file. |
| Compatibility | The `basic` selector, metadata, generated folders/files, default selection, and existing VS Code behavior remain unchanged. |
| Verification | Focused tests cover registration, metadata, exact structures, package-name normalization, generator selection, and template-aware VS Code output. |

Sprint 8.2 introduced no further template types, release number, or delivery date.

## Implemented — Sprint 8.3 CLI Template

Sprint 8.3 added a minimal standard-library command-line application template on the existing registry and editor-configuration contracts. Merge commit `f9ae27c` incorporates the work into `master`; no newer release tag was created.

| Area | Sprint 8.3 outcome |
| --- | --- |
| Built-in catalog | `TemplateRegistry` registers `cli` after the established `basic` and `library` templates. |
| CLI metadata | `cli` has a factual description, independent template revision, author, and Python/CLI/argparse tags. |
| Generated layout | A normalized package contains `__init__.py`, `__main__.py`, and `cli.py`; `tests/` has an initializer and shared root files remain minimal. |
| Runtime behavior | The generated package runs with `python -m`, and argparse provides help and version output without third-party dependencies. |
| Editor compatibility | The template publishes its generated `cli.py` path so VS Code launch and run tasks reference a real executable file. |
| Compatibility | The existing templates, default selection, CLI/configuration architecture, builders, and generator lifecycle remain unchanged. |
| Verification | Focused tests cover registration, metadata, exact output, normalization, subprocess execution, editor JSON, and existing-template regressions. |

Sprint 8.3 introduced no additional ForgePy command, release number, or delivery date.

## Implemented — Sprint 8.4 Template Architecture

Sprint 8.4 separated the implemented templates' metadata, generation context, file mappings, and context-aware VS Code entry-point resolution without adding another template or changing generated output. Merge commit `409f28b` incorporates the work into `master`; no newer release tag was created.

| Area | Sprint 8.4 outcome |
| --- | --- |
| Shared execution | `FileTemplate` owns the repeated folder creation, ordered file-writing loop, and post-write VS Code entry-point resolution for all three built-ins. |
| Generation data | Immutable `TemplateContext` keeps project and optional normalized package data separate from registry metadata. |
| File ownership | `BasicFiles`, `LibraryFiles`, and `CliFiles` own complete mappings and call `TemplateManager` directly for the root content they share. |
| VS Code entry points | Per-template defaults and the CLI context hook preserve the existing `vscode_entry_point` compatibility property. |
| Compatibility | Registry APIs, CLI/configuration behavior, generator sequencing, builders, generated files, and VS Code output remain unchanged. |
| Verification | Independent snapshots cover every template-owned file; dedicated VS Code tests cover the four editor files and entry-point behavior for each built-in. |

Sprint 8.4 introduced no new template, command, ForgePy version, or delivery date.

## Implemented — Sprint 9.0 Component Foundation

Sprint 9.0 introduces an independent component-definition and registration foundation without adding components or connecting the catalog to project generation.

| Area | Current implementation |
| --- | --- |
| Metadata | Immutable `ComponentMetadata` contains name, description, component version, author, and tuple tags. |
| Contract | `BaseComponent` defines only component name and metadata; installation behavior is intentionally absent. |
| Registry | `ComponentRegistry` starts empty and supports explicit registration, lookup by name, and immutable registration-ordered listing. |
| Validation | Registration rejects non-components, empty or mismatched names, invalid metadata, and duplicates before changing state. |
| Isolation | Components have no built-ins, discovery, persistence, CLI, configuration, template, builder, or generator integration. |
| Verification | Focused standard-library tests cover metadata immutability, valid registration, lookup/listing, and rejection paths. |

Sprint 9.0 introduced no component installation, built-in component, CLI command, ForgePy version, or delivery date.

## Completed — Sprint 9.1 Component Installation Contract

Sprint 9.1 adds only the contract required for a component to operate on an explicitly supplied existing project directory.

| Area | Current Sprint 9.1 scope |
| --- | --- |
| Context | Immutable `ComponentContext` validates one `pathlib.Path` as an existing directory. |
| Contract | `BaseComponent.install(context)` is the only installation hook. |
| Registry | Registration and lookup remain installation-agnostic and empty by default. |
| Integration | No built-in components, CLI command, discovery, persistence, dependency resolution, rollback, plugin loading, or generation integration. |

Sprint 9.1 does not change the ForgePy version or existing template behavior.

## Completed — Sprint 9.2 Component Manifest Foundation

Sprint 9.2 adds only the declarative properties currently needed to describe a component installation.

| Area | Current Sprint 9.2 scope |
| --- | --- |
| Manifest | Immutable project-relative owned or managed paths, dependencies, and conflicts. |
| Validation | Non-empty typed entries, consistent duplicate rejection, safe lexical paths, aligned component/metadata names, and no self-dependency or self-conflict. |
| Registry | Registration and lookup remain installation- and relationship-resolution agnostic. |
| Integration | No built-ins, dependency resolution, installation ordering, rollback, uninstall, persistence, discovery, marketplace, CLI, template, or generation integration. |

Sprint 9.2 does not change the ForgePy version or existing template behavior.

## Completed — Sprint 9.3 Built-in Pytest Component

Sprint 9.3 proves the existing component contracts with one real built-in and no new orchestration layer.

| Area | Implemented Sprint 9.3 behavior |
| --- | --- |
| Component | `pytest` metadata and a manifest owning only project-relative `pytest.ini`. |
| Installation | Exclusive creation of deterministic pytest configuration inside an explicitly supplied existing project. |
| Existing target | Installation raises `FileExistsError` and preserves the existing file; repeated installation follows the same policy. |
| Registry | `ComponentRegistry` registers `pytest` first by default and remains installation- and resolution-agnostic. |
| Integration | No package installation, CLI, template, configuration, builder, or `ProjectGenerator` integration. |

Sprint 9.3 does not change the ForgePy version or existing template output.

## Completed — Sprint 9.4 Component CLI

Sprint 9.4 exposes the existing component catalog and installation hook without changing component architecture or project generation.

| Area | Implemented Sprint 9.4 behavior |
| --- | --- |
| Listing | `component list` displays registered component names and descriptions. |
| Installation | `component add NAME --project PATH` resolves the registry entry, validates an existing project context, and delegates to `install(context)`. |
| Safety | Unknown names, invalid project paths, and existing owned targets produce friendly errors; exclusive component writes remain authoritative. |
| Boundaries | No package installation, discovery, persistence, dependency resolution, rollback, uninstall, template association, or `ProjectGenerator` change. |

Sprint 9.4 does not change ForgePy version `0.6.0` or existing template output.

## Completed — Sprint 9.5 Component Relationship Validation

Sprint 9.5 adds a stateless pre-install check for direct manifest relationships while keeping validation separate from installation.

| Area | Implemented Sprint 9.5 behavior |
| --- | --- |
| Installed state | Callers explicitly supply an iterable of component names considered installed. |
| Dependencies | Every directly declared dependency must appear in that supplied state. |
| Conflicts | No directly declared conflict may appear in that supplied state. |
| Failure | One `ComponentValidationError` exposes ordered missing dependencies and active conflicts. |
| Boundaries | No persistence, discovery, registry resolution, transitive resolution, version constraints, installation ordering, installation, or filesystem writes. |

Sprint 9.5 does not change ForgePy version `0.6.0`, CLI behavior, project generation, or template output.

## Completed — Sprint 9.6 Project-local Component State

Sprint 9.6 adds isolated persistence for installed ForgePy component names without connecting it automatically to installation or validation.

| Area | Implemented Sprint 9.6 behavior |
| --- | --- |
| Location | `<project>/.forgepy/components.json` under an explicitly supplied existing project. |
| Shape | One deterministic, duplicate-free `installed` array containing non-empty component-name strings. |
| Operations | Load, save, add one name, and membership check. Missing state is empty. |
| Safety | Invalid JSON or shape raises a ForgePy component-state error; saves use same-directory temporary files and atomic replacement. |
| Boundaries | Registry, CLI, validation, and installation remain separate; no uninstall, rollback, discovery, resolution, ordering, scanning, or version locking. |

Sprint 9.6 does not change ForgePy version `0.6.0`, CLI behavior, project generation, or template output.

## Completed — Sprint 9.7 Component Installation Orchestration

Sprint 9.7 adds one fixed, explicit installation sequence without adding resolution, transactions, or CLI integration.

| Area | Implemented Sprint 9.7 behavior |
| --- | --- |
| Sequence | Registry lookup, context validation, state load, already-installed rejection, direct validation, one installation hook, then state recording. |
| Failure before recording | Invalid state, relationship failure, existing targets, and hook failures leave the requested component unrecorded. |
| Recording failure | State errors after hook success are surfaced; installed files may remain because no rollback is implemented. |
| Boundaries | Registry, state store, validator, and components retain their responsibilities; registered and installed remain distinct. |
| Exclusions | No automatic dependencies, ordering, graph traversal, rollback, uninstall, discovery, scanning, package installation, version locking, or CLI connection. |

Sprint 9.7 keeps ForgePy version `0.6.0`, CLI syntax, project generation, and template output unchanged.

### Sprint 9.7 Component CLI Integration

`component add NAME --project PATH` now delegates to `ComponentInstaller`. Successful hooks are recorded in project-local state; repeated installation, direct relationship failures, malformed state, existing targets, and persistence failures receive friendly CLI output without tracebacks. `component list` remains metadata-only and side-effect free.

The integration preserves existing handled-error exit status behavior and adds no rollback, resolution, ordering, discovery, package installation, or generation integration. A state-recording failure after hook success remains a surfaced partial-success condition.

## Completed — Sprint 9.8 Installed Component State CLI

`component installed --project PATH` reads the existing project-local component state and presents stored names in deterministic order. A missing state file reports `No installed components.`; malformed state produces a friendly error and remains unchanged. Stored names remain visible even when they are not registered because catalog membership and installed state are distinct.

This read-only action adds no discovery, filesystem scanning, state migration, resolver, planning, rollback, uninstall, or project model. `component list` remains the registered catalog, and `component add` retains its `ComponentInstaller` flow.

## Completed — Sprint 9.9 Built-in Ruff Component

Sprint 9.9 adds `RuffComponent` as the second built-in, registered deterministically after `pytest`. Its manifest owns only `ruff.toml`; installation exclusively creates a small deterministic Ruff configuration and refuses an existing target without modification.

The component uses the existing installer, state store, relationship validator, and CLI flows unchanged. It does not edit `pyproject.toml`, install Ruff, invoke package tools, or add dependencies/conflicts, resolution, rollback, or special CLI handling.

## Completed — Sprint 10.0 Built-in GitHub Actions Component

Sprint 10.0 adds `GitHubActionsComponent` as the third built-in, registered after `pytest` and `ruff`. Its manifest owns only `.github/workflows/ci.yml`; installation creates the required parent directories and exclusively writes a minimal deterministic workflow for checkout, Python setup, CI-only pytest and Ruff installation, linting, and tests.

The component declares no ForgePy component dependencies because its workflow installs its own CI tools. It uses the existing registry, installer, state, validation, and generic CLI paths unchanged; local installation does not access the network, install packages, or modify `requirements.txt` or `pyproject.toml`.

## Completed — Sprint 11.1 Project Destination Safety

Sprint 11.1 validates project names as one non-empty filesystem segment before generation writes. Dot names, absolute and Windows drive-qualified names, path separators, and lexical multi-component names are rejected rather than normalized into another destination.

`ProjectGenerator` resolves the selected existing directory, requires the new destination to remain its direct child, and rejects every existing destination file, directory, symlink, or junction. A valid destination is created exclusively before the unchanged template and tooling stages. Unknown-template ordering, CLI error translation, generated Python/TOML quoting, rollback, and generalized filesystem ownership remain separate concerns.

## Completed — Sprint 11.2 Component State Confinement

Sprint 11.2 preserves `<project>/.forgepy/components.json` while resolving and confining the state directory, state file, and atomic temporary file beneath the resolved project root. Existing symlinks, junctions, or equivalent redirections outside the project are rejected with a ForgePy component-state I/O error before state access or component installation.

Missing in-project state remains empty and side-effect free; malformed state remains unchanged; successful saves retain same-directory temporary files, flush/`fsync`, and atomic replacement. Registry, validation, installer sequencing, concrete components, project generation, and the existing CLI error policy remain unchanged.

## Completed — Sprint 11.3 Template Validation Ordering

Sprint 11.3 preserves destination validation precedence and the registry's existing `KeyError` lookup contract while moving template lookup before exclusive project-root creation. An unknown template now leaves no project directory, template file, builder operation, subprocess action, dependency installation, or Git initialization artifact.

The `basic`, `library`, and `cli` registrations, generated output, project-destination safety, CLI error policy, and remaining lifecycle stages are unchanged.

## Completed — Sprint 11.4 Project Name Validity

Sprint 11.4 extends the one-segment destination rule with the supported Windows filename and current generated-content contract. Whitespace-only names, control characters, Windows-invalid filename characters, trailing spaces or dots, and reserved device stems (including extension forms) are rejected before template lookup or generation writes.

Accepted human-readable display names remain unchanged. Library and CLI templates continue to derive their Python package identifiers through the existing separate normalization step; no general template escaping framework was added.

### Sprint 11.5 — Template-specific package preflight

Sprint 11.5 adds a harmless template preflight after destination validation and template lookup but before project-root creation. File-based templates preflight through their existing context construction, so library and CLI reuse the established package normalizer and reject display names that yield no usable ASCII Python identifier without filesystem, builder, or subprocess activity.

The basic template retains the complete `ProjectConfig` display-name contract and has no package-specific restriction. Existing destination errors and unknown-template `KeyError` behavior remain authoritative in their established order.

### Sprint 11.6 — CLI error status and presentation

Sprint 11.6 establishes the minimal CLI process contract: `0` for success, `1` for handled operational or user failures, and argparse's existing `2` for syntax or usage errors. Commands return integer statuses through `Dispatcher` to `main`, while create, configuration, and component commands translate their expected domain and operational failures into concise output without tracebacks.

Library exception contracts remain at their owning boundaries, unexpected programming errors still surface, and no global exception hierarchy or error-management framework was added.

### Sprint 11.7 — Generated-file lifecycle ordering

Sprint 11.7 moves VS Code generation before Git initialization, staging, and the initial commit. All ForgePy-owned template and editor files therefore exist before `git add .`; a VS Code failure prevents Git from running, while a commit failure propagates before full-success reporting.

Git and VS Code responsibilities remain separate, and partial projects remain possible because no rollback or transaction framework was added.

### Sprint 11.8 — Bounded lifecycle subprocesses

Sprint 11.8 adds explicit finite, stage-owned timeouts to virtual-environment creation, packaging-tool upgrades, requirements installation, and Git initialization, staging, and commit. Timeout and non-zero-exit failures retain Python's existing subprocess exceptions, identify the failed stage, stop later lifecycle work, and use the existing CLI status-`1` translation.

Packaging upgrades and dependency installation may require network access. No retry, cache, rollback, generic subprocess wrapper, or cross-platform environment-path change was introduced; partial destinations remain available for inspection or removal before retrying.

## Completed — Sprint 11.9 Required Git Creation Stage

Sprint 11.9 defines Git initialization, staging, and the initial commit as the required final stage of successful project creation. An unavailable Git executable now raises `FileNotFoundError`, uses the existing CLI operational-failure translation and status `1`, and prevents full-success reporting.

Git discovery remains owned by `GitBuilder` when its lifecycle stage is reached. Earlier generated artifacts remain because no early dependency discovery, rollback, cleanup, or new tool-management abstraction was introduced.

## Completed — Sprint 12.1 Standard Python Packaging

Sprint 12.1 adds a setuptools-backed root `pyproject.toml`, constrained runtime-package discovery, and the installed `forgepy` console command through the existing `main:main` entry path. Distribution version metadata reads the canonical `config.version.VERSION`, while ForgePy remains standard-library-only at runtime and keeps template and component revisions independent.

Packaging excludes tests and repository-only utilities, requires no non-Python package data, and introduces no CLI duplication, source-layout migration, plugin discovery, or release framework. Repository licensing, the final README, and release artifact validation remain separate release-readiness work.

## Completed — Sprint 12.2 Support Contract

Sprint 12.2 defines the v1.0 support target as Windows 10/11 on CPython 3.12+ and records Python 3.12, 3.13, and 3.14 as the required validation matrix. Packaging metadata advertises only CPython and Windows support; Linux, macOS, and alternative Python implementations remain unsupported and unverified.

The existing Windows-specific environment paths, destination-name rules, and generated VS Code paths remain unchanged. No runtime platform guard or portability abstraction was added. The contract is ready for real `windows-latest` interpreter-matrix validation in Sprint 12.3, so local results on one interpreter do not make the support claim release-final.

## Completed — Sprint 12.3 Repository CI

Sprint 12.3 adds ForgePy's repository-level GitHub Actions workflow on `windows-latest` for CPython 3.12, 3.13, and 3.14. Every matrix entry runs the full unit suite, `compileall`, and focused packaging/support tests. The Python 3.12 entry also builds and inspects the wheel and sdist, installs the wheel in isolation, and exercises the installed CLI from outside the checkout.

This repository workflow is separate from the minimal built-in `github-actions` component generated into user projects. The CPython 3.12, 3.13, and 3.14 jobs pass, including Python 3.12 artifact and installed-CLI validation. GitHub's hosted Windows runner validates runner compatibility rather than literally proving both Windows 10 and Windows 11 client editions.

## Completed — Sprint 12.4 Public README

Sprint 12.4 replaces the empty root README with a public guide covering source and editable installation, verified CLI usage, built-in templates and components, configuration, the project-creation lifecycle, partial-project behavior, supported Windows and CPython environments, and contributor validation. It makes no PyPI availability, v1.0 release, license, or native Windows client-test claim.

## Completed — Sprint 12.5 Release Metadata and Changelog

Sprint 12.5 links the distribution long description to `README.md`, adds verified GitHub project URLs, minimal search keywords, and a pre-stable Beta classifier, and introduces a concise `CHANGELOG.md`. The changelog keeps post-0.6.0 work under Unreleased and summarizes only the formally tagged `0.6.0` baseline as released history.

ForgePy remains `0.6.0`. The maintainer selected the MIT License, recorded in the root `LICENSE` and modern SPDX package metadata without a legacy license classifier. Sprint 12.6 is the next release-candidate validation stage; Sprint 12.5 creates no tag, release, or publishing workflow.

## Completed — Sprint 12.6 v1.0 Release Candidate

Sprint 12.6 establishes `1.0.0rc1` as the canonical development version while
the latest stable tag remains `v0.6.0`. Packaging continues to derive the
version from `config.version.VERSION`; this RC is not final v1.0.0 and does not
claim a tag, GitHub Release, or PyPI publication.

The RC gate requires the full automated suite, compilation and source CLI
checks, fresh artifact build and inspection, clean wheel installation,
installed CLI probes outside the checkout, and temporary installed-wheel
project generation with isolated Git configuration. Native Windows 10 and
Windows 11 smoke checks remain separately recorded manual evidence; hosted
`windows-latest` results do not prove either client edition.

The `v1.0.0rc1` tag and GitHub prerelease were created after its Windows
CPython 3.12-3.14 CI passed. Native Windows 11 25H2, fresh artifacts, isolated
wheel installation, installed CLI, and installed-wheel project generation also
passed. Windows 10 was not directly tested, and no PyPI publication occurred.

## Completed — Sprint 12.7 Final v1.0.0 Promotion

Sprint 12.7 promotes the validated RC to final version source `1.0.0` without
new product behavior. Fresh final artifacts, isolated installation, installed
CLI checks, and native Windows 11 25H2 installed-wheel project generation pass
locally. The final `v1.0.0` tag and GitHub Release now exist; PyPI publication
remains separate. Windows 10 has not been directly tested.

## In progress — Sprint 12.8 PyPI Trusted Publishing

Sprint 12.8 prepares the first PyPI publication under distribution name
`forgepy-cli` without changing the ForgePy application brand, `forgepy` console
command, Python packages, or canonical `1.0.0` version. Current package URLs use
`rzou89/ForgePy`.

The repository publishing workflow uses separate build and publish jobs, passes
fresh wheel and sdist files through a workflow artifact, and uses GitHub OIDC
Trusted Publishing with the official PyPA action. The pending publisher is
bound to `rzou89/ForgePy`, `publish.yml`, and GitHub environment `pypi`.
Publishing can occur for a newly published GitHub Release; a deliberate manual
dispatch supports the first upload because the existing v1.0.0 Release event
predates the workflow. No PyPI upload is claimed.

## Completed — Post-v1.0 Linux Support

After the v1.0.0 release, ForgePy expanded the supported project-generation path from Windows-only behavior to a cross-platform Windows/Linux contract.

The merged Linux support work updates virtual-environment interpreter resolution and generated VS Code configuration to use platform-aware paths while preserving the existing project-name portability rules and lifecycle ordering.

| Area | Current post-v1.0 behavior |
| --- | --- |
| Supported platforms | Windows and Linux on CPython. |
| Virtual environment | Windows uses `.venv/Scripts/python.exe`; POSIX systems use `.venv/bin/python`. |
| VS Code | Generated interpreter settings follow the same platform-aware path rule. |
| Repository CI | `windows-latest` and `ubuntu-latest` validate CPython 3.12, 3.13, and 3.14. |
| Native smoke evidence | Full project creation has passed on CachyOS Linux. |
| Compatibility | Windows-compatible project-name rules remain intentionally stricter so generated projects stay portable across supported platforms. |

This work does not claim macOS or alternative Python implementations as supported.

## Completed — Interactive Project Wizard

Post-v1.0 ForgePy also added a guided Easy Mode for users who run ForgePy without a subcommand, including the VS Code **Run ▶** workflow.

The merged wizard work keeps Advanced Mode backward compatible while making template selection explicit and user-friendly.

| Area | Current behavior |
| --- | --- |
| Easy Mode | No-command startup guides project name, location, template selection, confirmation, and creation. |
| Template catalog | The wizard reads registered templates from `TemplateRegistry` rather than duplicating a separate list. |
| Built-in choices | `basic` = General Application, `cli` = CLI / Automation / Backend Tool, `library` = Python Library. |
| Metadata | Templates expose user-facing `display_name` and `use_cases` in addition to the existing metadata contract. |
| Cancellation | Selection `0` cancels before generation; confirmation `n`/`no` also cancels before `ProjectGenerator` runs. |
| Invalid input | Invalid template selections and invalid confirmation responses are rejected and prompted again. |
| Advanced Mode | Explicit `create` usage preserves configuration-driven fallback behavior and does not show the interactive template menu when `--template` is supplied. |
| Verification | Focused tests cover all three selections, retries, cancellation, confirmation, and Advanced Mode separation; manual full lifecycle creation also passed. |

## Planned — Post-v1.0 Maintenance

These are outcome-oriented priorities, not guaranteed feature commitments.

### Repository Consistency

- Keep `README.md`, `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `AGENTS.md`, `ROADMAP.md`, and `CHANGELOG.md` aligned with implemented behavior.
- Keep the canonical application version synchronized with release tags without duplicating it in module headers.
- Keep the MIT License file and package metadata aligned through release validation.
- Keep template presentation metadata synchronized with the real registered template catalog.

### Verification and Failure Behavior

- Continue expanding automated coverage across builders, the full generator lifecycle, interactive behavior, and subprocess failure boundaries.
- Preserve predictable handling for missing tools, invalid destinations, unknown templates, and failed subprocesses.
- Retain documented manual smoke checks where hosted CI cannot prove native-platform behavior.

### Compatibility and Support

- Keep repository CI green on both `windows-latest` and `ubuntu-latest` with CPython 3.12, 3.13, and 3.14.
- Preserve the stable CLI contract, all three built-in template names and outputs, and the project-generation lifecycle unless a reviewed requirement explicitly changes them.
- Preserve the intentional distinction between Easy Mode and Advanced Mode.
- Define a template-metadata version policy before independently evolving template revisions in ways that require compatibility guarantees.
- Keep Windows and Linux support documented accurately without claiming macOS or alternative Python implementations as verified.

### Distribution and Release Maintenance

- Complete the first `forgepy-cli` PyPI publication when the maintainer deliberately approves and dispatches the prepared Trusted Publishing workflow.
- Keep GitHub Release, package metadata, changelog, and documentation synchronized for future releases.

## Ideas — Not Scheduled

- Evaluate further commands or templates beyond `basic`, `library`, and `cli` only after a concrete use case and compatibility review.
- Evaluate macOS support only after the project has a defined compatibility target and a real validation plan.
- Evaluate additional Easy Mode usability improvements, such as friendlier interruption handling or post-creation guidance, only as separately scoped changes.

Ideas become planned work only after maintainer approval, defined acceptance criteria, and an identified verification approach.
