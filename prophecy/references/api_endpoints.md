# Prophecy REST API — endpoint reference

Verified set of all 18 endpoints used by the `prophecy` skill. Paths and methods come from the per-page OpenAPI specs at `https://docs.prophecy.ai/api-reference/...`.

> **Important:** the index at `https://docs.prophecy.ai/llms.txt` lists wrong paths (e.g. `/api/pipelines/trigger`, `/api/fabrics/{id}`). The OpenAPI specs and this reference are authoritative.

All endpoints require:

- `X-AUTH-TOKEN: <Personal Access Token>` header
- `Content-Type: application/json` (for POST / PUT)

Base URL is the user's Prophecy instance host (e.g. `https://app.prophecy.io` or a Dedicated SaaS host).

## Pipelines

### POST /api/trigger/pipeline

Trigger a deployed pipeline run.

```json
{
  "fabricId": 1,
  "pipelineName": "api_test",
  "projectId": "36",
  "parameters": {"franchise_id": "3000007"},
  "branch": "main",
  "version": "2",
  "processName": "franchise_reviews"
}
```

Required: `fabricId`, `pipelineName`, `projectId`. All other fields optional.

Success: `{"success": true, "runId": "abc-123", "msg": "Pipeline triggered successfully"}`

### GET /api/trigger/pipeline/{runId}

Fetch run status. Response includes `runStatus` (`RUNNING` | `SUCCEEDED` | `ERROR`); `errorMessage` is included on `ERROR`.

```json
{
  "success": true,
  "runId": "abc-123",
  "createdAt": "2025-06-17T18:01:49.275359",
  "updatedAt": "2025-06-17T18:02:41.712486",
  "projectId": "41459",
  "pipelineName": "bakehouse",
  "fabricId": "33290",
  "runStatus": "SUCCEEDED"
}
```

## Projects

### POST /api/deploy/project

Deploy a project to a fabric. `gitTag` is `{projectName}/{version}`.

```json
{
  "projectName": "CustomerAnalytics",
  "fabricName": "production-databricks",
  "gitTag": "CustomerAnalytics/2.1",
  "pipelineConfigurations": {
    "sales_report": {"report_period": "monthly", "include_forecasts": "true"}
  },
  "projectConfiguration": {"environment": "production"}
}
```

### POST /api/orchestration/tests/run

Run project data tests.

**Column / table / project tests:**

```json
{
  "fabricId": 4251,
  "projectId": "2419",
  "tests": [
    {
      "source": "hospital_patients",
      "table": "patient_details",
      "columnTests": [{"name": "age", "tests": [{"name": "not_null"}]}],
      "tableTests": [{"name": "equal_row_count"}]
    },
    {"projectTests": [{"name": "assert_table_not_empty"}]}
  ]
}
```

**Model tests** — set `modelName`, pass a single empty `tests` entry:

```json
{
  "fabricId": 4251,
  "projectId": "2419",
  "modelName": "patient_risk_model",
  "tests": [{}]
}
```

Optional on either form: `branch`, `version`.

## Fabrics

### POST /api/orchestration/fabric

Create a fabric. `provider` is `databricks`, `bigquery`, or `ProphecyManaged`.

```json
{
  "name": "API_Generated_Fabric",
  "description": "...",
  "teamName": "devTeam",
  "provider": "databricks",
  "secret": {"kind": "prophecy", "subKind": "text", "properties": {...}},
  "connection": {"name": "...", "kind": "databricks", "properties": {...}}
}
```

`secret` and `connection` are optional embedded creates. Response: `{"success": true, "data": {"id": "10740"}}`.

### GET /api/orchestration/fabric/{fabricId}

Returns `{"success": true, "data": {"fabricID": "10740", "name": "...", "teamID": "1200"}}`.

### PUT /api/orchestration/fabric/{fabricId}

Update fabric. Only `name` and `description` are mutable.

```json
{"name": "renamed", "description": "new description"}
```

### DELETE /api/orchestration/fabric/{fabricId}

Returns `{"success": true, "data": {"id": "10743"}}`.

## Connections (scoped to a fabric)

Connection `properties` are connector-specific. See `https://docs.prophecy.ai/api-reference/connections/properties/` for per-connector schemas (databricks, snowflake, bigquery, postgres, redshift, oracle, mssql, mongodb, salesforce, tableau, etc.).

### POST /api/orchestration/fabric/{fabricId}/connection

