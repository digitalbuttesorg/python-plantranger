"""Authentication for the Plant Ranger API."""

from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Any

from aiohttp import (
    ClientConnectionError,
    ClientError,
    ClientPayloadError,
    ClientResponse,
    ClientSession,
    InvalidURL,
    NonHttpUrlClientError,
    TooManyRedirects,
)

from .const import API_BASE_PATH, API_HOST
from .exceptions import (
    PlantRangerAccountActionError,
    PlantRangerAuthError,
    PlantRangerConnectionError,
    PlantRangerError,
    PlantRangerForbiddenError,
)

_CODE_ACCOUNT_ACTION_REQUIRED = "ACCOUNT_ACTION_REQUIRED"


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
        except TimeoutError as err:
            raise PlantRangerConnectionError(f"Timeout calling {path}") from err
        except (InvalidURL, NonHttpUrlClientError, TooManyRedirects) as err:
            raise PlantRangerError(str(err)) from err
        except ClientError as err:
            raise PlantRangerConnectionError(str(err)) from err

    async def request_json(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a request and return the decoded body."""
        response = await self.request(method, path, json=json)
        async with response:
            if response.status >= HTTPStatus.BAD_REQUEST:
                raise await _error(response)
            try:
                data = await response.json()
            except TimeoutError as err:
                raise PlantRangerConnectionError(f"Timeout calling {path}") from err
            except (ClientConnectionError, ClientPayloadError) as err:
                raise PlantRangerConnectionError(str(err)) from err
            except (ClientError, ValueError) as err:
                raise PlantRangerError(f"Malformed response from {path}") from err
            if not isinstance(data, dict):
                raise PlantRangerError(f"Malformed response from {path}")
            return data


async def _error(response: ClientResponse) -> PlantRangerError:
    """Build the exception for an error response."""
    message, code = await _error_details(response)
    if response.status == HTTPStatus.UNAUTHORIZED:
        return PlantRangerAuthError(message)
    if response.status == HTTPStatus.FORBIDDEN:
        return PlantRangerForbiddenError(message)
    if (
        response.status == HTTPStatus.BAD_REQUEST
        and code == _CODE_ACCOUNT_ACTION_REQUIRED
    ):
        return PlantRangerAccountActionError(message)
    if response.status in (
        HTTPStatus.REQUEST_TIMEOUT,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        HTTPStatus.BAD_GATEWAY,
        HTTPStatus.SERVICE_UNAVAILABLE,
        HTTPStatus.GATEWAY_TIMEOUT,
    ):
        return PlantRangerConnectionError(message)
    return PlantRangerError(message)


async def _error_details(response: ClientResponse) -> tuple[str, str | None]:
    """Pull the message and code out of the API's error envelope."""
    try:
        body = await response.json()
    except (ClientError, TimeoutError, ValueError):
        return f"HTTP {response.status}", None
    if not isinstance(body, dict):
        return f"HTTP {response.status}", None
    if message := body.get("message"):
        return f"HTTP {response.status}: {message}", body.get("code")
    return f"HTTP {response.status}", body.get("code")
