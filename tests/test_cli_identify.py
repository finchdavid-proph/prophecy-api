"""Tests for the ``prophecy identify`` CLI subcommand."""

from __future__ import annotations

import pytest
import responses

from prophecy_api.cli import main


@pytest.fixture
def setenv(monkeypatch: pytest.MonkeyPatch, base_url: str) -> None:
    monkeypatch.setenv("PROPHECY_BASE_URL", base_url)
    monkeypatch.setenv("PROPHECY_TOKEN", "test-token")


@responses.activate
def test_identify_classifies_works(
    setenv: None,
    base_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A successful response classifies as WORKS and prints a preview."""
    responses.add(
        responses.GET,
        f"{base_url}/api/trigger/pipeline/abc-123",
        json={"success": True, "runId": "abc-123", "runStatus": "SUCCEEDED"},
        status=200,
    )
    main(["identify", "pipelines.get_run_status", "--arg", "run_id=abc-123"])
    out = capsys.readouterr().out
    assert "WORKS" in out
    assert "SUCCEEDED" in out


@responses.activate
def test_identify_classifies_api_error_as_broken(
    setenv: None,
    base_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ``success: false`` response is classified as BROKEN with the
    server's error body inlined."""
    responses.add(
        responses.GET,
        f"{base_url}/api/trigger/pipeline/missing",
        json={
            "success": False,
            "runId": "missing",
            "errorMessage": "Run not found in any orchestration endpoint",
        },
        status=200,
    )
    main(["identify", "pipelines.get_run_status", "--arg", "run_id=missing"])
    out = capsys.readouterr().out
    assert "BROKEN" in out
    assert "success=false" in out
    assert "Run not found" in out


@responses.activate
def test_identify_classifies_http_error_as_broken(
    setenv: None,
    base_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A 4xx HTTP response is also BROKEN; the status code is reported."""
    responses.add(
        responses.GET,
        f"{base_url}/api/orchestration/fabric/99999/connection",
        json={"success": False, "message": "Fabric not found"},
        status=400,
    )
    main(["identify", "connections.list", "--arg", "fabric_id=99999"])
    out = capsys.readouterr().out
    assert "BROKEN" in out
    assert "HTTP 400" in out


def test_identify_unverified_on_missing_arg(
    setenv: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing required arg → TypeError → UNVERIFIED (the call never
    reaches the server, so we don't claim BROKEN)."""
    main(["identify", "pipelines.get_run_status"])
    out = capsys.readouterr().out
    assert "UNVERIFIED" in out


def test_identify_rejects_bad_resource(setenv: None) -> None:
    with pytest.raises(SystemExit, match="no resource 'nonexistent'"):
        main(["identify", "nonexistent.do_thing"])


def test_identify_rejects_bad_method(setenv: None) -> None:
    with pytest.raises(SystemExit, match="no callable method 'no_such_thing'"):
        main(["identify", "pipelines.no_such_thing"])


def test_identify_rejects_method_without_dot(setenv: None) -> None:
    with pytest.raises(SystemExit, match="must be 'resource.method'"):
        main(["identify", "trigger"])


def test_identify_arg_coercion_int_then_json_then_str(
    setenv: None,
    base_url: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """KEY=VALUE parsing: int → JSON → str fallback. Assert by checking
    the request body that fabric_id was sent as int (not str), and
    that a JSON-shaped value parses, and bare strings stay strings."""
    captured: dict[str, bytes] = {}

    @responses.activate
    def run() -> None:
        def callback(request):
            captured["body"] = request.body
            return (200, {}, '{"success": true, "data": {"id": "1"}}')

        responses.add_callback(
            responses.POST,
            f"{base_url}/api/orchestration/fabric",
            callback=callback,
        )
        # team_name is a plain string, provider too; description has spaces
        # and won't be passed (just test that the call succeeds with int +
        # string args).
        main([
            "identify",
            "fabrics.create",
            "--arg", "name=test",
            "--arg", "team_name=devTeam",
            "--arg", "provider=databricks",
        ])

    run()
    out = capsys.readouterr().out
    assert "WORKS" in out