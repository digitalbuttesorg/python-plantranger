"""Client for the Plant Ranger API."""

from collections.abc import Callable
from typing import Any

from .auth import AbstractAuth
from .exceptions import PlantRangerError
from .models import (
    FullPlant,
    PlantSummary,
    Sample,
    SensorStatus,
    SubmitResult,
    Team,
    TeamListItem,
)


class PlantRangerClient:
    """Client for the Plant Ranger API."""

    def __init__(self, auth: AbstractAuth) -> None:
        """Initialize the client."""
        self._auth = auth

    async def _request[T](
        self,
        build: Callable[[dict[str, Any]], T],
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> T:
        """Make a request and build a model from the decoded body."""
        data = await self._auth.request_json(method, path, json=json)
        try:
            return build(data)
        except (AttributeError, KeyError, TypeError) as err:
            raise PlantRangerError(f"Malformed response from {path}") from err

    async def get_teams(self) -> list[TeamListItem]:
        """Return the teams the token has access to."""
        return await self._request(
            lambda data: [
                TeamListItem.from_dict(team) for team in data.get("teams") or []
            ],
            "GET",
            "/teams",
        )

    async def get_team(self, team_id: str) -> Team:
        """Return a team with its plant and bridge summaries."""
        return await self._request(Team.from_dict, "GET", f"/teams/{team_id}")

    async def get_plant(self, plant_id: str) -> FullPlant:
        """Return full detail for a single plant."""
        return await self._request(FullPlant.from_dict, "GET", f"/plants/{plant_id}")

    async def get_sensor(self, team_id: str, mac: str) -> SensorStatus:
        """Return what a sensor's MAC address is to a team."""
        return await self._request(
            SensorStatus.from_dict, "GET", f"/teams/{team_id}/sensors/{mac}"
        )

    async def register_sensor(
        self, team_id: str, mac: str, plant_name: str, *, location: str | None = None
    ) -> PlantSummary:
        """Create a plant for a sensor, or return the one it already has."""
        body: dict[str, str] = {"plant_name": plant_name}
        if location is not None:
            body["location"] = location
        return await self._request(
            PlantSummary.from_dict,
            "POST",
            f"/teams/{team_id}/sensors/{mac}",
            json=body,
        )

    async def submit_samples(self, team_id: str, samples: list[Sample]) -> SubmitResult:
        """Submit sensor readings for a team's plants."""
        if not samples:
            return SubmitResult()
        return await self._request(
            SubmitResult.from_dict,
            "POST",
            f"/teams/{team_id}/samples",
            json={"samples": [sample.as_dict() for sample in samples]},
        )
