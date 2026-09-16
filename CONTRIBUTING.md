# Contributing to ForgePy

Thank you for improving ForgePy. Keep contributions focused on the behavior and architecture present in the repository, and discuss substantial product changes with the maintainers before implementation.

## ForgePy Philosophy

Prefer clear, focused automation; explicit module boundaries; visible side effects; and backward-compatible, evidence-based evolution. Read [`ENGINEERING_PRINCIPLES.md`](ENGINEERING_PRINCIPLES.md) before changing behavior or architecture.

## Development setup

ForgePy currently uses only the Python standard library and has an empty root `requirements.txt`.

Prerequisites are Git and CPython 3.12+ with the standard-library `venv` module. Git is required for project creation; if its executable is unavailable when the final Git stage is reached, creation fails and may leave an already-generated partial project. ForgePy v1.0 officially supports Windows 10, Windows 11, and Linux on CPython. macOS and alternative Python implementations remain unsupported and unverified. CPython 3.12, 3.13, and 3.14 are the required v1.0 validation targets.

Generated-project requirements are separate from ForgePy's empty root requirements file. The `basic` template declares `PySide6`, `pandas`, and `openpyxl`; the minimal `library` and `cli` templates write empty requirements files. A full create run still upgrades packaging tools, so it may require network access.

Windows PowerShell:

```powershell
git clone <repository-url>
cd ForgePy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
forgepy --help
```

Linux:

```bash
git clone <repository-url>
cd ForgePy
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
forgepy --help
```

The editable install uses the root `pyproject.toml`, exposes the existing
`main:main` application path as `forgepy`, and reads distribution version
metadata from `config/version.py`. ForgePy declares no third-party Python
runtime dependencies and is licensed under the root MIT License.

The Python distribution is named `forgepy-cli`; the application brand remains
ForgePy and the installed command remains `forgepy`.

Release-facing metadata uses `README.md` as the distribution long description,
and `CHANGELOG.md` records Unreleased work plus only formally tagged history.
Package license metadata uses the SPDX expression `MIT` and distributes the
root `LICENSE` file. This does not introduce a CLA, copyright assignment, DCO,
or other contributor-licensing process.

The implementation and generated VS Code configuration use platform-aware virtual-environment paths for Windows and POSIX systems.

Repository CI is defined in `.github/workflows/ci.yml` and targets both `windows-latest` and `ubuntu-latest` with CPython 3.12, 3.13, and 3.14. Every matrix entry runs the full unit suite, `compileall`, and packaging/support tests. The Python 3.12 jobs also build and inspect the wheel and sdist, install the wheel in an isolated environment, run the installed `forgepy --help`, `forgepy version`, `forgepy list`, and `forgepy component list` commands from outside the checkout, verify the expected ForgePy version, and verify that tests and `utils` remain absent from the distribution artifacts.

The CPython 3.12, 3.13, and 3.14 matrix on Windows and Ubuntu must remain green as the project approaches v1.0. The hosted runners validate those environments but do not literally prove every Windows edition or Linux distribution. A full project-creation smoke test has been completed successfully on CachyOS Linux; additional native-platform smoke validation may remain a release-stage manual check. This repository workflow is intentionally richer than the independent `github-actions` component generated into user projects.

PyPI publishing is defined separately in `.github/workflows/publish.yml`. It
builds fresh distributions, transfers them through a workflow artifact, and
publishes from a job bound to the GitHub environment `pypi` using OIDC Trusted
Publishing. The pending publisher is scoped to owner `rzou89`, repository
`ForgePy`, workflow `publish.yml`, and environment `pypi`. Do not configure a
PyPI API-token secret. Repository environment protection, including an optional
required maintainer review, may be used to gate publication.

## Coding style

- Follow PEP 8 and use four-space indentation.
- Add type annotations to public functions and methods.
- Use `pathlib.Path` for file-system paths and UTF-8 for text files.
- Use `snake_case` for modules, functions, methods, and variables; `PascalCase` for classes; and uppercase for constants.
- Order imports as standard library, then project-local modules.
- Keep commands, builders, templates, and orchestration separate.
- Keep builders single-purpose and leave workflow sequencing to `ProjectGenerator`.
- Generate file contents in `templates/`; do not embed large templates in CLI or orchestration modules.
- Preserve the existing console-message prefixes for user-visible status.

