"""Constants for the Plant Ranger API."""

import os
from typing import Final

# Override both to point a development install at a local Plant Ranger stack, e.g.
#   PLANTRANGER_API_HOST=http://localhost:8080 PLANTRANGER_WEB_HOST=http://localhost:4000
API_HOST: Final = os.environ.get(
    "PLANTRANGER_API_HOST", "https://api.plantranger.com"
).rstrip("/")
WEB_HOST: Final = os.environ.get(
    "PLANTRANGER_WEB_HOST", "https://www.plantranger.com"
).rstrip("/")

API_BASE_PATH: Final = "/v1"

OAUTH2_AUTHORIZE: Final = f"{WEB_HOST}/oauth/authorize"
# Code exchange and refresh both live on the web host; the API only refreshes.
OAUTH2_TOKEN: Final = f"{WEB_HOST}/oauth/token"
