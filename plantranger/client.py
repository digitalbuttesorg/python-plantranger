"""Client for the Plant Ranger API."""

from .auth import AbstractAuth
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

    async def get_teams(self) -> list[TeamListItem]:
        """Return the teams the token has access to."""
        data = await self._auth.request_json("GET", "/teams")
        return [TeamListItem.from_dict(team) for team in data.get("teams") or []]

    async def get_team(self, team_id: str) -> Team:
        """Return a team with its plant and bridge summaries."""
        return Team.from_dict(await self._auth.request_json("GET", f"/teams/{team_id}"))

    async def get_plant(self, plant_id: str) -> FullPlant:
        """Return full detail for a single plant."""
        return FullPlant.from_dict(
            await self._auth.request_json("GET", f"/plants/{plant_id}")
        )

    async def get_sensor(self, team_id: str, mac: str) -> SensorStatus:
        """Return what a sensor's MAC address is to a team."""
        return SensorStatus.from_dict(
            await self._auth.request_json("GET", f"/teams/{team_id}/sensors/{mac}")
        )

    async def register_sensor(
        self, team_id: str, mac: str, plant_name: str, *, location: str | None = None
    ) -> PlantSummary:
        """Create a plant for a sensor, or return the one it already has."""
        body: dict[str, str] = {"plant_name": plant_name}
        if location is not None:
            body["location"] = location
        return PlantSummary.from_dict(
            await self._auth.request_json(
                "POST", f"/teams/{team_id}/sensors/{mac}", json=body
            )
        )

    async def submit_samples(self, team_id: str, samples: list[Sample]) -> SubmitResult:
        """Submit sensor readings for a team's plants."""
        if not samples:
            return SubmitResult()
        return SubmitResult.from_dict(
            await self._auth.request_json(
                "POST",
                f"/teams/{team_id}/samples",
                json={"samples": [sample.as_dict() for sample in samples]},
            )
        )