## Branching strategy

Repository policy treats `master` as the protected stable branch. Create a short-lived feature branch from it for every ForgePy implementation change. Use a descriptive prefix:

- `feature/` for user-visible additions
- `fix/` for defect corrections
- `docs/` for documentation
- `refactor/` for behavior-preserving restructuring
- `test/` for test-only work

Keep branches limited to one logical change. Synchronize with the default branch before final review, and do not rewrite shared branch history.

Examples include `feature/cli-validation`, `fix/template-lookup`, `docs/project-context`, and `test/basic-template`.

## Commit convention

Use Conventional Commits for changes to the ForgePy repository:

```text
<type>(<optional-scope>): <imperative summary>
```

Supported common types include `feat`, `fix`, `docs`, `refactor`, `test`, `build`, and `chore`. Useful scopes include `cli`, `core`, `builders`, and `templates`.

Examples:

```text
fix(templates): report an unknown template
test(cli): cover default create dispatch
docs: document project architecture
```

Keep the subject concise. Use the body to explain motivation, trade-offs, or migration details when they are not obvious from the diff.

The generator's fixed initial-commit message belongs to newly generated projects and is separate from this contribution convention.

## Testing requirements

The repository uses the Python standard library `unittest` framework for focused user-configuration, CLI, create-input-resolution, and template-metadata coverage. Contributions that change behavior should introduce or update focused automated tests. Where an area remains uncovered, verify the affected behavior directly and describe the command and result in the pull request.

Relevant coverage includes:

- user configuration defaults, persistence, validation, updates, resets, and error handling
- CLI parsing and dispatch for `create`, `list`, `version`, `config`, and `component`
- `config show/set/reset` output, persistence, validation, and malformed-file handling
- validation of interactive and explicit create inputs
- create precedence from explicit location/template arguments through persisted defaults to the existing prompt/`basic` fallback
- configuration-read failures that abort creation without prompting, generating, or overwriting user data
- template metadata registration, registry lookup, and list-command output
- the exact folders and files produced by each affected built-in template
- generated text and JSON content
- subprocess success and failure paths without invoking real package installation or Git operations in unit tests
- behavior around missing locations, tools, requirements, and virtual environments

Tests that create files should use an isolated temporary directory and must not write generated projects into the repository. External commands should be mocked in unit tests. Run the full available suite before submitting; if no automated test covers the change, include the manual verification performed.

### Supported manual checks

Run the automated suite with:

```powershell
python -m unittest discover -s tests -v
```

These read-only commands exercise existing CLI paths:

```powershell
python main.py --help
python main.py version
python main.py list
python main.py config --help
python main.py component --help
python main.py component list
```

`config show` reads and prints the effective user configuration, while `config set` and `config reset` write `~/.forgepy/config.json`. Run all three against an isolated home during recorded manual verification so user values are neither changed nor exposed in logs. On Windows PowerShell, use a process-scoped temporary `USERPROFILE` and restore it afterward:

```powershell
$forgepyOriginalProfile = $env:USERPROFILE
$forgepyTestProfile = Join-Path $env:TEMP (
    "forgepy-cli-test-" + [guid]::NewGuid()
)
New-Item -ItemType Directory -Force -Path $forgepyTestProfile | Out-Null

try {
    $env:USERPROFILE = $forgepyTestProfile
    python main.py config show
    python main.py config set author "Test User"
    python main.py config show
    python main.py config reset
}
finally {
    $env:USERPROFILE = $forgepyOriginalProfile
    Remove-Item -LiteralPath $forgepyTestProfile -Recurse -Force
}
```

`python main.py` and `python main.py create <name> --location <existing-path> --template <basic-or-library-or-cli>` are also supported, but they start or perform a side-effectful generation lifecycle. Omitted location or template options can read the current user configuration; use both explicit options for a deterministic bypass or isolate `USERPROFILE`. Run generation only with deliberate input in an isolated temporary parent directory because it may build an environment, install packages, and initialize Git.

### Release-candidate validation gate

An RC review requires all of the following evidence:

1. Run the full unit suite, `compileall`, and source-tree `--help`, `version`,
   `list`, and `component list` probes.
