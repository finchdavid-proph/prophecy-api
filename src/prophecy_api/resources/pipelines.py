"""Pipeline-run endpoints."""

from __future__ import annotations

import time
from typing import Any

from prophecy_api.exceptions import ProphecyAPIError
from prophecy_api.resources._base import Resource

TERMINAL_STATUSES: frozenset[str] = frozenset({"SUCCEEDED", "ERROR"})


class PipelinesResource(Resource):
    """Triggers and monitors pipeline runs.

    Endpoints:
        - ``POST /api/trigger/pipeline``
        - ``GET  /api/trigger/pipeline/{runId}``
    """

    def trigger(
        self,
        *,
        fabric_id: int,
        pipeline_name: str,
        project_id: str,
        parameters: dict[str, str] | None = None,
        branch: str | None = None,
        version: str | None = None,
        process_name: str | None = None,
    ) -> dict[str, Any]:
        """Kick off a pipeline run in a deployed project.

        Returns a dict with ``success``, ``runId``, and ``msg``.
        """
        payload: dict[str, Any] = {
            "fabricId": fabric_id,
            "pipelineName": pipeline_name,
            "projectId": project_id,
        }
        if parameters is not None:
            payload["parameters"] = parameters
        if branch is not None:
            payload["branch"] = branch
        if version is not None:
            payload["version"] = version
        if process_name is not None:
            payload["processName"] = process_name
        return self._http.request("POST", "/api/trigger/pipeline", json=payload)

    def get_run_status(self, run_id: str) -> dict[str, Any]:
        """Fetch run status by ``runId``.

        Returns a dict with ``runStatus`` (``RUNNING`` | ``SUCCEEDED`` |
        ``ERROR``), timestamps, and (when applicable) ``errorMessage``.
        """
        if not run_id:
            raise ValueError("run_id is required")
        return self._http.request("GET", f"/api/trigger/pipeline/{run_id}")

    def run_and_wait(
        self,
        *,
        fabric_id: int,
        pipeline_name: str,
        project_id: str,
        parameters: dict[str, str] | None = None,
        branch: str | None = None,
        version: str | None = None,
        process_name: str | None = None,
        poll_interval: float = 10.0,
        timeout: float = 1800.0,
    ) -> dict[str, Any]:
        """Trigger a pipeline and poll until it reaches a terminal state.

        Raises:
            ProphecyAPIError: if the run does not finish within ``timeout``
                seconds. Inspect the chained ``response_body`` for the last
                observed status.
        """
        triggered = self.trigger(
            fabric_id=fabric_id,
            pipeline_name=pipeline_name,
            project_id=project_id,
            parameters=parameters,
            branch=branch,
            version=version,
            process_name=process_name,
        )
        run_id = triggered["runId"]
        deadline = time.monotonic() + timeout
        while True:
            status = self.get_run_status(run_id)
            if status.get("runStatus") in TERMINAL_STATUSES:
                return status
            if time.monotonic() > deadline:
                raise ProphecyAPIError(
                    f"Run {run_id} did not finish within {timeout}s "
                    f"(last status: {status.get('runStatus')})",
                    response_body=status,
                )
            time.sleep(poll_interval)
