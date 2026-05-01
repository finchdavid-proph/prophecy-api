---
name: apex-prophecy
description: Trigger and monitor Prophecy pipelines, deploy Prophecy projects, run Prophecy data tests, and manage Prophecy fabrics, connections, and secrets via the Prophecy REST API. Use this skill whenever the user asks to "trigger a Prophecy pipeline", "kick off a Prophecy run", "run a pipeline in Prophecy", "deploy a Prophecy project", "check Prophecy run status", "wait for a Prophecy pipeline to finish", "run Prophecy data tests", "create / update / delete a Prophecy fabric", "add a connection to a Prophecy fabric", "list Prophecy connections", "create / rotate / delete a Prophecy secret", or anything that calls the Prophecy API at app.prophecy.io or a Dedicated SaaS Prophecy host. Trigger even when the user does not say "API" — phrases like "start the bakehouse pipeline", "deploy CustomerAnalytics 2.1 to production-databricks", "is run abc-123 done yet", "spin up a new fabric for staging", "wire a Snowflake connection into fabric 5", "rotate the databricks PAT secret", or "block until the nightly job finishes" all warrant this skill.
skill-type: specialist
category: Integration
---

# Prophecy REST API

This skill calls all 18 endpoints of the Prophecy REST API. It covers two distinct workflows:

1. **Pipeline operations** — trigger runs, check status, wait for completion, deploy projects, run data tests.
2. **Fabric admin** — create/update/delete fabrics, connections, and secrets.

It is *not* for editing Prophecy projects (the UI / git is the source of truth there) — it is for **automation against deployed projects** and **provisioning fabrics**.

## When to use this skill

Trigger when the user wants to:

- **Run a pipeline** in a deployed Prophecy project, with or without parameters.
- **Get the status** of a pipeline run by its `runId`.
- **Trigger and wait** for a pipeline run to reach a terminal state (`SUCCEEDED` or `ERROR`).
- **Deploy a project** to a fabric (e.g., promote a tagged version to production).
- **Run data tests** for a project (column tests, table tests, project tests, model tests).
- **Manage fabrics** — create, get details, rename / re-describe, delete.
- **Manage connections** in a fabric — create, list, get, replace, delete.
- **Manage secrets** in a fabric — create, list, get, rotate, delete.

Pipelines must run on a Prophecy fabric and be part of a *published* project — i.e., deployed.

## Required setup

Set the following environment variables before invoking any script (the skill will not store these for you — surface a clear error if either is missing):

- `PROPHECY_BASE_URL` — your instance host, e.g. `https://app.prophecy.io` or a Dedicated SaaS host like `https://g36b-sbox.sap.cloud.prophecy.ai`.
- `PROPHECY_TOKEN` — a Personal Access Token (Settings → Access Tokens → Generate Token in the Prophecy UI). It is shown only once at creation.

If `PROPHECY_BASE_URL` is missing, infer it from the URL of any Prophecy page the user shares (the host portion is the base URL). If `PROPHECY_TOKEN` is missing, ask the user to paste it.

## Inputs to gather from the user

Confirm the inputs you need from the user before calling. **Do not guess** these — surface what is missing:

| Operation | Required inputs |
|---|---|
| Pipeline trigger | `fabricId` (int), `pipelineName`, `projectId` |
| Pipeline status | `runId` |
| Pipeline run-and-wait | same as trigger, plus optional `pollInterval` and `timeout` |
| Project deploy | `projectName`, `fabricName`, `gitTag` (`{projectName}/{version}`) |
| Project run-tests | `fabricId`, `projectId`, a `tests` array (see `references/api_endpoints.md`) |
| Fabric create | `name`, `teamName`, `provider` (`databricks`/`bigquery`/`ProphecyManaged`) |
| Fabric get/update/delete | `fabricId` |
| Connection create | `fabricId`, `name`, `kind` (databricks/snowflake/bigquery/...), `properties` (connector-specific) |
| Connection list/get/update/delete | `fabricId` and `connectionName` (when targeting one) |
| Secret create | `fabricId`, `subKind` (text/binary/username_password/m2m_oauth), `properties` |
| Secret list/get/update/delete | `fabricId` and `secretId` (when targeting one) |

Helpful tip: if the user pastes a Prophecy pipeline URL like `https://<host>/metadata/sql/<projectId>?entity=pipeline&name=<pipelineName>`, you can read both `projectId` and `pipelineName` from it. The host is `PROPHECY_BASE_URL`.

## Workflow

This skill bundles `scripts/prophecy_client.py`, a class-based client with resource-namespaced accessors:

