"""Construction and config tests for ProphecyClient."""

from __future__ import annotations

import pytest

from prophecy_api import ProphecyClient, ProphecyError
from prophecy_api.resources import (
    ConnectionsResource,
    FabricsResource,
    PipelinesResource,
    ProjectsResource,
    SecretsResource,
)

BASE_URL = "https://app.prophecy.io"
TOKEN = "test-token"


def test_requires_base_url_and_token():
    with pytest.raises(ValueError):
        ProphecyClient(base_url="", token=TOKEN)
    with pytest.raises(ValueError):
        ProphecyClient(base_url=BASE_URL, token="")


def test_resource_accessors_are_wired():
    c = ProphecyClient(base_url=BASE_URL, token=TOKEN)
    assert isinstance(c.pipelines, PipelinesResource)
    assert isinstance(c.projects, ProjectsResource)
    assert isinstance(c.fabrics, FabricsResource)
    assert isinstance(c.connections, ConnectionsResource)
    assert isinstance(c.secrets, SecretsResource)
    # All resources share one HTTP client
    assert c.pipelines._http is c.fabrics._http


def test_base_url_strips_trailing_slash():
    c = ProphecyClient(base_url=f"{BASE_URL}/", token=TOKEN)
    assert c.base_url == BASE_URL


def test_from_env_missing_raises(monkeypatch):
    monkeypatch.delenv("PROPHECY_BASE_URL", raising=False)
    monkeypatch.delenv("PROPHECY_TOKEN", raising=False)
    with pytest.raises(ProphecyError, match="PROPHECY_BASE_URL"):
        ProphecyClient.from_env()


def test_from_env_builds_client(monkeypatch):
    monkeypatch.setenv("PROPHECY_BASE_URL", BASE_URL)
    monkeypatch.setenv("PROPHECY_TOKEN", TOKEN)
    c = ProphecyClient.from_env()
    assert c.base_url == BASE_URL


def test_context_manager_closes_session():
    with ProphecyClient(base_url=BASE_URL, token=TOKEN) as c:
        assert c.base_url == BASE_URL
    # Re-using the closed session is an error in requests; we just check no exception above.


def test_auth_header_set():
    c = ProphecyClient(base_url=BASE_URL, token=TOKEN)
    assert c._http.session.headers["X-AUTH-TOKEN"] == TOKEN
    assert c._http.session.headers["Content-Type"] == "application/json"
