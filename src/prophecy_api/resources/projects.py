"""Project deploy and data-test endpoints."""

from __future__ import annotations

from typing import Any

from prophecy_api.resources._base import Resource


class ProjectsResource(Resource):
    """Deploys projects and runs project-scoped data tests.

    Endpoints:
        - ``POST /api/deploy/project``
        - ``POST /api/orchestration/tests/run``
    """

    def deploy(
        self,
        *,
        project_name: str,
        fabric_name: str,
        git_tag: str,
        pipeline_configurations: dict[str, dict[str, str]] | None = None,
        project_configuration: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Deploy a project to a fabric. ``git_tag`` is ``{projectName}/{version}``."""
        payload: dict[str, Any] = {
            "projectName": project_name,
            "fabricName": fabric_name,
            "gitTag": git_tag,
        }
        if pipeline_configurations is not None:
            payload["pipelineConfigurations"] = pipeline_configurations
        if project_configuration is not None:
            payload["projectConfiguration"] = project_configuration
        return self._http.request("POST", "/api/deploy/project", json=payload)

    def run_data_tests(
        self,
        *,
        fabric_id: int,
        project_id: str,
        tests: list[dict[str, Any]],
        branch: str | None = None,
        version: str | None = None,
        model_name: str | None = None,
    ) -> dict[str, Any]:
        """Execute project data tests.

        Pass ``model_name`` for model tests; otherwise ``tests`` carries
        column / table / project test specs.
        """
        payload: dict[str, Any] = {
            "fabricId": fabric_id,
            "projectId": project_id,
            "tests": tests,
        }
        if branch is not None:
            payload["branch"] = branch
        if version is not None:
            payload["version"] = version
        if model_name is not None:
            payload["modelName"] = model_name
        return self._http.request("POST", "/api/orchestration/tests/run", json=payload)