2. Build fresh wheel and sdist artifacts.
3. Inspect both artifacts for the canonical version, README metadata, MIT
   license metadata and file, console entry point, required runtime packages,
   sdist `CHANGELOG.md` and `pyproject.toml`, and absence of `tests` and `utils`.
4. Install the wheel without dependencies into a clean isolated environment.
5. From outside the checkout, run installed `forgepy --help`, `forgepy version`,
   `forgepy list`, and `forgepy component list`.
6. Confirm Git is available, use temporary process-scoped Git identity/config,
   and create at least one temporary project with the installed CLI outside the
   checkout. Verify successful exit, expected template files, `.venv`, applicable
   VS Code configuration, `.git`, and an initial commit, then remove the project.

The GitHub-hosted `windows-latest` matrix does not literally validate native
Windows 10 or Windows 11 clients. For each native client that is actually
available, record a manual checklist covering RC-wheel installation, `forgepy
--help`, `forgepy version`, `forgepy list`, temporary basic-project creation,
virtual-environment creation, Git initialization and initial commit, expected
project structure, and cleanup. Do not claim an edition passed without recorded
evidence.

## Pull request rules

- Open one pull request per logical change.
- Explain the problem, the chosen solution, and any user-visible effect.
- Link the relevant issue or discussion when one exists.
- Include tests for changed behavior and documentation for changed interfaces.
- Update documentation whenever behavior, CLI syntax, generated output, or architectural contracts change.
- Report platform assumptions, external commands, and manual verification.
- Keep generated artifacts, virtual environments, logs, editor state, and secrets out of the diff.
- Avoid unrelated formatting or refactoring.
- Confirm that `git diff` contains only intentional changes.
- Obtain review before merging; do not merge with unresolved review comments or failing checks.
- Require passing tests or clearly documented manual verification before merging.

## Definition of Done

Before requesting review, confirm:

- [ ] The requested scope and acceptance criteria are complete.
- [ ] No unrelated refactor or architectural movement is included.
- [ ] Existing commands, interactive behavior, template names, and generated output remain compatible unless explicitly changed.
- [ ] Tests pass, or supported manual verification commands and results are documented.
- [ ] Relevant behavior and architecture documentation is updated.
- [ ] `git diff --check` passes and `git status --short` shows only intended files.
- [ ] The pull request explains assumptions, compatibility impact, limitations, and verification.

## Code Review Checklist

- [ ] The change is focused and matches the stated problem.
- [ ] CLI, core orchestration, builders, templates, models, and configuration retain clear responsibilities.
- [ ] File-system and subprocess side effects are explicit and have appropriate failure handling.
- [ ] Type hints, `pathlib.Path`, UTF-8 I/O, naming, and imports follow project conventions.
- [ ] Compatibility-sensitive behavior is preserved or accompanied by an approved migration explanation.
- [ ] Tests isolate external commands and temporary files; manual checks are reproducible when tests are unavailable.
- [ ] No secret, generated environment, editor state, or unrelated formatting change is present.

## Documentation Checklist

- [ ] Current, in-progress, planned, and exploratory behavior are not conflated.
- [ ] CLI examples were verified against supported syntax.
- [ ] Directory trees, dependency diagrams, lifecycles, and module descriptions match the code.
- [ ] ForgePy version statements match `config/version.py` and the current release tag; template-metadata, generated-project, and schema versions remain distinct.
- [ ] Platform or Python support claims have evidence.
- [ ] `PROJECT_CONTEXT.md`, `ROADMAP.md`, and `ARCHITECTURE.md` are updated when their facts change.
- [ ] Markdown links, headings, tables, lists, and code fences render correctly on GitHub.

## Adding a template

A new template contribution should implement `BaseTemplate`, provide `TemplateMetadata` with a non-empty stable `name`; string `description`, template `version`, and `author`; and an iterable of string `tags` stored as a tuple. Register through `TemplateRegistry.register()`; the metadata name must match the template's selection name and must not duplicate an existing registration. Explicitly declare the real `vscode_entry_point`, or `None` when the template has no runnable application file; do not infer it from generated paths. Keep rendered content separate from file writes, add coverage for registration, registry listing, generated output, and template-matched VS Code JSON, and do not change existing built-in template contracts incidentally.
