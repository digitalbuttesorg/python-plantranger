"""Exceptions raised by the Plant Ranger client."""


class PlantRangerError(Exception):
    """Base error for the Plant Ranger API."""


class PlantRangerAuthError(PlantRangerError):
    """The token was rejected."""


class PlantRangerForbiddenError(PlantRangerAuthError):
    """The token is not allowed to do this."""


class PlantRangerAccountActionError(PlantRangerError):
    """The account needs attention on the Plant Ranger website."""


class PlantRangerConnectionError(PlantRangerError):
    """The API could not be reached or is unavailable."""
