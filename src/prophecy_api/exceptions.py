"""Exceptions raised by the Prophecy API client."""

from __future__ import annotations

from typing import Any


class ProphecyError(Exception):
    """Base class for all errors raised by this client."""


class ProphecyHTTPError(ProphecyError):
    """Raised when an HTTP request fails (network, timeout, non-2xx status).

    Attributes:
        status_code: HTTP status code, or ``None`` if the request never reached
            the server (timeout, DNS failure, etc.).
        response_body: The decoded response body as a dict if available, or
            the raw text otherwise.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: dict[str, Any] | str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ProphecyAPIError(ProphecyError):
    """Raised when a Prophecy API call returns ``success: false``.

    Attributes:
        message: The ``msg`` (or ``message``) field from the response.
        response_body: The full decoded response body.
    """

    def __init__(self, message: str, *, response_body: dict[str, Any] | None = None):
        super().__init__(message)
        self.response_body = response_body or {}
