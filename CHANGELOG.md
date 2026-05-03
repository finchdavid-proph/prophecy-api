# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `docs/METHODS.md` — full reference table for all 19 client methods (18 endpoints + 1 polling helper) with status, endpoint path, and purpose. Linked from the README.
- `prophecy identify <resource>.<method> [--arg KEY=VALUE ...]` CLI subcommand — live-probes a method against the configured instance and classifies the outcome (WORKS / BROKEN / UNVERIFIED). Useful for verifying Dedicated SaaS endpoints, sanity-checking new tokens, or scoping endpoints not yet documented. Arg values are coerced via `int → JSON → str`.
- 8 unit tests for the `identify` subcommand covering WORKS / API-error BROKEN / HTTP-error BROKEN / UNVERIFIED and bad-input rejection paths.

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
