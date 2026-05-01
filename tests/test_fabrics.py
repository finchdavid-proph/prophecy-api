from __future__ import annotations

import pytest
import responses

from prophecy_api import ProphecyClient


@responses.activate
def test_create(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/orchestration/fabric",
        json={"success": True, "data": {"id": "10740"}},
        status=200,
    )
    result = client.fabrics.create(
        name="API_Generated_Fabric",
        team_name="devTeam",
        provider="databricks",
        description="hello",
    )
    assert result["data"]["id"] == "10740"
    body = responses.calls[0].request.body
    assert b'"teamName": "devTeam"' in body
    assert b'"provider": "databricks"' in body
    assert b'"description": "hello"' in body


@responses.activate
def test_get(client: ProphecyClient, base_url: str):
    responses.add(
        responses.GET,
        f"{base_url}/api/orchestration/fabric/10740",
        json={"success": True, "data": {"fabricID": "10740", "name": "x", "teamID": "1"}},
        status=200,
    )
    result = client.fabrics.get(10740)
    assert result["data"]["fabricID"] == "10740"


@responses.activate
def test_update_uses_put_and_only_provided_fields(client: ProphecyClient, base_url: str):
    responses.add(
        responses.PUT,
        f"{base_url}/api/orchestration/fabric/10740",
        json={"success": True, "data": {"id": "10740"}},
        status=200,
    )
    client.fabrics.update(10740, name="renamed")
    body = responses.calls[0].request.body
    assert b'"name": "renamed"' in body
    assert b"description" not in body


def test_update_requires_some_field(client: ProphecyClient):
    with pytest.raises(ValueError, match="at least one of name or description"):
        client.fabrics.update(10740)


@responses.activate
def test_delete(client: ProphecyClient, base_url: str):
    responses.add(
        responses.DELETE,
        f"{base_url}/api/orchestration/fabric/10743",
        json={"success": True, "data": {"id": "10743"}},
        status=200,
    )
    result = client.fabrics.delete(10743)
    assert result["data"]["id"] == "10743"
