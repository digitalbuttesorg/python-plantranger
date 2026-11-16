# Change Log

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this
project adheres to [Semantic Versioning](http://semver.org/).

## [0.2.0] - 2026-11-14

### Added

- `get_sensor()`, `register_sensor()` and `submit_samples()`, with the
  `SensorStatus`, `Sample`, `SubmitResult` and `RejectedSample` models.
- `PlantRangerForbiddenError` (403, a subclass of `PlantRangerAuthError`) and
  `PlantRangerAccountActionError` (400 `ACCOUNT_ACTION_REQUIRED`).
- A test suite, run with `make test`.

### Changed

- `AbstractAuth.request_json()` replaces `get_json()` and also sends JSON bodies.
- A 502, 503 or 504 raises `PlantRangerConnectionError`.

## [0.1.0] - 2026-09-27

### Added

- Initial release: `PlantRangerClient` with `get_teams()`, `get_team()` and
  `get_plant()`, driven by a caller-supplied `AbstractAuth`.
