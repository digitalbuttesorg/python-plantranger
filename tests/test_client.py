"""Tests for the Plant Ranger client."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, override
from unittest.mock import Mock, patch

import pytest
from aiohttp import (
    ClientOSError,
    ClientPayloadError,
    ClientResponse,
    ClientSession,
    InvalidUrlClientError,
    NonHttpUrlClientError,
    NonHttpUrlRedirectClientError,
    ServerDisconnectedError,
    ServerTimeoutError,
    TooManyRedirects,
    web,
)
from aiohttp.test_utils import TestServer, unused_port

from plantranger import (
    REJECT_REASON_NOT_IN_TEAM,
    SENSOR_STATUS_IN_TEAM,
    SENSOR_STATUS_UNREGISTERED,
    AbstractAuth,
    PlantRangerAccountActionError,
    PlantRangerAuthError,
    PlantRangerClient,
    PlantRangerConnectionError,
    PlantRangerError,
    PlantRangerForbiddenError,
    Sample,
)

TEAM_ID = "team-1"
MAC = "AA:BB:CC:DD:EE:FF"
TEAMS_PATH = "/v1/teams"
SENSOR_PATH = f"/v1/teams/{TEAM_ID}/sensors/{MAC}"
SAMPLES_PATH = f"/v1/teams/{TEAM_ID}/samples"
SAMPLE_TIME = datetime(2026, 1, 2, 15, 4, 5, tzinfo=UTC)


class MockAuth(AbstractAuth):
    """Auth with a fixed token."""

    @override
    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        return "token"


class MockApi:
    """A local server standing in for the Plant Ranger API."""

    def __init__(self) -> None:
        """Initialize the server."""
        self.host = ""
        self.headers: dict[str, str] = {}
        self.json: dict[str, Any] | None = None
        self.path = ""
        self._responses: dict[tuple[str, str], web.Response] = {}

    def respond(
        self,
        method: str,
        path: str,
        *,
        status: int = 200,
        payload: Any = None,
        html: str | None = None,
    ) -> None:
        """Set the response for a route."""
        if html is not None:
            response = web.Response(status=status, text=html, content_type="text/html")
        else:
            response = web.json_response(payload, status=status)
        self._responses[(method, path)] = response

    async def handle(self, request: web.Request) -> web.Response:
        """Record the request and return the route's response."""
        self.headers = dict(request.headers)
        self.json = await request.json() if request.can_read_body else None
        self.path = request.raw_path
        return self._responses[(request.method, request.path)]


@pytest.fixture
async def mock_api() -> AsyncIterator[MockApi]:
    """Run a fake Plant Ranger API."""
    api = MockApi()
    app = web.Application()
    app.router.add_route("*", "/{path:.*}", api.handle)
    async with TestServer(app) as server:
        api.host = f"http://{server.host}:{server.port}"
        yield api


@pytest.fixture
async def client(mock_api: MockApi) -> AsyncIterator[PlantRangerClient]:
    """Return a client for the fake API."""
    async with ClientSession() as session:
        yield PlantRangerClient(MockAuth(session, mock_api.host))


async def test_get_teams(mock_api: MockApi, client: PlantRangerClient) -> None:
    """Test listing teams sends the bearer token."""
    mock_api.respond(
        "GET", TEAMS_PATH, payload={"teams": [{"id": TEAM_ID, "name": "Demo Home"}]}
    )

    teams = await client.get_teams()

    assert [team.id for team in teams] == [TEAM_ID]
    assert teams[0].name == "Demo Home"
    assert mock_api.headers["Authorization"] == "Bearer token"


async def test_get_team(mock_api: MockApi, client: PlantRangerClient) -> None:
    """Test fetching a team with its plants."""
    mock_api.respond(
        "GET",
        f"/v1/teams/{TEAM_ID}",
        payload={"id": TEAM_ID, "plants": [{"id": "plant-1", "moisture": 42}]},
    )

    team = await client.get_team(TEAM_ID)

    assert team.id == TEAM_ID
    assert team.plants[0].moisture == 42.0


async def test_get_plant(mock_api: MockApi, client: PlantRangerClient) -> None:
    """Test fetching a plant."""
    mock_api.respond(
        "GET", "/v1/plants/plant-1", payload={"id": "plant-1", "team_id": TEAM_ID}
    )

    plant = await client.get_plant("plant-1")

    assert plant.id == "plant-1"
    assert plant.team_id == TEAM_ID


