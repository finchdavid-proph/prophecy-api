# prophecy-api

Python client for the [Prophecy](https://docs.prophecy.ai/) REST API. Wraps all 18 public endpoints for pipeline runs, project deploys, and admin (fabrics, connections, secrets) with a resource-namespaced interface.

```python
from prophecy_api import ProphecyClient

with ProphecyClient.from_env() as client:
    run = client.pipelines.trigger(fabric_id=1, pipeline_name="api_test", project_id="36")
    final = client.pipelines.run_and_wait(
        fabric_id=1, pipeline_name="api_test", project_id="36",
        poll_interval=10, timeout=1800,
    )
```

## Features

- **All 18 endpoints** — pipelines, projects, fabrics, connections, secrets.
- **Resource-namespaced API** — `client.pipelines.trigger()`, `client.fabrics.create()`, ... Mirrors the OpenAPI doc structure.
- **Single shared session** — one `requests.Session` with auth headers, used by every resource.
- **Automatic retry** for transient errors (5xx, 429) on idempotent verbs, with exponential backoff. Configurable per-client.
- **Typed exceptions** — `ProphecyHTTPError` (HTTP failures with status code), `ProphecyAPIError` (`success: false` responses), both inheriting `ProphecyError`.
- **`prophecy` CLI** — hierarchical subcommands covering every endpoint.
- **Polling helper** — `client.pipelines.run_and_wait()` triggers and blocks until terminal.
- **Type hints throughout**, Python 3.10+.

## Install

```bash
pip install prophecy-api
```

From a clone:

```bash
pip install -e ".[dev]"
```

## Authentication

Generate a Personal Access Token in Prophecy: **Settings → Access Tokens → Generate Token**. Copy the value immediately — it cannot be retrieved later.

```python
from prophecy_api import ProphecyClient

# Direct
client = ProphecyClient(
    base_url="https://app.prophecy.io",  # or your Dedicated SaaS host
    token="eyJ0eXAi...",
)

# Or via environment (PROPHECY_BASE_URL, PROPHECY_TOKEN)
client = ProphecyClient.from_env()
```

The base URL is your Prophecy instance host — `https://app.prophecy.io` for the public SaaS, or e.g. `https://g36b-sbox.sap.cloud.prophecy.ai` for Dedicated SaaS.

## Endpoints

All 18 endpoints in the OpenAPI spec are wrapped:

### Pipelines (`client.pipelines`)

| Method | Endpoint | Path |
|---|---|---|
| `trigger()` | `POST` | `/api/trigger/pipeline` |
| `get_run_status()` | `GET` | `/api/trigger/pipeline/{runId}` |
| `run_and_wait()` | — | trigger + poll |

### Projects (`client.projects`)

| Method | Endpoint | Path |
|---|---|---|
| `deploy()` | `POST` | `/api/deploy/project` |
| `run_data_tests()` | `POST` | `/api/orchestration/tests/run` |

### Fabrics (`client.fabrics`)

| Method | Endpoint | Path |
|---|---|---|
| `create()` | `POST` | `/api/orchestration/fabric` |
| `get()` | `GET` | `/api/orchestration/fabric/{fabricId}` |
| `update()` | `PUT` | `/api/orchestration/fabric/{fabricId}` |
| `delete()` | `DELETE` | `/api/orchestration/fabric/{fabricId}` |

### Connections (`client.connections`)

| Method | Endpoint | Path |
|---|---|---|
| `create()` | `POST` | `/api/orchestration/fabric/{fabricId}/connection` |
| `list()` | `GET` | `/api/orchestration/fabric/{fabricId}/connection` |
| `get()` | `GET` | `/api/orchestration/fabric/{fabricId}/connection/name/{connectionName}` |
| `update()` | `PUT` | `/api/orchestration/fabric/{fabricId}/connection/name/{connectionName}` |
| `delete()` | `DELETE` | `/api/orchestration/fabric/{fabricId}/connection/name/{connectionName}` |

Connection `properties` are connector-specific (Databricks, Snowflake, BigQuery, ...). Build the dict per the [connector reference](https://docs.prophecy.ai/api-reference/connections/properties) — this client forwards it as-is.

### Secrets (`client.secrets`)

| Method | Endpoint | Path |
|---|---|---|
| `create()` | `POST` | `/api/orchestration/fabric/{fabricId}/secret` |
| `list()` | `GET` | `/api/orchestration/fabric/{fabricId}/secret` |
| `get()` | `GET` | `/api/orchestration/fabric/{fabricId}/secret/id/{secretId}` |
| `update()` | `PUT` | `/api/orchestration/fabric/{fabricId}/secret/id/{secretId}` |
| `delete()` | `DELETE` | `/api/orchestration/fabric/{fabricId}/secret/id/{secretId}` |

## Library examples

```python
from prophecy_api import ProphecyClient

client = ProphecyClient.from_env()

# --- Pipelines ---
run = client.pipelines.trigger(
    fabric_id=1,
    pipeline_name="api_test",
    project_id="36",
    parameters={"franchise_id": "3000007"},
    version="2",
)
status = client.pipelines.get_run_status(run["runId"])

# --- Projects ---
client.projects.deploy(
    project_name="CustomerAnalytics",
    fabric_name="production-databricks",
    git_tag="CustomerAnalytics/2.1",
)
client.projects.run_data_tests(
    fabric_id=4251,
    project_id="2419",
    tests=[{
        "source": "hospital_patients",
        "table": "patient_details",
        "columnTests": [{"name": "age", "tests": [{"name": "not_null"}]}],
    }],
)

# --- Fabrics ---
fabric = client.fabrics.create(
    name="staging",
    team_name="data-platform",
    provider="databricks",
    description="staging fabric for tests",
)
client.fabrics.update(fabric["data"]["id"], description="updated")
client.fabrics.delete(fabric["data"]["id"])

# --- Connections ---
client.connections.create(
    fabric_id=1,
    name="bigquery_dev",
    kind="bigquery",
    properties={
        "authType": "private_key",
        "dataset": "dev",
        "projectId": "dev-project-2222",
        "serviceAccountKey": {
            "kind": "prophecy", "type": "secret", "subKind": "text",
            "properties": {"id": "1234", "name": "bq_sa"},
        },
    },
    is_default_warehouse_connection=False,
)
connections = client.connections.list(1)
client.connections.delete(1, "bigquery_dev")

# --- Secrets ---
secret = client.secrets.create(
    fabric_id=1,
    kind="prophecy",
    sub_kind="text",
    properties={"name": "databricks-pat", "value": "pat-value"},
)
client.secrets.list(1)
client.secrets.delete(1, secret["data"]["id"])
```

## CLI

A `prophecy` console command is installed alongside the package, with hierarchical subcommands:

```bash
export PROPHECY_BASE_URL=https://app.prophecy.io
export PROPHECY_TOKEN=eyJ0eXAi...

prophecy pipeline trigger --fabric-id 1 --pipeline api_test --project-id 36 \
    --param franchise_id=3000007
prophecy pipeline status <run_id>
prophecy pipeline wait --fabric-id 1 --pipeline api_test --project-id 36 \
    --poll-interval 10 --timeout-seconds 1800

prophecy project deploy --project CustomerAnalytics --fabric prod \
    --git-tag CustomerAnalytics/2.1
prophecy project run-tests --fabric-id 4251 --project-id 2419 \
    --tests-file tests.json

prophecy fabric create --name staging --team-name data --provider databricks
prophecy fabric get 10740
prophecy fabric update 10740 --description "new description"
prophecy fabric delete 10740

prophecy connection create --fabric-id 1 --name bq1 --kind bigquery \
    --properties bigquery.json
prophecy connection list 1
prophecy connection get 1 bq1
prophecy connection delete 1 bq1

prophecy secret create --fabric-id 1 --sub-kind text --properties pat.json
prophecy secret list 1
prophecy secret delete 1 4657
```

`--properties` for connections/secrets is a path to a JSON file with the connector- or secret-type-specific body. See the [Prophecy connector docs](https://docs.prophecy.ai/api-reference/connections/properties) for shapes.

The `scripts/` directory contains the most common pipeline operations as standalone Python files (no install required if `requests` is on `PYTHONPATH`):

```bash
python scripts/trigger_pipeline.py --fabric-id 1 --pipeline api_test --project-id 36
python scripts/get_run_status.py <run_id>
python scripts/run_pipeline_and_wait.py --fabric-id 1 --pipeline api_test --project-id 36
python scripts/deploy_project.py --project CustomerAnalytics --fabric prod --git-tag CustomerAnalytics/2.1
python scripts/run_data_tests.py --fabric-id 4251 --project-id 2419 --tests-file tests.json
```

For admin operations (fabrics, connections, secrets), use the unified `prophecy` CLI.

## Errors

Three exception classes, all inheriting `ProphecyError`:

| Exception | When | Attributes |
|---|---|---|
| `ProphecyHTTPError` | Non-2xx response or network/timeout failure | `status_code`, `response_body` |
| `ProphecyAPIError` | API responded 2xx but with `success: false` | `response_body` |
| `ProphecyError` | Base class for catching either | — |

```python
from prophecy_api import ProphecyAPIError, ProphecyClient, ProphecyHTTPError

try:
    client.pipelines.trigger(fabric_id=999, pipeline_name="x", project_id="y")
except ProphecyAPIError as e:
    print(f"API said no: {e} (body: {e.response_body})")
except ProphecyHTTPError as e:
    print(f"HTTP {e.status_code}: {e}")
```

## Retry

Idempotent verbs (`GET`, `HEAD`, `OPTIONS`) auto-retry on `429` and `5xx` responses with exponential backoff. POST / PUT / DELETE are not retried (creates and updates may not be idempotent on the server side).

Tune via constructor:

```python
ProphecyClient(
    base_url=...,
    token=...,
    retry_total=5,        # default 3; set to 0 to disable
    retry_backoff=1.0,    # default 0.5
)
```

## Development

```bash
pip install -e ".[dev]"
pytest         # 36 tests, ~0.1s
ruff check .
```

Tests use [`responses`](https://github.com/getsentry/responses) to mock HTTP — no real Prophecy account required.

## Claude Code skill

A self-contained Claude Code skill that wraps this client lives in [claude-skill/](claude-skill/). Drop the folder into your `.claude/skills/` directory (renamed `apex-prophecy` or whatever you prefer) and Claude will trigger it on phrases like "trigger a Prophecy pipeline", "deploy CustomerAnalytics 2.1", or "rotate the databricks PAT secret". The skill bundles its own copy of the client so it works without `pip install prophecy-api`.

## License

MIT — see [LICENSE](LICENSE).
