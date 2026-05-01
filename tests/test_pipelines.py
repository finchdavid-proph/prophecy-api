from __future__ import annotations

import pytest
import responses

from prophecy_api import ProphecyAPIError, ProphecyClient, ProphecyHTTPError


@responses.activate
def test_trigger_sends_full_payload(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/trigger/pipeline",
        json={"success": True, "runId": "abc-123", "msg": "ok"},
        status=200,
    )

    result = client.pipelines.trigger(
        fabric_id=1,
        pipeline_name="api_test",
        project_id="36",
        parameters={"k": "v"},
        version="2",
    )
    assert result["runId"] == "abc-123"

    body = responses.calls[0].request.body
    assert b'"fabricId": 1' in body
    assert b'"pipelineName": "api_test"' in body
    assert b'"projectId": "36"' in body
    assert b'"parameters"' in body
    assert b'"version": "2"' in body
    assert b"branch" not in body
    assert b"processName" not in body


@responses.activate
def test_trigger_raises_api_error_on_success_false(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/trigger/pipeline",
        json={"success": False, "msg": "Fabric `2290` not found"},
        status=200,
    )
    with pytest.raises(ProphecyAPIError, match="Fabric `2290` not found"):
        client.pipelines.trigger(fabric_id=2290, pipeline_name="x", project_id="y")


@responses.activate
def test_trigger_raises_http_error_on_4xx(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/trigger/pipeline",
        json={"msg": "Unauthorized"},
        status=401,
    )
    with pytest.raises(ProphecyHTTPError) as exc:
        client.pipelines.trigger(fabric_id=1, pipeline_name="x", project_id="y")
    assert exc.value.status_code == 401
    assert "Unauthorized" in str(exc.value)


@responses.activate
def test_get_run_status(client: ProphecyClient, base_url: str):
    run_id = "MDAw-xZGYzYzc3=="
    responses.add(
        responses.GET,
        f"{base_url}/api/trigger/pipeline/{run_id}",
        json={"success": True, "runId": run_id, "runStatus": "SUCCEEDED"},
        status=200,
    )
    result = client.pipelines.get_run_status(run_id)
    assert result["runStatus"] == "SUCCEEDED"


def test_get_run_status_requires_run_id(client: ProphecyClient):
    with pytest.raises(ValueError):
        client.pipelines.get_run_status("")


@responses.activate
def test_run_and_wait_polls_to_terminal(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/trigger/pipeline",
        json={"success": True, "runId": "r1"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_url}/api/trigger/pipeline/r1",
        json={"runStatus": "RUNNING"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_url}/api/trigger/pipeline/r1",
        json={"runStatus": "SUCCEEDED"},
        status=200,
    )

    result = client.pipelines.run_and_wait(
        fabric_id=1,
        pipeline_name="p",
        project_id="36",
        poll_interval=0,
        timeout=10,
    )
    assert result["runStatus"] == "SUCCEEDED"


@responses.activate
def test_run_and_wait_times_out(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/trigger/pipeline",
        json={"success": True, "runId": "r1"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base_url}/api/trigger/pipeline/r1",
        json={"runStatus": "RUNNING"},
        status=200,
    )
    with pytest.raises(ProphecyAPIError, match="did not finish"):
        client.pipelines.run_and_wait(
            fabric_id=1,
            pipeline_name="p",
            project_id="36",
            poll_interval=0,
            timeout=0,
        )