```json
{
  "name": "bigquery_connection_1",
  "kind": "bigquery",
  "isDefaultWarehouseConnection": false,
  "properties": {
    "authType": "private_key",
    "dataset": "dev",
    "projectId": "dev-project-2222",
    "serviceAccountKey": {
      "kind": "prophecy", "type": "secret", "subKind": "text",
      "properties": {"id": "1234", "name": "bq_service_account_1"}
    }
  }
}
```

`isDefaultWarehouseConnection` applies only to databricks / bigquery / snowflake.

### GET /api/orchestration/fabric/{fabricId}/connection

List connections in the fabric. Response is enveloped:

```json
{
  "success": true,
  "data": {
    "Connections": [
      {"id": "...", "name": "...", "kind": "...", "isDefaultWarehouseConnection": false, "properties": {}}
    ]
  }
}
```

### GET /api/orchestration/fabric/{fabricId}/connection/name/{connectionName}

Get one connection. The `/name/` segment is required.

### PUT /api/orchestration/fabric/{fabricId}/connection/name/{connectionName}

Replace a connection. **All four** body fields are required: `name`, `kind`, `isDefaultWarehouseConnection`, `properties`.

### DELETE /api/orchestration/fabric/{fabricId}/connection/name/{connectionName}

Returns `{"success": true, "data": {"id": "<connection_name>"}}`.

## Secrets (scoped to a fabric)

Secret `properties` are `subKind`-specific. See `https://docs.prophecy.ai/api-reference/secrets/properties/`:

- `text` — `{"name": ..., "value": ...}`
- `binary` — `{"name": ..., "value": <base64>}`
- `username_password` — `{"name": ..., "username": ..., "password": ...}`
- `m2m_oauth` — OAuth M2M shape

### POST /api/orchestration/fabric/{fabricId}/secret

```json
{
  "kind": "prophecy",
  "subKind": "text",
  "properties": {"name": "your-secret-name", "value": "your-secret-value"}
}
```

Response: `{"success": true, "data": {"id": "4657"}}`.

### GET /api/orchestration/fabric/{fabricId}/secret

List secrets. Response is enveloped under `data.secrets`:

```json
{
  "success": true,
  "data": {
    "secrets": [
      {"kind": "prophecy", "subKind": "text", "properties": {"id": "...", "name": "..."}, "type": "secret"}
    ]
  }
}
```

### GET /api/orchestration/fabric/{fabricId}/secret/id/{secretId}

Get one secret. The `/id/` segment is required.

### PUT /api/orchestration/fabric/{fabricId}/secret/id/{secretId}

Replace a secret. All three body fields are required: `kind`, `subKind`, `properties`.

### DELETE /api/orchestration/fabric/{fabricId}/secret/id/{secretId}

Returns `{"success": true, "data": {"id": "4656"}}`.

## Run statuses

| Status | Terminal? | Meaning |
|---|---|---|
| `RUNNING` | no | Pipeline is executing |
| `SUCCEEDED` | yes | Pipeline finished without error |
| `ERROR` | yes | Pipeline failed; `errorMessage` is populated |

`run_pipeline_and_wait()` polls until the status is in `{SUCCEEDED, ERROR}` or the deadline elapses.

## Authentication

Generate a Personal Access Token in the Prophecy UI:
**Settings → Access Tokens → Generate Token**

The token is shown once at creation and cannot be retrieved later. Store it in `PROPHECY_TOKEN`. The base URL goes in `PROPHECY_BASE_URL`.

## Source links

- Introduction: https://docs.prophecy.ai/api-reference/introduction
- Trigger pipeline: https://docs.prophecy.ai/api-reference/pipelines/trigger-pipeline-run
- Get run status: https://docs.prophecy.ai/api-reference/pipelines/get-pipeline-run-status
- Run data tests: https://docs.prophecy.ai/api-reference/pipelines/run-data-tests
- Deploy project: https://docs.prophecy.ai/api-reference/projects/deploy-project
- Fabrics: https://docs.prophecy.ai/api-reference/fabrics/{create-a-new-fabric, get-fabric-details, update-an-existing-fabric, delete-a-fabric}
- Connections: https://docs.prophecy.ai/api-reference/connections/{add-connection-to-fabric, list-connections-per-fabric, retrieve-connection-details, update-connection, delete-connection}
- Secrets: https://docs.prophecy.ai/api-reference/secrets/{add-secret-to-fabric, list-secrets-per-fabric, retrieve-secret-details, update-secret, delete-secret}
- Connector property shapes: https://docs.prophecy.ai/api-reference/connections/properties
- Secret property shapes: https://docs.prophecy.ai/api-reference/secrets/properties
