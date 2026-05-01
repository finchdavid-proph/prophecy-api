"""Base class for resource clients."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prophecy_api._http import HTTPClient


class Resource:
    """Shared base for resource-namespaced API accessors.

    Each resource (Pipelines, Projects, Fabrics, Connections, Secrets) holds a
    reference to the shared ``HTTPClient``. Resources should use ``self._http``
    for all requests; they never construct URLs against ``base_url`` directly.
    """

    def __init__(self, http: HTTPClient):
        self._http = http
