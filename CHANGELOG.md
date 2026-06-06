# Changelog

All notable changes to Smart YouTube Reader are documented here.

This project follows the spirit of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning starts at the first public baseline, `0.1.0`.

## [Unreleased]

### Added

- Added archive and manifest provenance metadata so generated deliverables record the local runtime, model, prompt contract, and image-selection evidence.

### Fixed

- Fixed Unix launcher Tailscale IP detection so share mode allows tailnet-origin Next.js dev assets without cross-origin warnings.
- Fixed dashboard card overflow menus so opening `⋯` does not shift the page or show the native browser tooltip.
- Prevented derived AI digest projects from inheriting source archive provenance as if it described the external-agent digest itself.

## [0.1.0] - 2026-06-01

### Added

- Local-first YouTube archive pipeline that produces transcripts, de-duplicated frames, semantic chapters, and `manifest.json` metadata under `data/jobs/`.
- Next.js dashboard, reader, slicer, and bundled demo digest projects for first-run exploration.
- External-agent digest workflows for single-project AI digests, text-only digests, group AI digests, and summary thumbnails.
- Local/Tailscale sharing mode with `PUBLIC_SHARE_ORIGIN` support for reverse-proxy deployments.
- Contributor, security, license, and third-party notice documents for public open-source review.
- Backend `requirements.lock` generated with `uv` and installed by CI for reproducible backend checks.

### Changed

- Launchers bootstrap missing backend/frontend dependencies and bind to localhost by default; LAN/tailnet exposure is opt-in with `SYR_SHARE=1`.
- README setup, platform, Node runtime, first-run model download, and verification guidance now match the code and CI surface.
- Frontend linting fails on warnings, and backend CI runs ruff plus the backend pytest suite.

### Security

- Restricted backend CORS to local/tailnet frontend origins rather than wildcard-with-credentials behavior.
- Hardened slicer selected-file handling against path traversal outside the preview directory.
- Removed unused OpenAI dependency from the backend dependency spec.

### Fixed

- Restored-job metadata now uses manifest status and schema defaults instead of stale guessed values.
- Digest prompt text is centralized so dashboard and reader copy tasks stay byte-identical.
- Agent skill attribution now covers the checked-in Impeccable port and vendored browser helper copies.
