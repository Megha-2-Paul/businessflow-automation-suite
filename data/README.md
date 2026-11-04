# Public dataset storage

Place downloaded public source datasets in `raw/` only after checking their
licence, attribution, redistribution terms, and privacy implications.

- `raw/`: unchanged source files; excluded from Git by default.
- `processed/`: reproducible transformed outputs; excluded from Git by default.
- `metadata/`: provenance manifests and checksums. Commit only metadata that
  does not expose personal or restricted information.

Do not commit private business data, credentials, or restricted source files.
