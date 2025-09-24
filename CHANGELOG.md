# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-09-24
### Added
- `vep-prepare-pipeline` one-shot CLI to run **filter → normalise → merge → overview**.
- `vep-overview` console alias (alongside `vep-parsing-overview`) for consistency.
- Rich, step-by-step logging in the pipeline wrapper.
- Documentation suggestions (Makefile, CI, README Quickstart).

### Changed
- Minor polish in logging/diagnostics for merge step (prints join overlap stats).

### Fixed
- Ensured all entry points are exposed via `pyproject.toml`.

## [0.1.0] - 2025-09-24
### Added
- Initial MCP parser tools:
  - `vep-filter-consequence-mane`
  - `vep-normalise-columns`
  - `vep-merge-gnomad-constraint`
  - `vep-parsing-overview`
- Example schemas: `VEP_RAW.schema.json`, `ANNOTATION_NORMALISED.schema.json`, `GNOMAD_CONSTRAINT.schema.json`.
- Tiny, reproducible test fixtures and basic pytest suite.

---

## Unreleased
### Planned
- Optional `vep-validate` CLI for schema validation of outputs.
- `-` stdin/stdout support for all CLIs for easier agent composition.
- JSON log mode for machine parsing.
