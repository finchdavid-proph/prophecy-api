from __future__ import annotations

import responses

from prophecy_api import ProphecyClient


@responses.activate
def test_deploy(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/deploy/project",
        json={"success": True, "deploymentId": "d-1"},
        status=200,
    )
    result = client.projects.deploy(
        project_name="CustomerAnalytics",
        fabric_name="prod",
        git_tag="CustomerAnalytics/2.1",
        pipeline_configurations={"sales_report": {"period": "monthly"}},
    )
    assert result["deploymentId"] == "d-1"
    body = responses.calls[0].request.body
    assert b'"gitTag": "CustomerAnalytics/2.1"' in body
    assert b'"pipelineConfigurations"' in body


@responses.activate
def test_deploy_omits_optional_fields(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/deploy/project",
        json={"success": True, "deploymentId": "d-2"},
        status=200,
    )
    client.projects.deploy(project_name="P", fabric_name="F", git_tag="P/1")
    body = responses.calls[0].request.body
    assert b"pipelineConfigurations" not in body
    assert b"projectConfiguration" not in body


@responses.activate
def test_run_data_tests(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/orchestration/tests/run",
        json={"success": True, "results": []},
        status=200,
    )
    tests = [
        {
            "source": "hospital_patients",
            "table": "patient_details",
            "columnTests": [{"name": "age", "tests": [{"name": "not_null"}]}],
        }
    ]
    result = client.projects.run_data_tests(fabric_id=4251, project_id="2419", tests=tests)
    assert result["success"] is True
    body = responses.calls[0].request.body
    assert b'"fabricId": 4251' in body
    assert b'"projectId": "2419"' in body
    assert b'"tests"' in body


@responses.activate
def test_run_data_tests_model_call(client: ProphecyClient, base_url: str):
    responses.add(
        responses.POST,
        f"{base_url}/api/orchestration/tests/run",
        json={"success": True},
        status=200,
    )
    client.projects.run_data_tests(
        fabric_id=4251,
        project_id="2419",
        tests=[{}],
        model_name="risk_model",
    )
    body = responses.calls[0].request.body
    assert b'"modelName": "risk_model"' in body
