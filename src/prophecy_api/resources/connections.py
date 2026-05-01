"""Connection admin endpoints (scoped to a fabric)."""

from __future__ import annotations

from typing import Any

from prophecy_api.resources._base import Resource


def _base(fabric_id: int | str) -> str:
    return f"/api/orchestration/fabric/{fabric_id}/connection"


class ConnectionsResource(Resource):
    """Manage connections inside a fabric.

    Connection ``properties`` are connector-specific (Databricks, Snowflake,
    BigQuery, Postgres, ...). This client takes the dict you build per the
    connector reference at
    https://docs.prophecy.ai/api-reference/connections/properties — it does
    not validate connector-specific schemas.

    Endpoints:
        - ``POST   /api/orchestration/fabric/{fabricId}/connection``
        - ``GET    /api/orchestration/fabric/{fabricId}/connection``
        - ``GET    /api/orchestration/fabric/{fabricId}/connection/name/{connectionName}``
        - ``PUT    /api/orchestration/fabric/{fabricId}/connection/name/{connectionName}``
        - ``DELETE /api/orchestration/fabric/{fabricId}/connection/name/{connectionName}``
    """

    def create(
        self,
        fabric_id: int | str,
        *,
        name: str,
        kind: str,
        properties: dict[str, Any],
        is_default_warehouse_connection: bool | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "kind": kind, "properties": properties}
        if is_default_warehouse_connection is not None:
            payload["isDefaultWarehouseConnection"] = is_default_warehouse_connection
        return self._http.request("POST", _base(fabric_id), json=payload)

    def list(self, fabric_id: int | str) -> dict[str, Any]:
        """List every connection in the fabric.

        Returns the envelope ``{"success": ..., "data": {"Connections": [...]}}``.
        """
        return self._http.request("GET", _base(fabric_id))

    def get(self, fabric_id: int | str, connection_name: str) -> dict[str, Any]:
        return self._http.request("GET", f"{_base(fabric_id)}/name/{connection_name}")

    def update(
        self,
        fabric_id: int | str,
        connection_name: str,
        *,
        name: str,
        kind: str,
        is_default_warehouse_connection: bool,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Replace the connection. All four body fields are required.

        ``connection_name`` in the path is the existing name; ``name`` in the
        body is the (possibly new) name to set.
        """
        payload = {
            "name": name,
            "kind": kind,
            "isDefaultWarehouseConnection": is_default_warehouse_connection,
            "properties": properties,
        }
        return self._http.request(
            "PUT", f"{_base(fabric_id)}/name/{connection_name}", json=payload
        )

    def delete(self, fabric_id: int | str, connection_name: str) -> dict[str, Any]:
        return self._http.request("DELETE", f"{_base(fabric_id)}/name/{connection_name}")
