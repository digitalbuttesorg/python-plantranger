"""Exceptions raised by the Plant Ranger client."""


class PlantRangerError(Exception):
    """Base error for the Plant Ranger API."""


class PlantRangerAuthError(PlantRangerError):
    """The token was rejected."""


class PlantRangerConnectionError(PlantRangerError):
    """The API could not be reached."""
