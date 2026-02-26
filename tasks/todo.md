# Bing Webmaster CLI Implementation Plan

- [x] Confirm API method contracts and request/response wrappers from Microsoft docs
- [x] Scaffold Python package and project metadata for PyPI publishing
- [x] Implement API-key auth (env + local persisted key) and config path helpers
- [x] Implement Bing Webmaster HTTP client with consistent error handling
- [x] Implement CLI commands:
  - [x] `auth login|whoami|clear`
  - [x] `site list`
  - [x] `stats site`
  - [x] `stats url`
  - [x] `url check-index`
  - [x] `url submit`
- [x] Add output rendering helpers (table/json/csv)
- [x] Add automated tests for auth/config/client/CLI behavior
- [x] Write README with setup, auth, commands, and publish instructions
- [x] Add GitHub Actions workflow for trusted publishing to PyPI
- [x] Run tests and validate package build
- [x] Mark all checklist items complete
