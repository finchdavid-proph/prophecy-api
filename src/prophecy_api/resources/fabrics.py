"""Fabric admin endpoints."""

from __future__ import annotations

from typing import Any

from prophecy_api.resources._base import Resource

_BASE = "/api/orchestration/fabric"


class FabricsResource(Resource):
    """Create, fetch, update, and delete Prophecy fabrics.

    Endpoints:
        - ``POST   /api/orchestration/fabric``
        - ``GET    /api/orchestration/fabric/{fabricId}``
        - ``PUT    /api/orchestration/fabric/{fabricId}``
        - ``DELETE /api/orchestration/fabric/{fabricId}``
    """

    def create(
        self,
        *,
        name: str,
        team_name: str,
        provider: str,
        description: str | None = None,
        dataplane_url: str | None = None,
        secret: dict[str, Any] | None = None,
        connection: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a fabric.

        ``provider`` is one of ``databricks``, ``bigquery``, or
        ``ProphecyManaged``. ``secret`` and ``connection`` are optional
        embedded creates with the same body shape as
        :class:`SecretsResource.create` and
        :class:`ConnectionsResource.create`.
        """
        payload: dict[str, Any] = {
            "name": name,
            "teamName": team_name,
            "provider": provider,
        }
        if description is not None:
            payload["description"] = description
        if dataplane_url is not None:
            payload["dataplaneUrl"] = dataplane_url
        if secret is not None:
            payload["secret"] = secret
        if connection is not None:
            payload["connection"] = connection
        return self._http.request("POST", _BASE, json=payload)

    def get(self, fabric_id: int | str) -> dict[str, Any]:
        return self._http.request("GET", f"{_BASE}/{fabric_id}")

    def update(
        self,
        fabric_id: int | str,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update a fabric. Only ``name`` and ``description`` are mutable."""
        if name is None and description is None:
            raise ValueError("update() requires at least one of name or description")
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        return self._http.request("PUT", f"{_BASE}/{fabric_id}", json=payload)

    def delete(self, fabric_id: int | str) -> dict[str, Any]:
        return self._http.request("DELETE", f"{_BASE}/{fabric_id}")
