# ForgePy Agent Guide

## Purpose and boundaries

ForgePy is a cross-platform Python project generator for Windows and Linux. It currently provides the `basic`, `library`, and `cli` templates, then prepares `.venv`, updates packaging tools, installs generated requirements, writes VS Code configuration, and initializes Git with an initial commit.

ForgePy supports two project-creation interaction modes:

- **Easy Mode**: no command is supplied, so ForgePy guides the user through project name, location, template selection, confirmation, and creation.
- **Advanced Mode**: the explicit `create` command resolves CLI arguments and configuration without opening the interactive template-selection wizard when a template is already supplied.

## ForgePy Philosophy

Favor clear, focused automation and ordinary generated Python projects. Preserve behavior intentionally, keep side effects visible, and describe repository facts separately from future ideas. Apply the detailed policy in [`ENGINEERING_PRINCIPLES.md`](ENGINEERING_PRINCIPLES.md).

Preserve these boundaries:

- `cli/` parses and dispatches commands; commands own CLI-facing interaction and delegate application work.
- `core/ProjectGenerator` owns generation order.
- `builders/` performs focused file-system or Python-tool operations.
- `components/` owns independent component metadata, its declarative manifest, validated project context, the component installation hook, and in-memory registration. It has no template, configuration, builder, or project-generation responsibility.
- `templates/` owns descriptive metadata, per-generation context, rendered content, and explicit template-specific VS Code entry-point requirements; `TemplateRegistry` registers and selects `BaseTemplate` implementations and is the source of truth for the interactive template catalog.
- `models/` carries project data; `config/` owns application metadata, generated-layout defaults, and isolated user-configuration persistence.

Do not silently move responsibilities between these areas or perform broad refactors for a focused change.

## Before editing

1. Read `git status --short` and preserve user-owned changes.
2. Inspect the repository tree, relevant source, configuration, tests, and documentation.
3. Check Git history and tags when release or roadmap facts matter.
4. State assumptions when repository evidence is incomplete or inconsistent.

## Implementation rules

- Follow PEP 8, use Python type hints, `pathlib.Path`, UTF-8 text I/O, four-space indentation, and clear names.
- Keep CLI parsing in `Parser`, routing in `Dispatcher`, and CLI-facing behavior in `Command` implementations.
- Keep builders single-purpose; do not add prompting or template selection to builders.
- Implement built-in file-mapping templates through `FileTemplate` while preserving the `BaseTemplate` public contract. Keep `TemplateMetadata`, per-generation `TemplateContext`, and template-owned file mappings separate, and register templates through `TemplateRegistry.register()`.
- Give template metadata a non-empty stable `name`; string `description`, `version`, and `author`; an iterable of string `tags`; optional user-facing `display_name`; and an iterable of string `use_cases`. Keep metadata collections immutable after construction.
- Treat template metadata as registry and presentation data. Keep `metadata.name` aligned with the stable template selector. `display_name` and `use_cases` may improve presentation but must not alter generated output or template identity.
- Keep `TemplateRegistry` as the source of truth for registered templates. Do not duplicate the built-in template catalog in CLI wizard code.
- Implement component definitions through `BaseComponent`, immutable `ComponentMetadata` and `ComponentManifest`, and validated `ComponentContext`; keep component and metadata names aligned, and register explicitly through `ComponentRegistry.register()`. Manifest file declarations must remain project-relative. A new registry contains only the explicitly approved `pytest`, `ruff`, and `github-actions` built-ins by default and must not resolve manifest relationships or perform installation. Do not add further built-ins or application integration without an explicit requirement.
- Keep each built-in template's VS Code entry-point requirement explicit through `FileTemplate`'s default or context hook. `ProjectGenerator` may forward the `vscode_entry_point` compatibility property, while `VSCodeBuilder` remains responsible for rendering and writing editor files; do not infer the requirement from generated paths. A `FileTemplate` subclass that overrides `__init__()` must call `super().__init__()`.
- Keep lifecycle sequencing in `ProjectGenerator`.
- Preserve no-command dispatch to `create`.
- In Easy Mode, keep the guided flow in `CreateCommand`: project name, location resolution/prompting, template selection from `TemplateRegistry`, confirmation, then `ProjectGenerator`.
- In Advanced Mode, resolve explicit CLI values first. An omitted location uses `default_location` and then prompts if necessary. An omitted template uses `default_template` and then falls back to `basic`.
- If Advanced Mode receives an explicit `--template`, do not display the interactive template-selection prompt.
- Keep `ProjectGenerator`, builders, and templates independent of `ConfigStore`.
- Do not apply persisted `author` or `license` values to generated files without an explicit requirement.
- Preserve existing commands, template names, generated paths/content, and public contracts unless an approved change explicitly replaces them.
- Preserve platform-aware environment behavior: `.venv/Scripts/python.exe` on Windows and `.venv/bin/python` on POSIX systems. Do not reintroduce Windows-only assumptions into supported project-generation paths.
- ForgePy currently supports Windows and Linux on CPython; macOS and alternative Python implementations remain unsupported and unverified.
- Avoid new dependencies and unrelated cleanup unless required and documented.

## Verification

- Add or update focused tests for behavior changes, using the existing `unittest` infrastructure where applicable.
- For Easy Mode changes, cover template selection, invalid-selection retry, cancellation, confirmation, and separation from Advanced Mode when relevant.
- For template metadata changes, verify registry behavior and presentation metadata without changing generation semantics.
- Where automated coverage does not yet exist, run supported manual checks and document the results.
- Use isolated temporary locations for generation checks; do not generate test projects in this repository.
- Before handoff, run `git diff --check` and `git status --short` and inspect the final diff.

## Definition of Done

- The requested scope is complete without unrelated refactoring.
- Architectural boundaries and backward-compatible CLI/template behavior are preserved or an approved change is documented.
- Easy Mode and Advanced Mode remain intentionally distinct where create-input behavior differs.
- Tests pass, or supported manual verification and results are recorded.
- Relevant context, architecture, roadmap, and contributor documentation is current.
- The final diff passes `git diff --check` and contains no unintended files, secrets, or generated artifacts.

## Git and review rules

- Repository policy treats `master` as the protected stable branch. Future ForgePy implementation work requires a focused branch such as `feature/...`, `fix/...`, `docs/...`, or `test/...`.
- Use Conventional Commits for ForgePy contributions, for example `feat(cli): add command routing` or `fix(templates): validate template name`.
- Require tests or documented manual verification before merging.
- Never automatically commit, push, tag, publish, force-push, rewrite history, or run destructive commands against the ForgePy repository. This rule does not redefine the generator's implemented attempt to create an initial commit inside a generated project.
- Do not delete, rename, or overwrite unrelated files.

## AI collaboration

- Make only requested changes and never invent implemented behavior.
- Re-read relevant source before changing behavior; do not rely only on summaries or stale documentation.
- Do not silently change architecture; explain any proposed boundary change first.
- Preserve the registered template catalog unless the requested work explicitly adds or removes a real template.
- Stop and ask when requirements conflict or ambiguity could materially change the result.
- In the final summary, explain assumptions, list changed files, and report every test or verification command with its result.
