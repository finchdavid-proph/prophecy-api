from __future__ import annotations

import responses

from prophecy_api import ProphecyClient

SECRET_PROPS = {"name": "databricks-pat", "value": "pat-value"}


@responses.activate
def test_create(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/orchestration/fabric/1/secret",
        json={"success": True, "data": {"id": "4657"}},
        status=200,
    )
    client.secrets.create(1, kind="prophecy", sub_kind="text", properties=SECRET_PROPS)
    body = responses.calls[0].request.body
    assert b'"kind": "prophecy"' in body
    assert b'"subKind": "text"' in body


@responses.activate
def test_list(client: ProphecyClient, base_url: str):
    responses.add(
        responses.GET,
        f"{base_url}/api/orchestration/fabric/1/secret",
        json={"success": True, "data": {"secrets": [{"properties": {"id": "1"}}]}},
        status=200,
    )
    result = client.secrets.list(1)
    assert len(result["data"]["secrets"]) == 1


@responses.activate
def test_get_uses_id_segment(client: ProphecyClient, base_url: str):
    responses.add(
        responses.GET,
        f"{base_url}/api/orchestration/fabric/1/secret/id/4657",
        json={"success": True, "data": {"properties": {"id": "4657"}}},
        status=200,
    )
    client.secrets.get(1, 4657)


@responses.activate
def test_update_uses_put_and_id_segment(client: ProphecyClient, base_url: str):
    responses.add(
        responses.PUT,
        f"{base_url}/api/orchestration/fabric/1/secret/id/4657",
        json={"success": True, "data": {"id": "4657"}},
        status=200,
    )
    client.secrets.update(
        1, 4657, kind="prophecy", sub_kind="text", properties=SECRET_PROPS
    )


@responses.activate
def test_delete(client: ProphecyClient, base_url: str):
    responses.add(
        responses.DELETE,
        f"{base_url}/api/orchestration/fabric/1/secret/id/4656",
        json={"success": True, "data": {"id": "4656"}},
        status=200,
    )
    result = client.secrets.delete(1, 4656)
    assert result["data"]["id"] == "4656"
