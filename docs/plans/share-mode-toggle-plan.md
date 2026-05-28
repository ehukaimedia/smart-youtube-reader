# Share Mode Toggle Plan

**Spec:** `docs/specs/share-mode-toggle.md`
**Branch:** `claude/share-toggle-local-tailscale`

## Steps

1. Refactor `_get_tailscale_ip()` in `backend/app/main.py` into `_tailscale_status()`, returning `{ip, status}` with status one of `available`, `not_installed`, `not_running`, `no_tailnet_ip`. Keep the existing fallback scans (`ifconfig`, `getaddrinfo`) so users on a tailnet without the CLI still get a working share origin.
2. Reshape `GET /share-info` to return both modes plus availability metadata, preserving the legacy top-level `share_origin` field and respecting `PUBLIC_SHARE_ORIGIN` as an override that collapses both modes.
3. Replace `getShareOrigin()` in `frontend/src/lib/api.ts` with `getShareInfo()` plus `readStoredShareMode` / `writeStoredShareMode` helpers and a `resolveShareOrigin(info, mode)` accessor.
4. Add a Local / Tailscale pill toggle to the dashboard toolbar; persist the choice in `localStorage` under `smart-reader-share-mode`; show inline help when Tailscale is selected but unavailable.
5. Update the reader's `copyProjectLink` to use the same persisted mode and emit a toast if Tailscale is selected but unavailable.
6. Style the toggle in `frontend/src/app/globals.css`.
7. Update related specs that referenced the implicit Tailscale auto-mode (`docs/specs/project-zip-download.md`, `docs/specs/ai-digest-version.md`, `docs/specs/group-ai-digest.md`).
8. Add a "Sharing" section to `README.md` describing both modes, the Tailscale install command (`brew install --cask tailscale` then `tailscale up`), and the install URL.
9. Add backend tests (`backend/tests/test_share_info.py`) for the four `_tailscale_status()` branches and the `/share-info` response shape with and without `PUBLIC_SHARE_ORIGIN`.
10. Verify: backend `pytest`, frontend `npm run lint`, frontend `npm run build`.

## Out of Scope

- AI digest prompt text and default-WebP behavior.
- Anything that ships a Tailscale installer or runs `tailscale up` on the user's behalf.
- LAN/mDNS-style share modes.
