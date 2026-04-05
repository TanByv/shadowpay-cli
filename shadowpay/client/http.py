"""Base async HTTP client using curl_cffi with retry logic and structured logging."""

from __future__ import annotations

from typing import Any, Literal, TypeVar

import orjson
import structlog
from curl_cffi.requests import AsyncSession
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = structlog.get_logger()
T = TypeVar("T", bound=BaseModel)


class ApiError(Exception):
    """Raised when the Shadowpay API returns an error response."""

    def __init__(
        self,
        status_code: int,
        error_message: str | None = None,
        body: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_message = error_message
        self.body = body or {}
        super().__init__(f"API Error {status_code}: {error_message or 'Unknown error'}")


class TransientApiError(ApiError):
    """Retryable API error (429 / 5xx)."""


class ShadowpayHttpClient:
    """Async HTTP client wrapping ``curl_cffi`` for the Shadowpay V2 API.

    Usage::

        async with ShadowpayHttpClient(token, base_url) as client:
            data = await client.get("/user/balance")
    """

    def __init__(self, token: str, base_url: str) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> ShadowpayHttpClient:
        self._session = AsyncSession(impersonate="chrome")
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    # ── Internals ───────────────────────────────────────────────────────────

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    @retry(
        retry=retry_if_exception_type(TransientApiError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: Literal["GET", "POST", "PATCH", "DELETE", "PUT", "HEAD", "OPTIONS"],
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        """Perform an HTTP request and return the parsed JSON body."""
        assert self._session is not None, "Client not entered as context manager"

        url = self._url(path)

        log.debug(
            "http_request",
            method=method,
            url=url,
            params=params,
        )

        # Build kwargs
        kwargs: dict[str, Any] = {"headers": self._headers}
        if params:
            # Filter out None values
            kwargs["params"] = {k: v for k, v in params.items() if v is not None}
        if json_body is not None:
            kwargs["data"] = orjson.dumps(json_body)

        resp = await self._session.request(method, url, **kwargs)

        log.debug(
            "http_response",
            status_code=resp.status_code,
            url=url,
        )

        # Parse body
        try:
            body: dict[str, Any] = orjson.loads(resp.content)
        except Exception:
            body = {}

        # Handle errors
        if resp.status_code == 429 or resp.status_code >= 500:
            raise TransientApiError(
                resp.status_code,
                body.get("error_message") or body.get("message"),
                body,
            )

        if resp.status_code >= 400:
            raise ApiError(
                resp.status_code,
                body.get("error_message") or body.get("message"),
                body,
            )

        # Check API-level error
        if body.get("status") == "error":
            raise ApiError(
                resp.status_code,
                body.get("error_message") or body.get("message"),
                body,
            )

        return body

    # ── Public convenience methods ──────────────────────────────────────────

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        return await self._request("POST", path, params=params, json_body=json_body)

    async def patch(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._request("PATCH", path, json_body=json_body)

    async def delete(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("DELETE", path, params=params)
