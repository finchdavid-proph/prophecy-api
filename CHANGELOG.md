# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-01

### Added

- Initial release wrapping all 18 endpoints in the Prophecy REST API:
  - `pipelines`: trigger, get_run_status, run_and_wait
  - `projects`: deploy, run_data_tests
  - `fabrics`: create, get, update, delete
  - `connections`: create, list, get, update, delete
  - `secrets`: create, list, get, update, delete
- Resource-namespaced API: `client.pipelines.trigger()`, `client.fabrics.create()`, ...
- `prophecy` CLI with hierarchical subcommands (`prophecy <resource> <action>`).
- Typed exception hierarchy (`ProphecyError`, `ProphecyHTTPError`, `ProphecyAPIError`).
- Automatic retry on 5xx / 429 for idempotent verbs.
- `ProphecyClient.from_env()` builder using `PROPHECY_BASE_URL` / `PROPHECY_TOKEN`.

[Unreleased]: https://github.com/finchdavid-proph/prophecy-api/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/finchdavid-proph/prophecy-api/releases/tag/v0.1.0
