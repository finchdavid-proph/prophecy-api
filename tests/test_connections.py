from __future__ import annotations

import responses

from prophecy_api import ProphecyClient

CONNECTION_BODY = {
    "authType": "private_key",
    "dataset": "dev",
    "projectId": "dev-project-2222",
}


@responses.activate
def test_create(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/orchestration/fabric/1/connection",
        json={"success": True, "data": {"id": "c-1"}},
        status=200,
    )
    client.connections.create(
        1,
        name="bigquery_connection_1",
        kind="bigquery",
        properties=CONNECTION_BODY,
        is_default_warehouse_connection=False,
    )
    body = responses.calls[0].request.body
    assert b'"kind": "bigquery"' in body
    assert b'"isDefaultWarehouseConnection": false' in body


@responses.activate
def test_list(client: ProphecyClient, base_url: str):
    responses.add(
        responses.GET,
        f"{base_url}/api/orchestration/fabric/1/connection",
        json={"success": True, "data": {"Connections": [{"name": "c1"}, {"name": "c2"}]}},
        status=200,
    )
    result = client.connections.list(1)
    assert len(result["data"]["Connections"]) == 2


@responses.activate
def test_get_uses_name_segment(client: ProphecyClient, base_url: str):
    responses.add(
        responses.GET,
        f"{base_url}/api/orchestration/fabric/1/connection/name/c1",
        json={"success": True, "data": {"name": "c1"}},
        status=200,
    )
    result = client.connections.get(1, "c1")
    assert result["data"]["name"] == "c1"


@responses.activate
def test_update_uses_put_and_name_segment(client: ProphecyClient, base_url: str):
    responses.add(
        responses.PUT,
        f"{base_url}/api/orchestration/fabric/1/connection/name/c1",
        json={"success": True, "data": {"name": "c1"}},
        status=200,
    )
    client.connections.update(
        1,
        "c1",
        name="c1",
        kind="bigquery",
        is_default_warehouse_connection=True,
        properties=CONNECTION_BODY,
    )
    body = responses.calls[0].request.body
    assert b'"isDefaultWarehouseConnection": true' in body


@responses.activate
def test_delete(client: ProphecyClient, base_url: str):
    responses.add(
        responses.DELETE,
        f"{base_url}/api/orchestration/fabric/1/connection/name/c1",
        json={"success": True, "data": {"id": "c1"}},
        status=200,
    )
    result = client.connections.delete(1, "c1")
    assert result["data"]["id"] == "c1"
