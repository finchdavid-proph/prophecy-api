"""Internal HTTP transport for the Prophecy API client.

Wraps a ``requests.Session`` with auth headers, configurable retry, and
unified error translation. All resource modules go through ``HTTPClient``
rather than calling ``requests`` directly.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from prophecy_api.exceptions import ProphecyAPIError, ProphecyHTTPError

DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_RETRY_TOTAL = 3
DEFAULT_RETRY_BACKOFF = 0.5
DEFAULT_RETRY_STATUS = (429, 500, 502, 503, 504)
DEFAULT_RETRY_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class HTTPClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
        retry_total: int = DEFAULT_RETRY_TOTAL,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
    ):
        if not base_url:
            raise ValueError("base_url is required")
        if not token:
            raise ValueError("token is required")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or self._build_session(retry_total, retry_backoff)
        self.session.headers.update(
            {
                "X-AUTH-TOKEN": token,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "prophecy-api-python",
            }
        )

    @staticmethod
    def _build_session(retry_total: int, retry_backoff: float) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=retry_total,
            backoff_factor=retry_backoff,
            status_forcelist=DEFAULT_RETRY_STATUS,
            allowed_methods=DEFAULT_RETRY_METHODS,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def close(self) -> None:
        self.session.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.request(
                method,
                url,
                json=json,
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise ProphecyHTTPError(f"{method} {path} failed: {e}") from e

        body = self._decode_body(resp)

        if not resp.ok:
            msg = self._extract_error_message(body) or resp.reason or "HTTP error"
            raise ProphecyHTTPError(
                f"{method} {path} returned {resp.status_code}: {msg}",
                status_code=resp.status_code,
                response_body=body,
            )

        if isinstance(body, dict) and body.get("success") is False:
            raise ProphecyAPIError(
                self._extract_error_message(body) or f"{method} {path} returned success=false",
                response_body=body,
            )
        return body if isinstance(body, dict) else {"data": body}

    @staticmethod
    def _decode_body(resp: requests.Response) -> dict[str, Any] | list[Any] | str:
        try:
            return resp.json()
        except ValueError:
            return resp.text

    @staticmethod
    def _extract_error_message(body: Any) -> str | None:
        if not isinstance(body, dict):
            return None
        for key in ("msg", "message", "error"):
            value = body.get(key)
            if isinstance(value, str) and value:
                return value
        return None