```
client.pipelines.trigger | get_run_status | run_and_wait
client.projects.deploy | run_data_tests
client.fabrics.create | get | update | delete
client.connections.create | list | get | update | delete
client.secrets.create | list | get | update | delete
```

For the five most common pipeline operations, the skill ships standalone CLI scripts — see "Scripts" below. For everything else (fabric / connection / secret admin), import the client class directly in Python.

1. **Confirm inputs.** List what you have and what is missing. Ask for missing values before making calls.
2. **Pick the right approach** — bundled script for a common pipeline op, or `python3 -c` snippet for admin ops.
3. **Invoke** with the bundled scripts or by importing `prophecy_client` from `scripts/`.
4. **Parse the JSON response** and report it back to the user. On `ProphecyAPIError` (the API returned `success: false`), surface the message; on `ProphecyHTTPError`, surface the HTTP status.
5. **For long-running runs**, prefer `run_pipeline_and_wait.py` (or `client.pipelines.run_and_wait()`) — it handles deadlines and surfaces ERROR exit codes.

## Scripts

All scripts live in `scripts/` and are run as `python3 scripts/<name>.py [flags]`. They share a single `prophecy_client.py` module.

### `scripts/trigger_pipeline.py`

```bash
python3 scripts/trigger_pipeline.py \
    --fabric-id 1 \
    --pipeline api_test \
    --project-id 36 \
    --param franchise_id=3000007 \
    --version 2
```

### `scripts/get_run_status.py`

```bash
python3 scripts/get_run_status.py <run_id>
```

### `scripts/run_pipeline_and_wait.py`

```bash
python3 scripts/run_pipeline_and_wait.py \
    --fabric-id 1 --pipeline api_test --project-id 36 \
    --poll-interval 10 --timeout-seconds 1800
```

Triggers, then polls until `SUCCEEDED` or `ERROR`. Exits non-zero if the run errors or times out.

### `scripts/deploy_project.py`

```bash
python3 scripts/deploy_project.py \
    --project CustomerAnalytics \
    --fabric production-databricks \
    --git-tag CustomerAnalytics/2.1 \
    [--pipeline-configs configs.json] \
    [--project-config project.json]
```

### `scripts/run_data_tests.py`

```bash
python3 scripts/run_data_tests.py \
    --fabric-id 4251 --project-id 2419 \
    --tests-file tests.json
```

## Class-based usage for admin operations

For fabric, connection, and secret admin, import `prophecy_client` directly. Examples:

```python
import sys; sys.path.insert(0, "scripts")
from prophecy_client import ProphecyClient

with ProphecyClient.from_env() as c:
    # Create a fabric
    fabric = c.fabrics.create(
        name="staging",
        team_name="data-platform",
        provider="databricks",
        description="staging environment",
    )
    fabric_id = fabric["data"]["id"]

    # Add a Databricks connection
    c.connections.create(
        fabric_id,
        name="warehouse_default",
        kind="databricks",
        properties={
            "authType": "pat",
            "jdbcUrl": "<jdbc-url>",
            "catalog": "main",
            "schema": "default",
            "token": "{{SECRET}}",
        },
        is_default_warehouse_connection=True,
    )

    # Create a text secret (e.g., a PAT)
    secret = c.secrets.create(
        fabric_id,
        kind="prophecy",
        sub_kind="text",
        properties={"name": "databricks-pat", "value": "pat-value"},
    )

    # List, then delete
    print(c.connections.list(fabric_id))
    c.connections.delete(fabric_id, "warehouse_default")
    c.secrets.delete(fabric_id, secret["data"]["id"])
    c.fabrics.delete(fabric_id)
```

## Endpoint reference

See `references/api_endpoints.md` for the verified path, body schema, and example response of every endpoint. The llms.txt index at `https://docs.prophecy.ai/llms.txt` lists incorrect paths; the per-page OpenAPI specs (and that reference) are authoritative.

## Errors and what to surface

The bundled client raises three exception types:

- `ProphecyHTTPError` — HTTP non-2xx or network/timeout. Has `status_code` and `response_body`. Surface the status code.
- `ProphecyAPIError` — API returned 2xx with `success: false`. Has `response_body`. Surface the `msg` verbatim.
- `ProphecyError` — base class for catching either.

When the user reports a failure, report which class was raised and include the underlying message.

## What this skill does NOT do

- It does not edit project source — that lives in git, not the API.
- It does not validate connector- or secret-type-specific property schemas; you build the dict per the connector / secret-type docs and the client forwards it as-is.
- It does not list pipelines or projects — the API does not expose a discovery endpoint. The user must supply names/IDs (often pulled from the URL of a Prophecy UI page).
