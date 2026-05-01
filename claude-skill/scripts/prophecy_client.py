"""Prophecy REST API client (single-file copy for the apex-prophecy skill).

Mirrors the public ``prophecy-api`` package. Keep this file in sync with that
project's ``src/prophecy_api/`` modules.

Resource-namespaced usage:

    >>> client = ProphecyClient(base_url="https://app.prophecy.io", token="...")
    >>> client.pipelines.trigger(fabric_id=1, pipeline_name="x", project_id="36")
    >>> client.fabrics.create(name="staging", team_name="data", provider="databricks")
    >>> client.connections.list(fabric_id=1)
    >>> client.secrets.delete(fabric_id=1, secret_id=42)

Public package: https://github.com/finchdavid-proph/prophecy-api
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Exceptions --------------------------------------------------------------


class ProphecyError(Exception):
    """Base class for all errors raised by this client."""


class ProphecyHTTPError(ProphecyError):
    """Raised when an HTTP request fails (network, timeout, non-2xx status)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: dict[str, Any] | str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ProphecyAPIError(ProphecyError):
    """Raised when a Prophecy API call returns ``success: false``."""

    def __init__(self, message: str, *, response_body: dict[str, Any] | None = None):
        super().__init__(message)
        self.response_body = response_body or {}


# --- HTTP transport ----------------------------------------------------------

TERMINAL_STATUSES: frozenset[str] = frozenset({"SUCCEEDED", "ERROR"})

