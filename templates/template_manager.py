"""
==================================================
ForgePy
Template Manager
==================================================
"""

from templates.app_template import get_app
from templates.changelog_template import get_changelog
from templates.env_template import (
    get_env,
    get_env_example,
)
from templates.gitignore_template import get_gitignore
from templates.license_template import get_license
from templates.pyproject_template import get_pyproject
from templates.readme_template import get_readme
from templates.requirements_template import get_requirements


class TemplateManager:

    def get_app(
        self,
        project_name: str,
    ) -> str:
        return get_app(project_name)

    def get_gitignore(self) -> str:
        return get_gitignore()

    def get_readme(
        self,
        project_name: str,
    ) -> str:
        return get_readme(project_name)

    def get_requirements(self) -> str:
        return get_requirements()

    def get_license(self) -> str:
        return get_license()

    def get_changelog(self) -> str:
        return get_changelog()

    def get_env(self) -> str:
        return get_env()

    def get_env_example(self) -> str:
        return get_env_example()

    def get_pyproject(
        self,
        project_name: str,
    ) -> str:
        return get_pyproject(project_name)