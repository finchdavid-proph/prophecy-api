"""Lower-level transport tests."""

from __future__ import annotations

import pytest
import responses

from prophecy_api import ProphecyAPIError, ProphecyClient, ProphecyHTTPError


@responses.activate
def test_http_error_includes_response_body(client: ProphecyClient, base_url: str):
    responses.add(
        responses.GET,
        f"{base_url}/api/trigger/pipeline/r1",
        json={"msg": "boom"},
        status=500,
    )
    with pytest.raises(ProphecyHTTPError) as exc:
        client.pipelines.get_run_status("r1")
    assert exc.value.status_code == 500
    assert exc.value.response_body == {"msg": "boom"}


@responses.activate
def test_api_error_preserves_response_body(client: ProphecyClient, base_url: str):
    body = {"success": False, "msg": "Fabric not found"}
    responses.add(
        responses.POST,
        f"{base_url}/api/trigger/pipeline",
        json=body,
        status=200,
    )
    with pytest.raises(ProphecyAPIError) as exc:
        client.pipelines.trigger(fabric_id=1, pipeline_name="p", project_id="x")
    assert exc.value.response_body == body


@responses.activate
def test_non_json_error_falls_back_to_text(client: ProphecyClient, base_url: str):
    responses.add(
        responses.GET,
        f"{base_url}/api/trigger/pipeline/r1",
        body="<html>oops</html>",
        status=502,
        content_type="text/html",
    )
    with pytest.raises(ProphecyHTTPError) as exc:
        client.pipelines.get_run_status("r1")
    assert exc.value.status_code == 502
