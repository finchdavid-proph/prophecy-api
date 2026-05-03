"""Hierarchical ``prophecy`` console entry point.

Layout:

  prophecy pipeline    trigger | status | wait
  prophecy project     deploy | run-tests
  prophecy fabric      create | get | update | delete
  prophecy connection  create | list | get | update | delete
  prophecy secret      create | list | get | update | delete
  prophecy identify    live-probe a method, classify outcome
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from prophecy_api.client import ProphecyClient
from prophecy_api.exceptions import (
    ProphecyAPIError,
    ProphecyError,
    ProphecyHTTPError,
)

# --- helpers -----------------------------------------------------------------


def _parse_kv(items: list[str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--param expects KEY=VALUE, got: {item!r}")
        key, _, value = item.partition("=")
        out[key] = value
    return out


def _load_json(path: str | None) -> Any:
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _emit(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def _build_client(args: argparse.Namespace) -> ProphecyClient:
    if args.base_url and args.token:
        return ProphecyClient(base_url=args.base_url, token=args.token, timeout=args.timeout)
    return ProphecyClient.from_env(timeout=args.timeout)


def _add_global_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--base-url", help="Override PROPHECY_BASE_URL")
    p.add_argument("--token", help="Override PROPHECY_TOKEN")
    p.add_argument("--timeout", type=int, default=60, help="Per-request timeout (seconds)")


# --- command handlers --------------------------------------------------------


def _cmd_pipeline_trigger(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        result = c.pipelines.trigger(
            fabric_id=args.fabric_id,
            pipeline_name=args.pipeline,
            project_id=args.project_id,
            parameters=_parse_kv(args.param) or None,
            branch=args.branch,
            version=args.version,
            process_name=args.process_name,
        )
    _emit(result)


def _cmd_pipeline_status(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        result = c.pipelines.get_run_status(args.run_id)
    _emit(result)


def _cmd_pipeline_wait(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        result = c.pipelines.run_and_wait(
            fabric_id=args.fabric_id,
            pipeline_name=args.pipeline,
            project_id=args.project_id,
            parameters=_parse_kv(args.param) or None,
            branch=args.branch,
            version=args.version,
            process_name=args.process_name,
            poll_interval=args.poll_interval,
            timeout=args.timeout_seconds,
        )
    _emit(result)
    if result.get("runStatus") == "ERROR":
        sys.exit(1)


def _cmd_project_deploy(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        result = c.projects.deploy(
            project_name=args.project,
            fabric_name=args.fabric,
            git_tag=args.git_tag,
            pipeline_configurations=_load_json(args.pipeline_configs),
            project_configuration=_load_json(args.project_config),
        )
    _emit(result)


def _cmd_project_run_tests(args: argparse.Namespace) -> None:
    tests = _load_json(args.tests_file)
    with _build_client(args) as c:
        result = c.projects.run_data_tests(
            fabric_id=args.fabric_id,
            project_id=args.project_id,
            tests=tests,
            branch=args.branch,
            version=args.version,
            model_name=args.model_name,
        )
    _emit(result)


def _cmd_fabric_create(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        result = c.fabrics.create(
            name=args.name,
            team_name=args.team_name,
            provider=args.provider,
            description=args.description,
            dataplane_url=args.dataplane_url,
            secret=_load_json(args.secret_body),
            connection=_load_json(args.connection_body),
        )
    _emit(result)


def _cmd_fabric_get(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        _emit(c.fabrics.get(args.fabric_id))


def _cmd_fabric_update(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        _emit(c.fabrics.update(args.fabric_id, name=args.name, description=args.description))


def _cmd_fabric_delete(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        _emit(c.fabrics.delete(args.fabric_id))


def _cmd_connection_create(args: argparse.Namespace) -> None:
    properties = _load_json(args.properties)
    if properties is None:
        raise SystemExit("--properties is required (path to JSON file)")
    with _build_client(args) as c:
        result = c.connections.create(
            args.fabric_id,
            name=args.name,
            kind=args.kind,
            properties=properties,
            is_default_warehouse_connection=args.default_warehouse,
        )
    _emit(result)


def _cmd_connection_list(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        _emit(c.connections.list(args.fabric_id))


def _cmd_connection_get(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        _emit(c.connections.get(args.fabric_id, args.connection_name))


def _cmd_connection_update(args: argparse.Namespace) -> None:
    properties = _load_json(args.properties)
    if properties is None:
        raise SystemExit("--properties is required (path to JSON file)")
    with _build_client(args) as c:
        result = c.connections.update(
            args.fabric_id,
            args.connection_name,
            name=args.name,
            kind=args.kind,
            is_default_warehouse_connection=args.default_warehouse,
            properties=properties,
        )
    _emit(result)


def _cmd_connection_delete(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        _emit(c.connections.delete(args.fabric_id, args.connection_name))


def _cmd_secret_create(args: argparse.Namespace) -> None:
    properties = _load_json(args.properties)
    if properties is None:
        raise SystemExit("--properties is required (path to JSON file)")
    with _build_client(args) as c:
        result = c.secrets.create(
            args.fabric_id,
            kind=args.kind,
            sub_kind=args.sub_kind,
            properties=properties,
        )
    _emit(result)


def _cmd_secret_list(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        _emit(c.secrets.list(args.fabric_id))


def _cmd_secret_get(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        _emit(c.secrets.get(args.fabric_id, args.secret_id))


def _cmd_secret_update(args: argparse.Namespace) -> None:
    properties = _load_json(args.properties)
    if properties is None:
        raise SystemExit("--properties is required (path to JSON file)")
    with _build_client(args) as c:
        result = c.secrets.update(
            args.fabric_id,
            args.secret_id,
            kind=args.kind,
            sub_kind=args.sub_kind,
            properties=properties,
        )
    _emit(result)


def _cmd_secret_delete(args: argparse.Namespace) -> None:
    with _build_client(args) as c:
        _emit(c.secrets.delete(args.fabric_id, args.secret_id))


# --- identify (live-probe a method against the configured instance) ---------


def _resolve_method(client: ProphecyClient, dotted: str):
    """Resolve a ``resource.method`` path on the client. Raises
    ``SystemExit`` with a clear message if either part is wrong."""
    if "." not in dotted:
        raise SystemExit(
            f"identify: METHOD must be 'resource.method', got {dotted!r}. "
            f"Available resources: pipelines, projects, fabrics, connections, secrets."
        )
    resource_name, _, method_name = dotted.partition(".")
    resource = getattr(client, resource_name, None)
    if resource is None:
        raise SystemExit(
            f"identify: no resource {resource_name!r} on the client. "
            f"Available: pipelines, projects, fabrics, connections, secrets."
        )
    method = getattr(resource, method_name, None)
    if method is None or not callable(method):
        public = sorted(
            n for n in dir(resource)
            if not n.startswith("_") and callable(getattr(resource, n))
        )
        raise SystemExit(
            f"identify: {resource_name} has no callable method {method_name!r}. "
            f"Available: {', '.join(public)}"
        )
    return method


def _coerce_arg(raw: str) -> Any:
    """Best-effort coercion: try int, then JSON, then fall back to string."""
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw


def _cmd_identify(args: argparse.Namespace) -> None:
    """Live-probe a method against the configured instance and classify
    the outcome (WORKS / BROKEN / UNVERIFIED).

    Useful for verifying a Dedicated SaaS endpoint matches the public
    OpenAPI spec, sanity-checking auth on a new token, or scoping a
    new endpoint that isn't yet documented.
    """
    kwargs: dict[str, Any] = {}
    for item in args.arg or []:
        if "=" not in item:
            raise SystemExit(f"--arg expects KEY=VALUE, got: {item!r}")
        key, _, value = item.partition("=")
        kwargs[key] = _coerce_arg(value)

    client = _build_client(args)
    try:
        with client:
            method = _resolve_method(client, args.method)
            print(f"calling client.{args.method}(**{kwargs}) on {client.base_url}")
            try:
                result = method(**kwargs)
            except ProphecyAPIError as e:
                print(f"→ Status: BROKEN — server returned success=false: {e}")
                if e.response_body:
                    print(f"  body: {json.dumps(e.response_body, default=str)[:300]}")
                return
            except ProphecyHTTPError as e:
                print(f"→ Status: BROKEN — HTTP {e.status_code}: {e}")
                if e.response_body:
                    body_str = (
                        json.dumps(e.response_body, default=str)
                        if isinstance(e.response_body, dict)
                        else str(e.response_body)
                    )
                    print(f"  body: {body_str[:300]}")
                return
            except TypeError as e:
                print(f"→ Status: UNVERIFIED — bad args (TypeError): {e}")
                return
            except Exception as e:  # noqa: BLE001
                print(f"→ Status: UNVERIFIED — {type(e).__name__}: {e}")
                return

            print("→ Status: WORKS")
            preview = json.dumps(result, default=str)
            print(f"  preview: {preview[:300]}")
    except ProphecyError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)


# --- parser builder ----------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prophecy", description="Prophecy REST API client.")
    top = parser.add_subparsers(dest="resource", required=True)

    # pipeline
    pipeline = top.add_parser("pipeline", help="Pipeline runs")
    pipeline_sub = pipeline.add_subparsers(dest="command", required=True)

    p = pipeline_sub.add_parser("trigger", help="Trigger a pipeline run")
    _add_global_flags(p)
    p.add_argument("--fabric-id", type=int, required=True)
    p.add_argument("--pipeline", required=True)
    p.add_argument("--project-id", required=True)
    p.add_argument("--param", action="append", help="KEY=VALUE (repeatable)")
    p.add_argument("--branch")
    p.add_argument("--version")
    p.add_argument("--process-name", help="Stop the pipeline at this gem")
    p.set_defaults(func=_cmd_pipeline_trigger)

    p = pipeline_sub.add_parser("status", help="Get pipeline run status")
    _add_global_flags(p)
    p.add_argument("run_id")
    p.set_defaults(func=_cmd_pipeline_status)

    p = pipeline_sub.add_parser("wait", help="Trigger a pipeline and poll until it finishes")
    _add_global_flags(p)
    p.add_argument("--fabric-id", type=int, required=True)
    p.add_argument("--pipeline", required=True)
    p.add_argument("--project-id", required=True)
    p.add_argument("--param", action="append")
    p.add_argument("--branch")
    p.add_argument("--version")
    p.add_argument("--process-name")
    p.add_argument("--poll-interval", type=float, default=10.0)
    p.add_argument("--timeout-seconds", type=float, default=1800.0)
    p.set_defaults(func=_cmd_pipeline_wait)

    # project
    project = top.add_parser("project", help="Project deploys and tests")
    project_sub = project.add_subparsers(dest="command", required=True)

    p = project_sub.add_parser("deploy", help="Deploy a project to a fabric")
    _add_global_flags(p)
    p.add_argument("--project", required=True, help="Project name")
    p.add_argument("--fabric", required=True, help="Fabric name")
    p.add_argument("--git-tag", required=True, help="{projectName}/{version}")
    p.add_argument("--pipeline-configs", help="Path to JSON with pipelineConfigurations")
    p.add_argument("--project-config", help="Path to JSON with projectConfiguration")
    p.set_defaults(func=_cmd_project_deploy)

    p = project_sub.add_parser("run-tests", help="Run project data tests")
    _add_global_flags(p)
    p.add_argument("--fabric-id", type=int, required=True)
    p.add_argument("--project-id", required=True)
    p.add_argument(
        "--tests-file",
        required=True,
        help="Path to JSON array matching the tests schema",
    )
    p.add_argument("--branch")
    p.add_argument("--version")
    p.add_argument("--model-name", help="Set for model tests")
    p.set_defaults(func=_cmd_project_run_tests)

    # fabric
    fabric = top.add_parser("fabric", help="Fabric admin")
    fabric_sub = fabric.add_subparsers(dest="command", required=True)

    p = fabric_sub.add_parser("create", help="Create a fabric")
    _add_global_flags(p)
    p.add_argument("--name", required=True)
    p.add_argument("--team-name", required=True)
    p.add_argument(
        "--provider",
        required=True,
        choices=["databricks", "bigquery", "ProphecyManaged"],
    )
    p.add_argument("--description")
    p.add_argument("--dataplane-url")
    p.add_argument("--secret-body", help="Path to JSON with embedded secret payload")
    p.add_argument("--connection-body", help="Path to JSON with embedded connection payload")
    p.set_defaults(func=_cmd_fabric_create)

    p = fabric_sub.add_parser("get", help="Get fabric details")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.set_defaults(func=_cmd_fabric_get)

    p = fabric_sub.add_parser("update", help="Update fabric name/description")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.add_argument("--name")
    p.add_argument("--description")
    p.set_defaults(func=_cmd_fabric_update)

    p = fabric_sub.add_parser("delete", help="Delete a fabric")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.set_defaults(func=_cmd_fabric_delete)

    # connection
    connection = top.add_parser("connection", help="Connection admin (per fabric)")
    connection_sub = connection.add_subparsers(dest="command", required=True)

    p = connection_sub.add_parser("create", help="Add a connection to a fabric")
    _add_global_flags(p)
    p.add_argument("--fabric-id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--kind", required=True, help="Connector type (databricks, snowflake, ...)")
    p.add_argument("--properties", required=True, help="Path to JSON with the connector properties")
    p.add_argument("--default-warehouse", action="store_true", default=None)
    p.set_defaults(func=_cmd_connection_create)

    p = connection_sub.add_parser("list", help="List connections in a fabric")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.set_defaults(func=_cmd_connection_list)

    p = connection_sub.add_parser("get", help="Get connection details")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.add_argument("connection_name")
    p.set_defaults(func=_cmd_connection_get)

    p = connection_sub.add_parser("update", help="Replace a connection's config (PUT)")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.add_argument("connection_name")
    p.add_argument("--name", required=True)
    p.add_argument("--kind", required=True)
    p.add_argument("--default-warehouse", action="store_true", default=False)
    p.add_argument("--properties", required=True, help="Path to JSON with the connector properties")
    p.set_defaults(func=_cmd_connection_update)

    p = connection_sub.add_parser("delete", help="Delete a connection")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.add_argument("connection_name")
    p.set_defaults(func=_cmd_connection_delete)

    # secret
    secret = top.add_parser("secret", help="Secret admin (per fabric)")
    secret_sub = secret.add_subparsers(dest="command", required=True)

    p = secret_sub.add_parser("create", help="Add a secret to a fabric")
    _add_global_flags(p)
    p.add_argument("--fabric-id", required=True)
    p.add_argument("--kind", default="prophecy")
    p.add_argument(
        "--sub-kind",
        required=True,
        choices=["text", "binary", "username_password", "m2m_oauth"],
    )
    p.add_argument("--properties", required=True, help="Path to JSON with the secret properties")
    p.set_defaults(func=_cmd_secret_create)

    p = secret_sub.add_parser("list", help="List secrets in a fabric")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.set_defaults(func=_cmd_secret_list)

    p = secret_sub.add_parser("get", help="Get secret details")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.add_argument("secret_id")
    p.set_defaults(func=_cmd_secret_get)

    p = secret_sub.add_parser("update", help="Replace a secret (PUT)")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.add_argument("secret_id")
    p.add_argument("--kind", default="prophecy")
    p.add_argument(
        "--sub-kind",
        required=True,
        choices=["text", "binary", "username_password", "m2m_oauth"],
    )
    p.add_argument("--properties", required=True, help="Path to JSON with the secret properties")
    p.set_defaults(func=_cmd_secret_update)

    p = secret_sub.add_parser("delete", help="Delete a secret")
    _add_global_flags(p)
    p.add_argument("fabric_id")
    p.add_argument("secret_id")
    p.set_defaults(func=_cmd_secret_delete)

    # identify (live-probe a method)
    identify = top.add_parser(
        "identify",
        help="live-probe a method on the configured instance and classify the outcome",
        description=(
            "Call a resource.method on the configured instance with the "
            "given args and classify the outcome (WORKS / BROKEN / "
            "UNVERIFIED). Useful for verifying a Dedicated SaaS endpoint "
            "matches the public OpenAPI spec, sanity-checking auth on a "
            "new token, or scoping an endpoint that isn't yet documented."
        ),
    )
    _add_global_flags(identify)
    identify.add_argument(
        "method",
        help=(
            "resource.method, e.g. 'pipelines.get_run_status', "
            "'fabrics.get', 'connections.list'"
        ),
    )
    identify.add_argument(
        "--arg",
        action="append",
        metavar="KEY=VALUE",
        help=(
            "keyword argument; values are coerced via int → JSON → str. "
            "Repeat for multiple."
        ),
    )
    identify.set_defaults(func=_cmd_identify)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except ProphecyError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
