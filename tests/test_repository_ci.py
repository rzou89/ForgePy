"""Contract tests for ForgePy repository-level continuous integration."""

import re
import unittest
from pathlib import Path


class RepositoryCIContractTests(unittest.TestCase):

    project_root = Path(__file__).resolve().parents[1]
    workflow_path = (
        project_root / ".github" / "workflows" / "ci.yml"
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = cls.workflow_path.read_text(
            encoding="utf-8"
        )

    def test_repository_workflow_exists_with_master_triggers(
        self,
    ) -> None:

        self.assertTrue(self.workflow_path.is_file())

        self.assertRegex(
            self.workflow,
            re.compile(
                r"push:\s+branches:\s+- master",
                re.MULTILINE,
            ),
        )

        self.assertRegex(
            self.workflow,
            re.compile(
                r"pull_request:\s+branches:\s+- master",
                re.MULTILINE,
            ),
        )

    def test_workflow_uses_windows_and_linux_cpython_matrix(
        self,
    ) -> None:

        self.assertIn(
            "runs-on: ${{ matrix.os }}",
            self.workflow,
        )

        self.assertIn(
            "- windows-latest",
            self.workflow,
        )

        self.assertIn(
            "- ubuntu-latest",
            self.workflow,
        )

        self.assertIn(
            "uses: actions/checkout@v5",
            self.workflow,
        )

        self.assertIn(
            "uses: actions/setup-python@v6",
            self.workflow,
        )

        for python_version in (
            "3.12",
            "3.13",
            "3.14",
        ):
            with self.subTest(
                python_version=python_version
            ):
                self.assertIn(
                    f'- "{python_version}"',
                    self.workflow,
                )

    def test_every_matrix_entry_runs_required_validation(
        self,
    ) -> None:

        required_commands = (
            "python -m unittest discover -s tests -v",
            (
                "python -m compileall -q components cli "
                "templates core config builders models tests"
            ),
            "python -m unittest tests.test_packaging -v",
        )

        for command in required_commands:
            with self.subTest(command=command):
                self.assertIn(
                    command,
                    self.workflow,
                )

    def test_python_312_builds_and_inspects_distributions(
        self,
    ) -> None:

        self.assertGreaterEqual(
            self.workflow.count(
                "if: matrix.python-version == '3.12'"
            ),
            3,
        )

        self.assertIn(
            "python -m build",
            self.workflow,
        )

        self.assertIn(
            "zipfile.ZipFile",
            self.workflow,
        )

        self.assertIn(
            "tarfile.open",
            self.workflow,
        )

        self.assertIn(
            'metadata["Version"] == VERSION',
            self.workflow,
        )

        self.assertIn(
            'metadata["License-Expression"] == "MIT"',
            self.workflow,
        )

        self.assertIn(
            ".dist-info/licenses/LICENSE",
            self.workflow,
        )

        self.assertIn(
            "forgepy = main:main",
            self.workflow,
        )

        self.assertIn(
            'assert "tests" not in wheel_roots',
            self.workflow,
        )

        self.assertIn(
            'assert "pyproject.toml" in relative_names',
            self.workflow,
        )

        for release_file in (
            "README.md",
            "CHANGELOG.md",
            "LICENSE",
        ):
            with self.subTest(
                release_file=release_file
            ):
                self.assertIn(
                    (
                        f'assert "{release_file}" '
                        "in relative_names"
                    ),
                    self.workflow,
                )

        self.assertIn(
            'assert "utils" not in sdist_roots',
            self.workflow,
        )

    def test_python_312_installs_wheel_on_both_platforms(
        self,
    ) -> None:

        self.assertIn(
            'python -m venv "$validation_root"',
            self.workflow,
        )

        self.assertIn(
            'if [[ "$RUNNER_OS" == "Windows" ]]',
            self.workflow,
        )

        self.assertIn(
            "$validation_root/Scripts/python.exe",
            self.workflow,
        )

        self.assertIn(
            "$validation_root/bin/python",
            self.workflow,
        )

        self.assertIn(
            "$validation_root/Scripts/forgepy.exe",
            self.workflow,
        )

        self.assertIn(
            "$validation_root/bin/forgepy",
            self.workflow,
        )

        self.assertIn(
            (
                '"$validation_python" -m pip '
                'install "$wheel" --no-deps'
            ),
            self.workflow,
        )

        for command in (
            '"../$forgepy" --help',
            '"../$forgepy" version',
            '"../$forgepy" list',
            '"../$forgepy" component list',
        ):
            with self.subTest(command=command):
                self.assertIn(
                    command,
                    self.workflow,
                )


class PublishWorkflowContractTests(unittest.TestCase):

    project_root = Path(__file__).resolve().parents[1]

    workflow_path = (
        project_root
        / ".github"
        / "workflows"
        / "publish.yml"
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = cls.workflow_path.read_text(
            encoding="utf-8"
        )

        cls.normalized_workflow = (
            cls.workflow.casefold()
        )

    def test_publish_workflow_exists_with_intentional_triggers(
        self,
    ) -> None:

        self.assertTrue(
            self.workflow_path.is_file()
        )

        self.assertRegex(
            self.workflow,
            re.compile(
                r"release:\s+types:\s+- published",
                re.MULTILINE,
            ),
        )

        self.assertRegex(
            self.workflow,
            re.compile(
                r"workflow_dispatch:\s*$",
                re.MULTILINE,
            ),
        )

        self.assertNotRegex(
            self.workflow,
            re.compile(
                r"^\s*push:",
                re.MULTILINE,
            ),
        )

        self.assertNotRegex(
            self.workflow,
            re.compile(
                r"^\s*pull_request:",
                re.MULTILINE,
            ),
        )

    def test_manual_publish_build_is_restricted_to_master(
        self,
    ) -> None:

        self.assertIn(
            (
                "if: github.event_name == 'release' || "
                "github.ref == 'refs/heads/master'"
            ),
            self.workflow,
        )

        self.assertIn(
            "workflow_dispatch:",
            self.workflow,
        )

        self.assertIn(
            "github.event_name == 'release'",
            self.workflow,
        )

        self.assertIn(
            "github.ref == 'refs/heads/master'",
            self.workflow,
        )

    def test_publish_job_uses_pypi_environment_and_oidc(
        self,
    ) -> None:

        self.assertRegex(
            self.workflow,
            re.compile(
                r"environment:\s+name: pypi",
                re.MULTILINE,
            ),
        )

        self.assertIn(
            "id-token: write",
            self.workflow,
        )

        self.assertIn(
            (
                "uses: "
                "pypa/gh-action-pypi-publish@release/v1"
            ),
            self.workflow,
        )

    def test_build_artifacts_are_passed_to_publish_job(
        self,
    ) -> None:

        self.assertIn(
            "run: python -m build",
            self.workflow,
        )

        self.assertIn(
            "uses: actions/upload-artifact@v4",
            self.workflow,
        )

        self.assertIn(
            "uses: actions/download-artifact@v5",
            self.workflow,
        )

        self.assertGreaterEqual(
            self.workflow.count(
                "name: python-distributions"
            ),
            2,
        )

        self.assertRegex(
            self.workflow,
            re.compile(
                r"publish:\s+.*?needs: build",
                re.DOTALL,
            ),
        )

    def test_workflow_references_no_stored_pypi_credentials(
        self,
    ) -> None:

        for forbidden in (
            "secrets.",
            "api_token",
            "api-token",
            "password:",
            "username:",
        ):
            with self.subTest(
                forbidden=forbidden
            ):
                self.assertNotIn(
                    forbidden,
                    self.normalized_workflow,
                )


if __name__ == "__main__":
    unittest.main()