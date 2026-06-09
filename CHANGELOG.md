# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-06-09

### Changed
- **Default port changed from 6666 to 7777.** Chromium and Firefox
  hard-block 6666 (IRC's well-known port) with `ERR_UNSAFE_PORT`,
  silently breaking the dashboard in browsers. 7777 is unblocked
  everywhere we tested.

## [0.1.0] - 2026-06-09

### Added
- Initial release.
- Auto-discovery of local TCP listening ports via `psutil`.
- Concurrent async HTTP probing with `httpx` and `<title>` extraction.
- FastAPI backend serving JSON API and static dashboard.
- Glassmorphism Tailwind + Alpine.js dashboard with dark-mode support.
- User / system service classification.
- Search, auto-refresh, and 5-second TTL cache.
- One-line `start.sh` / `stop.sh` scripts.
