"""
Reusable HTTP client with retry logic, timeout handling, and structured error responses.
All microservice clients inherit from this base.
"""
import logging
from typing import Optional, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger("tiana-bff")

# Shared timeout config
DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class ServiceError(Exception):
    """Raised when a downstream service returns an error."""
    def __init__(self, status_code: int, detail: str, service: str):
        self.status_code = status_code
        self.detail = detail
        self.service = service
        super().__init__(f"[{service}] {status_code}: {detail}")


class BaseClient:
    """
    Base HTTP client for microservice communication.
    Provides retry logic, authentication headers, and error normalization.
    """

    def __init__(self, base_url: str, api_key: str = "", api_secret: str = "", service_name: str = "service"):
        self.base_url = base_url.rstrip("/") + "/"
        self.api_key = api_key
        self.api_secret = api_secret
        self.service_name = service_name
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=DEFAULT_TIMEOUT,
        )

    def _auth_headers(self, bearer_token: Optional[str] = None) -> dict:
        """Build authentication headers for the downstream service."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        if self.api_secret:
            headers["X-API-SECRET"] = self.api_secret
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        return headers

    def _form_auth_headers(self) -> dict:
        """Headers for OAuth2 form-based login."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        if self.api_secret:
            headers["X-API-SECRET"] = self.api_secret
        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        bearer_token: Optional[str] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> dict | list:
        """Execute an HTTP request with automatic retry on transient failures."""
        endpoint_clean = endpoint.lstrip("/")
        base_clean = self.base_url.rstrip("/")
        if base_clean.endswith("/api/v1") and endpoint_clean.startswith("api/v1/"):
            endpoint_clean = endpoint_clean[7:]
        elif base_clean.endswith("/api") and endpoint_clean.startswith("api/"):
            endpoint_clean = endpoint_clean[4:]

        req_headers = headers or self._auth_headers(bearer_token)

        try:
            response = await self._client.request(
                method,
                endpoint_clean,
                headers=req_headers,
                json=json,
                data=data,
                params=params,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout):
            logger.error(f"[{self.service_name}] Connection failed: {endpoint}")
            raise ServiceError(503, f"{self.service_name} is unavailable", self.service_name)
        except (httpx.ReadTimeout, httpx.TimeoutException):
            logger.error(f"[{self.service_name}] Timeout: {endpoint}")
            raise ServiceError(504, f"{self.service_name} timed out", self.service_name)
        except httpx.RequestError as e:
            logger.error(f"[{self.service_name}] Request error: {endpoint} - {e}")
            raise ServiceError(503, f"{self.service_name} error: {str(e)}", self.service_name)

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ServiceError(response.status_code, str(detail), self.service_name)

        # Some endpoints return empty body (204, etc.)
        if response.status_code == 204 or not response.content:
            return {}

        return response.json()

    async def get(self, endpoint: str, bearer_token: Optional[str] = None, params: Optional[dict] = None):
        return await self._request("GET", endpoint, bearer_token=bearer_token, params=params)

    async def post(self, endpoint: str, bearer_token: Optional[str] = None, json: Optional[Any] = None, data: Optional[Any] = None, headers: Optional[dict] = None):
        return await self._request("POST", endpoint, bearer_token=bearer_token, json=json, data=data, headers=headers)

    async def put(self, endpoint: str, bearer_token: Optional[str] = None, json: Optional[Any] = None, params: Optional[dict] = None):
        return await self._request("PUT", endpoint, bearer_token=bearer_token, json=json, params=params)

    async def delete(self, endpoint: str, bearer_token: Optional[str] = None):
        return await self._request("DELETE", endpoint, bearer_token=bearer_token)

    async def close(self):
        await self._client.aclose()