async def test_get_sensor_unregistered(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test the status of a sensor without a plant."""
    mock_api.respond("GET", SENSOR_PATH, payload={"status": "unregistered"})

    sensor = await client.get_sensor(TEAM_ID, MAC)

    assert sensor.status == SENSOR_STATUS_UNREGISTERED
    assert sensor.plant_id is None
    assert sensor.plant_name is None


async def test_get_sensor_in_team(mock_api: MockApi, client: PlantRangerClient) -> None:
    """Test the status of a sensor with a plant in the team."""
    mock_api.respond(
        "GET",
        SENSOR_PATH,
        payload={"status": "in_team", "plant_id": "plant-1", "plant_name": "Monstera"},
    )

    sensor = await client.get_sensor(TEAM_ID, MAC)

    assert sensor.status == SENSOR_STATUS_IN_TEAM
    assert sensor.plant_id == "plant-1"
    assert sensor.plant_name == "Monstera"


@pytest.mark.parametrize("status", [200, 201])
async def test_register_sensor(
    mock_api: MockApi, client: PlantRangerClient, status: int
) -> None:
    """Test a new and an existing plant are returned the same way."""
    mock_api.respond(
        "POST",
        SENSOR_PATH,
        status=status,
        payload={"id": "plant-1", "name": "Monstera", "mac_address": MAC},
    )

    plant = await client.register_sensor(
        TEAM_ID, MAC, "Monstera", location="Living Room"
    )

    assert plant.id == "plant-1"
    assert plant.name == "Monstera"
    assert mock_api.json == {
        "plant_name": "Monstera",
        "location": "Living Room",
    }


async def test_register_sensor_without_location(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test the location is left out of the body when not given."""
    mock_api.respond("POST", SENSOR_PATH, status=201, payload={"id": "plant-1"})

    await client.register_sensor(TEAM_ID, MAC, "Monstera")

    assert mock_api.json == {"plant_name": "Monstera"}


async def test_submit_samples(mock_api: MockApi, client: PlantRangerClient) -> None:
    """Test submitting samples returns the accepted count and the rejections."""
    mock_api.respond(
        "POST",
        SAMPLES_PATH,
        status=202,
        payload={
            "accepted": 1,
            "rejected": [
                {
                    "mac": "11:22:33:44:55:66",
                    "time": "2026-01-02T15:04:05Z",
                    "reason": "not_in_team",
                }
            ],
        },
    )

    result = await client.submit_samples(
        TEAM_ID,
        [
            Sample(mac=MAC, time=SAMPLE_TIME, moisture=42.5, rssi=-67),
            Sample(mac="11:22:33:44:55:66", time=SAMPLE_TIME),
        ],
    )

    assert result.accepted == 1
    (rejected,) = result.rejected
    assert rejected.mac == "11:22:33:44:55:66"
    assert rejected.time == SAMPLE_TIME
    assert rejected.reason == REJECT_REASON_NOT_IN_TEAM
    assert mock_api.json == {
        "samples": [
            {
                "mac": MAC,
                "time": "2026-01-02T15:04:05+00:00",
                "moisture": 42.5,
                "rssi": -67,
            },
            {"mac": "11:22:33:44:55:66", "time": "2026-01-02T15:04:05+00:00"},
        ]
    }


async def test_submit_samples_none_rejected(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test a null rejected list is read as empty."""
    mock_api.respond(
        "POST", SAMPLES_PATH, status=202, payload={"accepted": 1, "rejected": None}
    )

    result = await client.submit_samples(TEAM_ID, [Sample(mac=MAC, time=SAMPLE_TIME)])

    assert result.accepted == 1
    assert result.rejected == []


async def test_submit_samples_rejected_without_reason(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test a rejected sample's missing reason and time read as None."""
    mock_api.respond(
        "POST",
        SAMPLES_PATH,
        status=202,
        payload={"accepted": 0, "rejected": [{"mac": MAC}]},
    )

    result = await client.submit_samples(TEAM_ID, [Sample(mac=MAC, time=SAMPLE_TIME)])

    (rejected,) = result.rejected
    assert rejected.mac == MAC
    assert rejected.reason is None
    assert rejected.time is None


async def test_submit_samples_naive_time(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test a time without a timezone is sent as UTC."""
    mock_api.respond("POST", SAMPLES_PATH, status=202, payload={"accepted": 1})

    await client.submit_samples(
        TEAM_ID, [Sample(mac=MAC, time=SAMPLE_TIME.replace(tzinfo=None))]
    )

    assert mock_api.json == {
        "samples": [{"mac": MAC, "time": "2026-01-02T15:04:05+00:00"}]
    }


async def test_submit_samples_other_timezone(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test a time in another timezone is sent as UTC."""
    mock_api.respond("POST", SAMPLES_PATH, status=202, payload={"accepted": 1})
    time = SAMPLE_TIME.astimezone(timezone(timedelta(hours=2)))

    await client.submit_samples(TEAM_ID, [Sample(mac=MAC, time=time)])

    assert mock_api.json == {
        "samples": [{"mac": MAC, "time": "2026-01-02T15:04:05+00:00"}]
    }


async def test_submit_samples_non_finite(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test readings that are not finite are left out of the body."""
    mock_api.respond("POST", SAMPLES_PATH, status=202, payload={"accepted": 1})

    await client.submit_samples(
        TEAM_ID,
        [
            Sample(
                mac=MAC,
                time=SAMPLE_TIME,
                moisture=float("nan"),
                light=float("inf"),
                battery=87,
            )
        ],
    )

    assert mock_api.json == {
        "samples": [{"mac": MAC, "time": "2026-01-02T15:04:05+00:00", "battery": 87}]
    }


async def test_submit_samples_empty(client: PlantRangerClient) -> None:
    """Test an empty list returns an empty result without a request."""
    result = await client.submit_samples(TEAM_ID, [])

    assert result.accepted == 0
    assert result.rejected == []


@pytest.mark.parametrize(
    ("status", "code", "expected"),
    [
        pytest.param(401, "INVALID_TOKEN", PlantRangerAuthError, id="unauthorized"),
        pytest.param(403, "FORBIDDEN", PlantRangerForbiddenError, id="forbidden"),
        pytest.param(
            400,
            "ACCOUNT_ACTION_REQUIRED",
            PlantRangerAccountActionError,
            id="account_action",
        ),
        pytest.param(400, "INVALID_REQUEST", PlantRangerError, id="bad_request"),
        pytest.param(404, "NOT_FOUND", PlantRangerError, id="not_found"),
        pytest.param(
            408, "REQUEST_TIMEOUT", PlantRangerConnectionError, id="request_timeout"
        ),
        pytest.param(500, "INTERNAL", PlantRangerError, id="server_error"),
        pytest.param(502, "BAD_GATEWAY", PlantRangerConnectionError, id="bad_gateway"),
        pytest.param(503, "UNAVAILABLE", PlantRangerConnectionError, id="unavailable"),
        pytest.param(
            504, "GATEWAY_TIMEOUT", PlantRangerConnectionError, id="gateway_timeout"
        ),
    ],
)
async def test_error_mapping(
    mock_api: MockApi,
    client: PlantRangerClient,
    status: int,
    code: str,
    expected: type[PlantRangerError],
) -> None:
    """Test each error response raises its exception with the server message."""
    mock_api.respond(
        "POST",
        SENSOR_PATH,
        status=status,
        payload={"error": "Error", "code": code, "message": "Something happened"},
    )

    with pytest.raises(PlantRangerError) as err:
        await client.register_sensor(TEAM_ID, MAC, "Monstera")

    assert type(err.value) is expected
    assert str(err.value) == f"HTTP {status}: Something happened"


async def test_forbidden_is_auth_error(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test a 403 is still caught as an auth error."""
    mock_api.respond("GET", TEAMS_PATH, status=403, payload={"message": "Forbidden"})

    with pytest.raises(PlantRangerAuthError):
        await client.get_teams()


async def test_error_without_envelope(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test an error response that is not JSON falls back to the status."""
    mock_api.respond("GET", SENSOR_PATH, status=503, html="<html>")

    with pytest.raises(PlantRangerConnectionError, match=r"^HTTP 503$"):
        await client.get_sensor(TEAM_ID, MAC)


async def test_malformed_response(mock_api: MockApi, client: PlantRangerClient) -> None:
    """Test a successful response that is not JSON raises."""
    mock_api.respond("GET", SENSOR_PATH, html="<html>")

    with pytest.raises(PlantRangerError, match="Malformed response"):
        await client.get_sensor(TEAM_ID, MAC)


async def test_invalid_json_response(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test a successful response that is not valid JSON raises."""
    mock_api.respond("GET", SENSOR_PATH, payload={})

    with (
        patch.object(ClientResponse, "json", side_effect=ValueError),
        pytest.raises(PlantRangerError, match="Malformed response"),
    ):
        await client.get_sensor(TEAM_ID, MAC)


async def test_non_object_response(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test a successful response that is not a JSON object raises."""
    mock_api.respond("GET", SENSOR_PATH, payload=[])

    with pytest.raises(PlantRangerError, match="Malformed response"):
        await client.get_sensor(TEAM_ID, MAC)


async def test_missing_field_response(
    mock_api: MockApi, client: PlantRangerClient
) -> None:
    """Test a successful response without a required field raises."""
    mock_api.respond("GET", SENSOR_PATH, payload={})

    with pytest.raises(PlantRangerError, match="Malformed response"):
        await client.get_sensor(TEAM_ID, MAC)


@pytest.mark.parametrize(
    "rejected",
    [
        pytest.param([{}], id="missing_mac"),
        pytest.param(["x"], id="non_object_entry"),
        pytest.param(1, id="non_list"),
    ],
)
async def test_malformed_rejected(
    mock_api: MockApi, client: PlantRangerClient, rejected: Any
) -> None:
    """Test a rejected list that cannot be read raises."""
    mock_api.respond(
        "POST", SAMPLES_PATH, status=202, payload={"accepted": 0, "rejected": rejected}
    )

    with pytest.raises(PlantRangerError, match="Malformed response"):
        await client.submit_samples(TEAM_ID, [Sample(mac=MAC, time=SAMPLE_TIME)])


async def test_path_value_quoted(mock_api: MockApi, client: PlantRangerClient) -> None:
    """Test a value with a slash is sent as a single path segment."""
    mock_api.respond("GET", "/v1/teams/a/b", payload={"id": "a/b"})

    await client.get_team("a/b")

    assert mock_api.path == "/v1/teams/a%2Fb"


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("", id="empty"),
        pytest.param(".", id="dot"),
        pytest.param("..", id="dot_dot"),
    ],
)
async def test_invalid_path_value(client: PlantRangerClient, value: str) -> None:
    """Test a value that would change the request path raises."""
    with pytest.raises(PlantRangerError, match="Invalid path value"):
        await client.get_sensor(TEAM_ID, value)


async def test_connection_error() -> None:
    """Test a transport failure raises a connection error."""
    async with ClientSession() as session:
        client = PlantRangerClient(
            MockAuth(session, f"http://127.0.0.1:{unused_port()}")
        )

        with pytest.raises(PlantRangerConnectionError):
            await client.get_sensor(TEAM_ID, MAC)


async def test_request_timeout(client: PlantRangerClient) -> None:
    """Test a request that times out raises a connection error."""
    with (
        patch.object(ClientSession, "request", side_effect=TimeoutError),
        pytest.raises(PlantRangerConnectionError, match="Timeout calling"),
    ):
        await client.get_sensor(TEAM_ID, MAC)


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(InvalidUrlClientError("http://"), id="invalid_url"),
        pytest.param(NonHttpUrlClientError("ftp://example.com"), id="non_http_url"),
        pytest.param(
            NonHttpUrlRedirectClientError("ftp://example.com"), id="non_http_redirect"
        ),
        pytest.param(TooManyRedirects(Mock(), ()), id="too_many_redirects"),
    ],
)
async def test_request_config_error(
    client: PlantRangerClient, error: Exception
) -> None:
    """Test a request that a retry cannot fix raises a non-connection error."""
    with (
        patch.object(ClientSession, "request", side_effect=error),
        pytest.raises(PlantRangerError) as err,
    ):
        await client.get_sensor(TEAM_ID, MAC)

    assert type(err.value) is PlantRangerError


async def test_response_timeout(mock_api: MockApi, client: PlantRangerClient) -> None:
    """Test a response body that times out raises a connection error."""
    mock_api.respond("GET", SENSOR_PATH, payload={})

    with (
        patch.object(ClientResponse, "json", side_effect=ServerTimeoutError),
        pytest.raises(PlantRangerConnectionError, match="Timeout calling"),
    ):
        await client.get_sensor(TEAM_ID, MAC)


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(ServerDisconnectedError(), id="disconnected"),
        pytest.param(ClientOSError(), id="os_error"),
        pytest.param(
            ClientPayloadError("Response payload is not completed"), id="payload"
        ),
    ],
)
async def test_response_connection_error(
    mock_api: MockApi, client: PlantRangerClient, error: Exception
) -> None:
    """Test a response body that fails to arrive raises a connection error."""
    mock_api.respond("GET", SENSOR_PATH, payload={})

    with (
        patch.object(ClientResponse, "json", side_effect=error),
        pytest.raises(PlantRangerConnectionError),
    ):
        await client.get_sensor(TEAM_ID, MAC)
