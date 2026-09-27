"""Authentication for the Plant Ranger API."""

from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession

from .const import API_BASE_PATH, API_HOST
from .exceptions import (
    PlantRangerAuthError,
    PlantRangerConnectionError,
    PlantRangerError,
)


class AbstractAuth(ABC):
    """Authenticated transport for the Plant Ranger API.

    Token lifetime is the caller's problem: `async_get_access_token` is called on
    every request, so an implementation is free to refresh before returning.
    """

    def __init__(self, websession: ClientSession, host: str = API_HOST) -> None:
        """Initialize the transport."""
        self.websession = websession
        self.host = host.rstrip("/")

    @abstractmethod
    async def async_get_access_token(self) -> str:
        """Return a valid access token."""

    async def request(self, method: str, path: str, **kwargs: Any) -> ClientResponse:
        """Make an authenticated request against the API."""
        headers = dict(kwargs.pop("headers", None) or {})
        headers["Authorization"] = f"Bearer {await self.async_get_access_token()}"
        headers.setdefault("Accept", "application/json")

        try:
            return await self.websession.request(
                method,
                f"{self.host}{API_BASE_PATH}{path}",
                headers=headers,
                **kwargs,
            )
        except ClientError as err:
            raise PlantRangerConnectionError(str(err)) from err

    async def get_json(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make a GET request and return the decoded body."""
        response = await self.request("GET", path, **kwargs)
        async with response:
            if response.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                raise PlantRangerAuthError(await _error_message(response))
            if response.status >= HTTPStatus.BAD_REQUEST:
                raise PlantRangerError(await _error_message(response))
            try:
                return await response.json()
            except (ClientError, ValueError) as err:
                raise PlantRangerError(f"Malformed response from {path}") from err


async def _error_message(response: ClientResponse) -> str:
    """Pull the message out of the API's error envelope."""
    try:
        body = await response.json()
    except (ClientError, ValueError):
        return f"HTTP {response.status}"
    if isinstance(body, dict) and (message := body.get("message")):
        return f"HTTP {response.status}: {message}"
    return f"HTTP {response.status}"
