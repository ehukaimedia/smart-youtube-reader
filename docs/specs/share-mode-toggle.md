# Share Mode Toggle Spec

**Date:** 2026-05-27
**Owner:** Ehukai Media
**Status:** Active

## Goal

Give users an explicit global choice between **Local** and **Tailscale** app access. Replace the previous implicit "auto-Tailscale when accessed from localhost" behavior with a transparent toggle that redirects the current app session to the selected origin and also controls project links copied from the dashboard or reader.

## Behavior

### Modes

- **Local** — the app and copied links use localhost for same-machine work. This is the default for a fresh user.
- **Tailscale** — the app and copied links use the machine's tailnet IP (e.g. `http://100.x.y.z:3001`) so other devices on the same tailnet can open the dashboard and project links.

Selection persists in `localStorage` under `smart-reader-share-mode`. The top navigation exposes the toggle globally across dashboard, reader, slicer, and new-project views.

### Backend

`GET /share-info` returns:

```json
{
  "default_mode": "local",
  "modes": {
    "local":     { "share_origin": "http://localhost:3001", "available": true },
    "tailscale": {
      "share_origin": "http://100.64.1.2:3001",
      "available": true,
      "status": "available",
      "install_url": "https://tailscale.com/download/macos"
    }
  },
  "configured_override": false,
  "share_origin": "http://localhost:3001"
}
```

When Tailscale is unavailable, `modes.tailscale.share_origin` is `null` and `modes.tailscale.status` is one of:

| Status | Meaning |
|---|---|
| `not_installed` | The `tailscale` CLI is not on PATH (and no tailnet IP could be inferred from `ifconfig` or `hostname`). |
| `not_running` | The CLI is present but the command failed (typically not logged in / stopped). |
| `no_tailnet_ip` | The CLI succeeded but no `100.64.0.0/10` address was returned. |

`PUBLIC_SHARE_ORIGIN` remains a hard override: when set, both modes return that origin and `configured_override` is `true`. The frontend hides the toggle in that case.

A legacy top-level `share_origin` field is also returned for clients that pre-date the `modes` shape. It mirrors `modes.local.share_origin` when no override is set, and mirrors the override when `PUBLIC_SHARE_ORIGIN` is set. New clients should read `modes.<mode>.share_origin`.

### Frontend

- A global "Local / Tailscale" pill toggle lives in the top navigation (hidden when `configured_override` is `true`).
- Choosing Tailscale redirects the current URL to the Tailscale origin when available. Choosing Local redirects the current URL to the local origin.
- Copying a project link uses the persisted mode. If the user has chosen Tailscale but Tailscale is unavailable, the copy is aborted and a toast points to the right next step (install, run `tailscale up`, etc.).
- `start.command` opens `/dashboard` on the Tailscale origin when a tailnet IP is available, otherwise it falls back to localhost.

### Setup Path (no silent install)

The app never installs Tailscale on the user's behalf. The README documents the install path:

```
brew install --cask tailscale
tailscale up
```

…with a link to <https://tailscale.com/download/macos> for non-Homebrew users.

## Non-Goals

- No automatic / silent install of Tailscale.
- No mDNS or LAN-discovery alternative — Local mode is intentionally just "the browser's current host".
- No per-project share mode override; the toggle is a single global app preference.
- No backend-side change to anything outside `/share-info` and its helper functions.

## Acceptance Criteria

- `/share-info` returns the `modes` shape above; legacy `share_origin` field is preserved and equals `modes.local.share_origin` (or the `PUBLIC_SHARE_ORIGIN` override when set).
- Top navigation renders a Local / Tailscale pill toggle that persists across reloads and redirects the app to the selected origin.
- Tailscale-unavailable selection surfaces a clear next-step hint linking to the install page and mentioning `tailscale up`.
- `start.command` opens the dashboard on `http://<tailnet-ip>:3001/dashboard` when a tailnet IP is available.
- When `PUBLIC_SHARE_ORIGIN` is set, the toggle is hidden and both modes return the override.
- New backend tests cover the four `_tailscale_status()` branches and the override path.
- README has a "Sharing" section that documents both modes and the install command.