_RETRY_STATUS = (429, 500, 502, 503, 504)
_RETRY_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class _HTTPClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: int = 60,
        session: requests.Session | None = None,
        retry_total: int = 3,
        retry_backoff: float = 0.5,
    ):
        if not base_url:
            raise ValueError("base_url is required")
        if not token:
            raise ValueError("token is required")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or self._build_session(retry_total, retry_backoff)
        self.session.headers.update(
            {
                "X-AUTH-TOKEN": token,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "prophecy-api-python",
            }
        )

    @staticmethod
    def _build_session(retry_total: int, retry_backoff: float) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=retry_total,
            backoff_factor=retry_backoff,
            status_forcelist=_RETRY_STATUS,
            allowed_methods=_RETRY_METHODS,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def close(self) -> None:
        self.session.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.request(
                method, url, json=json, params=params, timeout=self.timeout
            )
        except requests.RequestException as e:
            raise ProphecyHTTPError(f"{method} {path} failed: {e}") from e

        body = self._decode_body(resp)

        if not resp.ok:
            msg = self._extract_error(body) or resp.reason or "HTTP error"
            raise ProphecyHTTPError(
                f"{method} {path} returned {resp.status_code}: {msg}",
                status_code=resp.status_code,
                response_body=body,
            )

        if isinstance(body, dict) and body.get("success") is False:
            raise ProphecyAPIError(
                self._extract_error(body) or f"{method} {path} returned success=false",
                response_body=body,
            )
        return body if isinstance(body, dict) else {"data": body}

    @staticmethod
    def _decode_body(resp: requests.Response) -> dict[str, Any] | list[Any] | str:
        try:
            return resp.json()
        except ValueError:
            return resp.text

    @staticmethod
    def _extract_error(body: Any) -> str | None:
        if not isinstance(body, dict):
            return None
        for key in ("msg", "message", "error"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
        return None


class _Resource:
    def __init__(self, http: _HTTPClient):
        self._http = http


# --- Pipelines ---------------------------------------------------------------


class PipelinesResource(_Resource):
    """``client.pipelines`` — trigger and monitor pipeline runs."""

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


# --- Projects ----------------------------------------------------------------


class ProjectsResource(_Resource):
    """``client.projects`` — deploys and data tests."""

    def deploy(
        self,
        *,
        project_name: str,
        fabric_name: str,
        git_tag: str,
        pipeline_configurations: dict[str, dict[str, str]] | None = None,
        project_configuration: dict[str, str] | None = None,
    ) -> dict[str, Any]:
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


# --- Fabrics -----------------------------------------------------------------

_FABRIC_BASE = "/api/orchestration/fabric"


class FabricsResource(_Resource):
    """``client.fabrics`` — create, get, update, delete fabrics."""

    def create(
        self,
        *,
        name: str,
        team_name: str,
        provider: str,
        description: str | None = None,
        dataplane_url: str | None = None,
        secret: dict[str, Any] | None = None,
        connection: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "teamName": team_name, "provider": provider}
        if description is not None:
            payload["description"] = description
        if dataplane_url is not None:
            payload["dataplaneUrl"] = dataplane_url
        if secret is not None:
            payload["secret"] = secret
        if connection is not None:
            payload["connection"] = connection
        return self._http.request("POST", _FABRIC_BASE, json=payload)

    def get(self, fabric_id: int | str) -> dict[str, Any]:
        return self._http.request("GET", f"{_FABRIC_BASE}/{fabric_id}")

    def update(
        self,
        fabric_id: int | str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        if name is None and description is None:
            raise ValueError("update() requires at least one of name or description")
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        return self._http.request("PUT", f"{_FABRIC_BASE}/{fabric_id}", json=payload)

    def delete(self, fabric_id: int | str) -> dict[str, Any]:
        return self._http.request("DELETE", f"{_FABRIC_BASE}/{fabric_id}")


# --- Connections -------------------------------------------------------------


def _connection_base(fabric_id: int | str) -> str:
    return f"/api/orchestration/fabric/{fabric_id}/connection"


class ConnectionsResource(_Resource):
    """``client.connections`` — manage connections inside a fabric.

    Connection ``properties`` are connector-specific (Databricks, Snowflake,
    BigQuery, Postgres, ...). Build the dict per the connector reference at
    https://docs.prophecy.ai/api-reference/connections/properties — this
    client forwards it as-is.
    """

    def create(
        self,
        fabric_id: int | str,
        *,
        name: str,
        kind: str,
        properties: dict[str, Any],
        is_default_warehouse_connection: bool | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "kind": kind, "properties": properties}
        if is_default_warehouse_connection is not None:
            payload["isDefaultWarehouseConnection"] = is_default_warehouse_connection
        return self._http.request("POST", _connection_base(fabric_id), json=payload)

    def list(self, fabric_id: int | str) -> dict[str, Any]:
        return self._http.request("GET", _connection_base(fabric_id))

    def get(self, fabric_id: int | str, connection_name: str) -> dict[str, Any]:
        return self._http.request(
            "GET", f"{_connection_base(fabric_id)}/name/{connection_name}"
        )

    def update(
        self,
        fabric_id: int | str,
        connection_name: str,
        *,
        name: str,
        kind: str,
        is_default_warehouse_connection: bool,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "name": name,
            "kind": kind,
            "isDefaultWarehouseConnection": is_default_warehouse_connection,
            "properties": properties,
        }
        return self._http.request(
            "PUT", f"{_connection_base(fabric_id)}/name/{connection_name}", json=payload
        )

    def delete(self, fabric_id: int | str, connection_name: str) -> dict[str, Any]:
        return self._http.request(
            "DELETE", f"{_connection_base(fabric_id)}/name/{connection_name}"
        )


# --- Secrets -----------------------------------------------------------------


def _secret_base(fabric_id: int | str) -> str:
    return f"/api/orchestration/fabric/{fabric_id}/secret"


class SecretsResource(_Resource):
    """``client.secrets`` — manage secrets inside a fabric.

    ``sub_kind`` is one of: ``text``, ``binary``, ``username_password``,
    ``m2m_oauth``. ``properties`` shape varies by sub_kind — see
    https://docs.prophecy.ai/api-reference/secrets/properties.
    """

    def create(
        self,
        fabric_id: int | str,
        *,
        kind: str,
        sub_kind: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {"kind": kind, "subKind": sub_kind, "properties": properties}
        return self._http.request("POST", _secret_base(fabric_id), json=payload)

    def list(self, fabric_id: int | str) -> dict[str, Any]:
        return self._http.request("GET", _secret_base(fabric_id))

    def get(self, fabric_id: int | str, secret_id: int | str) -> dict[str, Any]:
        return self._http.request("GET", f"{_secret_base(fabric_id)}/id/{secret_id}")

    def update(
        self,
        fabric_id: int | str,
        secret_id: int | str,
        *,
        kind: str,
        sub_kind: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {"kind": kind, "subKind": sub_kind, "properties": properties}
        return self._http.request(
            "PUT", f"{_secret_base(fabric_id)}/id/{secret_id}", json=payload
        )

    def delete(self, fabric_id: int | str, secret_id: int | str) -> dict[str, Any]:
        return self._http.request("DELETE", f"{_secret_base(fabric_id)}/id/{secret_id}")


# --- Top-level client --------------------------------------------------------


class ProphecyClient:
    """Client for the Prophecy REST API.

    Args:
        base_url: Your Prophecy instance URL (e.g. ``https://app.prophecy.io``
            or ``https://g36b-sbox.sap.cloud.prophecy.ai``).
        token: A Personal Access Token from Settings → Access Tokens.
        timeout: Per-request timeout in seconds.
        session: Optional pre-built ``requests.Session``.
        retry_total: Max retry attempts for transient errors. Set 0 to disable.
        retry_backoff: Exponential backoff factor between retries.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: int = 60,
        session: requests.Session | None = None,
        retry_total: int = 3,
        retry_backoff: float = 0.5,
    ):
        self._http = _HTTPClient(
            base_url=base_url,
            token=token,
            timeout=timeout,
            session=session,
            retry_total=retry_total,
            retry_backoff=retry_backoff,
        )
        self.pipelines = PipelinesResource(self._http)
        self.projects = ProjectsResource(self._http)
        self.fabrics = FabricsResource(self._http)
        self.connections = ConnectionsResource(self._http)
        self.secrets = SecretsResource(self._http)

    @classmethod
    def from_env(cls, *, timeout: int = 60) -> ProphecyClient:
        try:
            base_url = os.environ["PROPHECY_BASE_URL"]
            token = os.environ["PROPHECY_TOKEN"]
        except KeyError as missing:
            raise ProphecyError(
                f"Missing environment variable: {missing.args[0]}. "
                "Set PROPHECY_BASE_URL and PROPHECY_TOKEN."
            ) from missing
        return cls(base_url=base_url, token=token, timeout=timeout)

    @property
    def base_url(self) -> str:
        return self._http.base_url

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> ProphecyClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
