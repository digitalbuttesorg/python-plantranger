"""Models for the Plant Ranger API."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Self


def _parse_datetime(value: Any) -> datetime | None:
    """Parse an API timestamp, tolerating nulls and empty strings."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _float(value: Any) -> float | None:
    """Coerce an API number, tolerating nulls."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


@dataclass(frozen=True, kw_only=True)
class TeamListItem:
    """A team the token has access to."""

    id: str
    name: str | None = None
    owner_id: str | None = None
    role: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build from an API payload."""
        return cls(
            id=data["id"],
            name=data.get("name"),
            owner_id=data.get("owner_id"),
            role=data.get("role"),
        )


@dataclass(frozen=True, kw_only=True)
class TeamStats:
    """Aggregate counts for a team."""

    devices_online: int = 0
    needs_attention: int = 0
    ok_plants: int = 0
    total_plants: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build from an API payload."""
        return cls(
            devices_online=data.get("devices_online") or 0,
            needs_attention=data.get("needs_attention") or 0,
            ok_plants=data.get("ok_plants") or 0,
            total_plants=data.get("total_plants") or 0,
        )


@dataclass(frozen=True, kw_only=True)
class BridgeSummary:
    """A Plant Ranger bridge."""

    id: str
    name: str | None = None
    device_type: str | None = None
    location: str | None = None
    mac_address: str | None = None
    offline: bool = False
    registered: bool = False
    status: str | None = None
    version: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build from an API payload."""
        return cls(
            id=data["id"],
            name=data.get("name"),
            device_type=data.get("device_type"),
            location=data.get("location"),
            mac_address=data.get("mac_address"),
            offline=bool(data.get("offline")),
            registered=bool(data.get("registered")),
            status=data.get("status"),
            version=data.get("version"),
        )


@dataclass(frozen=True, kw_only=True)
class PlantSummary:
    """A plant with its most recent readings."""

    id: str
    name: str | None = None
    species: str | None = None
    location: str | None = None
    mac_address: str | None = None
    status: str | None = None
    last_checkup: datetime | None = None

    battery: float | None = None
    conductivity: float | None = None
    humidity: float | None = None
    light: float | None = None
    moisture: float | None = None
    signal_strength: float | None = None
    temperature: float | None = None

    needs_water: bool = False
    offline: bool = False
    low_battery: bool = False
    low_signal: bool = False
    out_of_range: bool = False
    conductivity_alert: bool = False
    humidity_alert: bool = False
    light_alert: bool = False
    moisture_alert: bool = False
    rssi_alert: bool = False
    temperature_alert: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build from an API payload."""
        return cls(
            id=data["id"],
            name=data.get("name"),
            species=data.get("species"),
            location=data.get("location"),
            mac_address=data.get("mac_address"),
            status=data.get("status"),
            last_checkup=_parse_datetime(data.get("last_checkup")),
            battery=_float(data.get("battery")),
            conductivity=_float(data.get("conductivity")),
            humidity=_float(data.get("humidity")),
            light=_float(data.get("light")),
            moisture=_float(data.get("moisture")),
            signal_strength=_float(data.get("signal_strength")),
            temperature=_float(data.get("temperature")),
            needs_water=bool(data.get("needs_water")),
            offline=bool(data.get("offline")),
            low_battery=bool(data.get("low_battery")),
            low_signal=bool(data.get("low_signal")),
            out_of_range=bool(data.get("out_of_range")),
            conductivity_alert=bool(data.get("conductivity_alert")),
            humidity_alert=bool(data.get("humidity_alert")),
            light_alert=bool(data.get("light_alert")),
            moisture_alert=bool(data.get("moisture_alert")),
            rssi_alert=bool(data.get("rssi_alert")),
            temperature_alert=bool(data.get("temperature_alert")),
        )


@dataclass(frozen=True, kw_only=True)
class Team:
    """A team with its plant and bridge summaries."""

    id: str
    name: str | None = None
    owner_id: str | None = None
    email_enabled: bool = False
    last_accessed: datetime | None = None
    stats: TeamStats = field(default_factory=TeamStats)
    plants: list[PlantSummary] = field(default_factory=list)
    bridges: list[BridgeSummary] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build from an API payload."""
        return cls(
            id=data["id"],
            name=data.get("name"),
            owner_id=data.get("owner_id"),
            email_enabled=bool(data.get("email_enabled")),
            last_accessed=_parse_datetime(data.get("last_accessed")),
            stats=TeamStats.from_dict(data.get("stats") or {}),
            plants=[
                PlantSummary.from_dict(plant) for plant in data.get("plants") or []
            ],
            bridges=[
                BridgeSummary.from_dict(bridge) for bridge in data.get("bridges") or []
            ],
        )


@dataclass(frozen=True, kw_only=True)
class SpeciesCare:
    """Care guidance for a species."""

    light: str | None = None
    soil: str | None = None
    water: str | None = None
    temperature_description: str | None = None
    min_temperature_c: float | None = None
    max_temperature_c: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build from an API payload."""
        return cls(
            light=data.get("light"),
            soil=data.get("soil"),
            water=data.get("water"),
            temperature_description=data.get("temperature_description"),
            min_temperature_c=_float(data.get("min_temperature_c")),
            max_temperature_c=_float(data.get("max_temperature_c")),
        )


@dataclass(frozen=True, kw_only=True)
class SpeciesData:
    """Reference data for a species."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    habitat: str | None = None
    region: str | None = None
    common_names: list[str] = field(default_factory=list)
    care: SpeciesCare = field(default_factory=SpeciesCare)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build from an API payload."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            habitat=data.get("habitat"),
            region=data.get("region"),
            common_names=list(data.get("common_names") or []),
            care=SpeciesCare.from_dict(data.get("care") or {}),
        )


@dataclass(frozen=True, kw_only=True)
class FullPlant:
    """Complete detail for a single plant."""

    id: str
    name: str | None = None
    species: str | None = None
    location: str | None = None
    mac_address: str | None = None
    serial_num: str | None = None
    team_id: str | None = None
    team_name: str | None = None
    last_checkup: datetime | None = None
    next_checkup: datetime | None = None
    species_data: SpeciesData = field(default_factory=SpeciesData)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Build from an API payload."""
        return cls(
            id=data["id"],
            name=data.get("name"),
            species=data.get("species"),
            location=data.get("location"),
            mac_address=data.get("mac_address"),
            serial_num=data.get("serial_num"),
            team_id=data.get("team_id"),
            team_name=data.get("team_name"),
            last_checkup=_parse_datetime(data.get("last_checkup")),
            next_checkup=_parse_datetime(data.get("next_checkup")),
            species_data=SpeciesData.from_dict(data.get("species_data") or {}),
        )
