# Method Reference

Single source of truth for the 19 client methods (18 endpoints + 1 polling helper).

**Status:** every method below is live-verified against `app.prophecy.io` and pinned by integration tests under `tests/`. The Prophecy REST API is publicly documented and stable — there are no UNVERIFIED or BROKEN entries here (unlike the GraphQL surface, which is internal and changes without notice).

| Status | Meaning |
|---|---|
| ✅ WORKS | Live-verified; documented on `docs.prophecy.ai/api-reference/`. |
| ⚙️ HELPER | Composes other methods (e.g. polling loops). |

---

## Pipelines (`client.pipelines`)

| Method | Status | Endpoint | Purpose |
|---|---|---|---|
| `trigger(*, fabric_id, pipeline_name, project_id, parameters?, branch?, version?, process_name?)` | ✅ | `POST /api/trigger/pipeline` | Trigger a deployed pipeline run. Returns `{success, runId, msg}`. |
| `get_run_status(run_id)` | ✅ | `GET /api/trigger/pipeline/{runId}` | Fetch run status. `runStatus` ∈ {`RUNNING`, `SUCCEEDED`, `ERROR`}; `errorMessage` is set on `ERROR`. |
| `run_and_wait(*, ..., poll_interval=10.0, timeout=1800.0)` | ⚙️ | (composes the two above) | Trigger then poll until terminal status or deadline. Raises `ProphecyAPIError` on timeout. |

## Projects (`client.projects`)

| Method | Status | Endpoint | Purpose |
|---|---|---|---|
| `deploy(*, project_name, fabric_name, git_tag, pipeline_configurations?, project_configuration?)` | ✅ | `POST /api/deploy/project` | Deploy a project to a fabric. `git_tag` is `{projectName}/{version}`. |
| `run_data_tests(*, fabric_id, project_id, tests, branch?, version?, model_name?)` | ✅ | `POST /api/orchestration/tests/run` | Run column / table / project tests, OR a model test (set `model_name`, pass `tests=[{}]`). |

## Fabrics (`client.fabrics`)

| Method | Status | Endpoint | Purpose |
|---|---|---|---|
| `create(*, name, team_name, provider, description?, dataplane_url?, secret?, connection?)` | ✅ | `POST /api/orchestration/fabric` | Create a fabric. `provider` ∈ {`databricks`, `bigquery`, `ProphecyManaged`}. Optional embedded creates: `secret`, `connection`. |
| `get(fabric_id)` | ✅ | `GET /api/orchestration/fabric/{fabricId}` | Returns `{success, data: {fabricID, name, teamID}}`. |
| `update(fabric_id, *, name?, description?)` | ✅ | `PUT /api/orchestration/fabric/{fabricId}` | Only `name` and `description` are mutable. Raises `ValueError` if both omitted. |
| `delete(fabric_id)` | ✅ | `DELETE /api/orchestration/fabric/{fabricId}` | Returns `{success, data: {id}}`. |

## Connections (`client.connections`)

