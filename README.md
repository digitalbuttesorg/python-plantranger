# python-plantranger

Asynchronous client for the [Plant Ranger](https://www.plantranger.com) API, built for the
Home Assistant `plant_ranger` integration.

The client does not manage OAuth tokens itself. Subclass `AbstractAuth` and implement
`async_get_access_token()` so the caller stays in charge of refreshing:

```python
from aiohttp import ClientSession
from plantranger import AbstractAuth, PlantRangerClient


class MyAuth(AbstractAuth):
    async def async_get_access_token(self) -> str:
        return "..."


async with ClientSession() as session:
    client = PlantRangerClient(MyAuth(session))
    for team in await client.get_teams():
        detail = await client.get_team(team.id)
        for plant in detail.plants:
            print(plant.name, plant.moisture, plant.needs_water)
```

## API

- `get_teams()` — teams the token can see
- `get_team(team_id)` — a team with plant and bridge summaries
- `get_plant(plant_id)` — full plant detail
- `get_sensor(team_id, mac)` — what a sensor is to a team: `unregistered`, `in_team`,
  `other_team` or `not_a_sensor`
- `register_sensor(team_id, mac, plant_name, location=None)` — create a plant for a sensor,
  or return the one it already has
- `submit_samples(team_id, samples)` — submit up to 100 readings; returns the accepted count
  and the rejected samples with a reason

Errors raise `PlantRangerAuthError` (401), `PlantRangerForbiddenError` (403, a subclass of
`PlantRangerAuthError`), `PlantRangerAccountActionError` (400 `ACCOUNT_ACTION_REQUIRED`),
`PlantRangerConnectionError` (transport, 408, 502, 503 or 504) or `PlantRangerError` (everything else).

## Testing

Needs Python 3.12 or newer.

```bash
make test       # pytest with coverage
make lint       # ruff, codespell, zizmor, yamllint
make typecheck  # mypy
make check      # all of the above, same as CI
```

To run the hooks on every commit:

```bash
.venv/bin/pre-commit install
```

## Pointing at a local server

Set both environment variables before starting the process that imports the library:

```bash
export PLANTRANGER_API_HOST=http://localhost:8080
export PLANTRANGER_WEB_HOST=http://localhost:4000
```

`API_HOST` is used for the API, `WEB_HOST` for the OAuth authorize and token endpoints.

## Releasing

Releases publish to PyPI from GitHub Actions when a `v*` tag is pushed. The
workflow refuses to publish if the tag does not match `__version__`.

1. Bump `__version__` in `plantranger/__init__.py` and add a section to
   `CHANGELOG.md`.
2. Commit, then tag and push:

```bash
git tag v0.1.0
git push origin main v0.1.0
```

Publishing uses PyPI Trusted Publishing against the `pypi` GitHub environment,
so no API token is stored in the repo.
