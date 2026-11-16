"""Asynchronous client for the Plant Ranger API."""

__version__ = "0.2.0rc2"

from .auth import AbstractAuth
from .client import PlantRangerClient
from .const import (
    API_HOST,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    REJECT_REASON_INVALID_MAC,
    REJECT_REASON_INVALID_SAMPLE,
    REJECT_REASON_NOT_IN_TEAM,
    SENSOR_STATUS_IN_TEAM,
    SENSOR_STATUS_NOT_A_SENSOR,
    SENSOR_STATUS_OTHER_TEAM,
    SENSOR_STATUS_UNREGISTERED,
    WEB_HOST,
)
from .exceptions import (
    PlantRangerAccountActionError,
    PlantRangerAuthError,
    PlantRangerConnectionError,
    PlantRangerError,
    PlantRangerForbiddenError,
)
from .models import (
    BridgeSummary,
    FullPlant,
    PlantSummary,
    RejectedSample,
    Sample,
    SensorStatus,
    SpeciesCare,
    SpeciesData,
    SubmitResult,
    Team,
    TeamListItem,
    TeamStats,
)

__all__ = [
    "API_HOST",
    "OAUTH2_AUTHORIZE",
    "OAUTH2_TOKEN",
    "REJECT_REASON_INVALID_MAC",
    "REJECT_REASON_INVALID_SAMPLE",
    "REJECT_REASON_NOT_IN_TEAM",
    "SENSOR_STATUS_IN_TEAM",
    "SENSOR_STATUS_NOT_A_SENSOR",
    "SENSOR_STATUS_OTHER_TEAM",
    "SENSOR_STATUS_UNREGISTERED",
    "WEB_HOST",
    "AbstractAuth",
    "BridgeSummary",
    "FullPlant",
    "PlantRangerAccountActionError",
    "PlantRangerAuthError",
    "PlantRangerClient",
    "PlantRangerConnectionError",
    "PlantRangerError",
    "PlantRangerForbiddenError",
    "PlantSummary",
    "RejectedSample",
    "Sample",
    "SensorStatus",
    "SpeciesCare",
    "SpeciesData",
    "SubmitResult",
    "Team",
    "TeamListItem",
    "TeamStats",
]