Connection `properties` are connector-specific. See [docs.prophecy.ai/api-reference/connections/properties](https://docs.prophecy.ai/api-reference/connections/properties) for per-connector schemas.

| Method | Status | Endpoint | Purpose |
|---|---|---|---|
| `create(fabric_id, *, name, kind, properties, is_default_warehouse_connection?)` | ✅ | `POST /api/orchestration/fabric/{fabricId}/connection` | Add a connection to a fabric. `is_default_warehouse_connection` applies only to databricks/bigquery/snowflake. |
| `list(fabric_id)` | ✅ | `GET /api/orchestration/fabric/{fabricId}/connection` | Response is enveloped under `data.Connections`. |
| `get(fabric_id, connection_name)` | ✅ | `GET /api/orchestration/fabric/{fabricId}/connection/name/{name}` | The `/name/` path segment is required. |
| `update(fabric_id, connection_name, *, name, kind, is_default_warehouse_connection, properties)` | ✅ | `PUT /api/orchestration/fabric/{fabricId}/connection/name/{name}` | All four body fields are required (full replace, not patch). |
| `delete(fabric_id, connection_name)` | ✅ | `DELETE /api/orchestration/fabric/{fabricId}/connection/name/{name}` | Returns `{success, data: {id: <connection_name>}}`. |

## Secrets (`client.secrets`)

`sub_kind` ∈ {`text`, `binary`, `username_password`, `m2m_oauth`}. `properties` shape depends on `sub_kind`. See [docs.prophecy.ai/api-reference/secrets/properties](https://docs.prophecy.ai/api-reference/secrets/properties).

| Method | Status | Endpoint | Purpose |
|---|---|---|---|
| `create(fabric_id, *, kind, sub_kind, properties)` | ✅ | `POST /api/orchestration/fabric/{fabricId}/secret` | Returns `{success, data: {id}}`. |
| `list(fabric_id)` | ✅ | `GET /api/orchestration/fabric/{fabricId}/secret` | Response is enveloped under `data.secrets`. |
| `get(fabric_id, secret_id)` | ✅ | `GET /api/orchestration/fabric/{fabricId}/secret/id/{secretId}` | The `/id/` path segment is required. |
| `update(fabric_id, secret_id, *, kind, sub_kind, properties)` | ✅ | `PUT /api/orchestration/fabric/{fabricId}/secret/id/{secretId}` | All three body fields are required (full replace). |
| `delete(fabric_id, secret_id)` | ✅ | `DELETE /api/orchestration/fabric/{fabricId}/secret/id/{secretId}` | Returns `{success, data: {id}}`. |

---

## Run statuses

| Status | Terminal? | Meaning |
|---|---|---|
| `RUNNING` | no | Pipeline is executing. |
| `SUCCEEDED` | yes | Pipeline finished without error. |
| `ERROR` | yes | Pipeline failed; `errorMessage` is populated. |

`run_and_wait()` polls until the status is in `{SUCCEEDED, ERROR}` or the deadline elapses.

## Authentication

Every request requires the `X-AUTH-TOKEN` header. Generate a Personal Access Token in the Prophecy UI: **Settings → Access Tokens → Generate Token**.

Set `PROPHECY_BASE_URL` and `PROPHECY_TOKEN` env vars and use `ProphecyClient.from_env()`, or pass them explicitly.

## Verifying against your instance

Run the `identify` CLI subcommand to live-probe a method against your Prophecy instance and classify the outcome:

```bash
prophecy identify pipelines.get_run_status --arg run_id=abc-123
prophecy identify fabrics.get --arg fabric_id=4251
```

Useful when debugging a 4xx, when validating a Dedicated SaaS endpoint matches the public OpenAPI spec, or when adding a 19th endpoint that isn't yet documented.

## Source links

- API introduction — https://docs.prophecy.ai/api-reference/introduction
- Pipelines — https://docs.prophecy.ai/api-reference/pipelines/{trigger-pipeline-run, get-pipeline-run-status, run-data-tests}
- Projects — https://docs.prophecy.ai/api-reference/projects/deploy-project
- Fabrics — https://docs.prophecy.ai/api-reference/fabrics/{create-a-new-fabric, get-fabric-details, update-an-existing-fabric, delete-a-fabric}
- Connections — https://docs.prophecy.ai/api-reference/connections/{add-connection-to-fabric, list-connections-per-fabric, retrieve-connection-details, update-connection, delete-connection}
- Secrets — https://docs.prophecy.ai/api-reference/secrets/{add-secret-to-fabric, list-secrets-per-fabric, retrieve-secret-details, update-secret, delete-secret}
- Connector property shapes — https://docs.prophecy.ai/api-reference/connections/properties
- Secret property shapes — https://docs.prophecy.ai/api-reference/secrets/properties
