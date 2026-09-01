# Changelog

All notable changes to the EDITED API Use Case Guides are recorded here.
This project follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

## [1.1.1] - 2026-09-01

### Fixed
- **Products Export guide** — deduplicated repeated Product Types values (two
  taxonomy IDs resolving to the same display string no longer render twice)
  and excluded taxonomy nodes flagged `visible: false`, matching the UI export.
- Clarified that Product Types is reconstructed via a join between the record's
  taxonomy IDs and the `GET /schema/v1/searches` endpoint, not from fields
  already present on the record.
- Corrected the guide's explanation of Product Types comma ordering: it is not
  a UI-side detail, and cannot be reproduced — compare that column as a set.

## [1.1.0] - 2026-07-13

### Added
- **Products Export guide** (`products-export-guide/`) — converts Jobs API output
  (NDJSON) into a CSV matching the Products tab of the standard UI list export.
  Documents the full field-by-field transformation mapping and reconstructs the
  Product Types hierarchy from the `searches` taxonomy.

## [1.0.1] - 2026-04-29

### Added
- Region configuration for Jobs API use cases.

### Fixed
- Bug fixes in the historical options guide and supporting `editedapi` modules.

## [1.0.0] - 2026-01-27

### Added
- Initial release of the EDITED API Use Case Guides: brand watchlist, colour
  analysis, historical options, and tariff tracker guides, plus the shared
  `editedapi` module.
