"""Client for the Plant Ranger API."""

from .auth import AbstractAuth
from .models import FullPlant, Team, TeamListItem


class PlantRangerClient:
    """Read-only client for the Plant Ranger API."""

    def __init__(self, auth: AbstractAuth) -> None:
        """Initialize the client."""
        self._auth = auth

    async def get_teams(self) -> list[TeamListItem]:
        """Return the teams the token has access to."""
        data = await self._auth.get_json("/teams")
        return [TeamListItem.from_dict(team) for team in data.get("teams") or []]

    async def get_team(self, team_id: str) -> Team:
        """Return a team with its plant and bridge summaries."""
        return Team.from_dict(await self._auth.get_json(f"/teams/{team_id}"))

    async def get_plant(self, plant_id: str) -> FullPlant:
        """Return full detail for a single plant."""
        return FullPlant.from_dict(await self._auth.get_json(f"/plants/{plant_id}"))
