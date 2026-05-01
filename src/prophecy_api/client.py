"""Top-level Prophecy API client.

Provides resource-namespaced accessors:

>>> client = ProphecyClient(base_url="https://app.prophecy.io", token="...")
>>> client.pipelines.trigger(fabric_id=1, pipeline_name="x", project_id="36")
>>> client.fabrics.create(name="staging", team_name="data", provider="databricks")
>>> client.connections.list(fabric_id=1)
>>> client.secrets.delete(fabric_id=1, secret_id=42)

All resources share a single :class:`HTTPClient` (one ``requests.Session``).
"""

from __future__ import annotations

import os

import requests

from prophecy_api._http import HTTPClient
from prophecy_api.exceptions import ProphecyError
from prophecy_api.resources import (
    ConnectionsResource,
    FabricsResource,
    PipelinesResource,
    ProjectsResource,
    SecretsResource,
)


class ProphecyClient:
    """Client for the Prophecy REST API.

    Args:
        base_url: Your Prophecy instance URL (e.g. ``https://app.prophecy.io``
            or ``https://g36b-sbox.sap.cloud.prophecy.ai``). Trailing slashes
            are trimmed.
        token: A Personal Access Token from Settings → Access Tokens.
        timeout: Per-request timeout in seconds.
        session: Optional pre-built ``requests.Session`` (e.g. for tests or
            to inject a custom adapter).
        retry_total: Max retry attempts for transient errors (5xx, 429).
            Set to 0 to disable retry.
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
        self._http = HTTPClient(
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
        """Build a client from ``PROPHECY_BASE_URL`` and ``PROPHECY_TOKEN``."""
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
