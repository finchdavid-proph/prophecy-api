"""Secret admin endpoints (scoped to a fabric)."""

from __future__ import annotations

from typing import Any

from prophecy_api.resources._base import Resource


def _base(fabric_id: int | str) -> str:
    return f"/api/orchestration/fabric/{fabric_id}/secret"


class SecretsResource(Resource):
    """Manage secrets inside a fabric.

    Secret ``properties`` are ``subKind``-specific (text, binary,
    username_password, m2m_oauth). Build the dict per the reference at
    https://docs.prophecy.ai/api-reference/secrets/properties — this client
    forwards it as-is.

    Endpoints:
        - ``POST   /api/orchestration/fabric/{fabricId}/secret``
        - ``GET    /api/orchestration/fabric/{fabricId}/secret``
        - ``GET    /api/orchestration/fabric/{fabricId}/secret/id/{secretId}``
        - ``PUT    /api/orchestration/fabric/{fabricId}/secret/id/{secretId}``
        - ``DELETE /api/orchestration/fabric/{fabricId}/secret/id/{secretId}``
    """

    def create(
        self,
        fabric_id: int | str,
        *,
        kind: str,
        sub_kind: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a secret. ``kind`` is typically ``"prophecy"``.

        ``sub_kind`` is one of ``text``, ``binary``, ``username_password``,
        ``m2m_oauth``.
        """
        payload = {"kind": kind, "subKind": sub_kind, "properties": properties}
        return self._http.request("POST", _base(fabric_id), json=payload)

    def list(self, fabric_id: int | str) -> dict[str, Any]:
        """List every secret in the fabric.

        Returns the envelope ``{"success": ..., "data": {"secrets": [...]}}``.
        """
        return self._http.request("GET", _base(fabric_id))

    def get(self, fabric_id: int | str, secret_id: int | str) -> dict[str, Any]:
        return self._http.request("GET", f"{_base(fabric_id)}/id/{secret_id}")

    def update(
        self,
        fabric_id: int | str,
        secret_id: int | str,
        *,
        kind: str,
        sub_kind: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {"kind": kind, "subKind": sub_kind, "properties": properties}
        return self._http.request(
            "PUT", f"{_base(fabric_id)}/id/{secret_id}", json=payload
        )

    def delete(self, fabric_id: int | str, secret_id: int | str) -> dict[str, Any]:
        return self._http.request("DELETE", f"{_base(fabric_id)}/id/{secret_id}")
