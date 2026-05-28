# Share Mode Toggle Spec

**Date:** 2026-05-27
**Owner:** Ehukai Media
**Status:** Active

## Goal

Give users an explicit choice between **Local** and **Tailscale** sharing for the project link copied from the dashboard or reader. Replace the previous implicit "auto-Tailscale when accessed from localhost" behavior with a transparent toggle that can also explain itself when Tailscale is not installed or not running.

## Behavior

### Modes

- **Local** — share links use the same host the browser is currently using (e.g. `http://localhost:3001`). This is the default for a fresh user.
- **Tailscale** — share links use the machine's tailnet IP (e.g. `http://100.x.y.z:3001`) so other devices on the same tailnet can open the link.

Selection persists in `localStorage` under `smart-reader-share-mode`. The dashboard exposes the toggle in its toolbar.

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
  "share_origin": "..."
}
```

When Tailscale is unavailable, `modes.tailscale.share_origin` is `null` and `modes.tailscale.status` is one of:

| Status | Meaning |
|---|---|
| `not_installed` | The `tailscale` CLI is not on PATH (and no tailnet IP could be inferred from `ifconfig` or `hostname`). |
| `not_running` | The CLI is present but the command failed (typically not logged in / stopped). |
| `no_tailnet_ip` | The CLI succeeded but no `100.64.0.0/10` address was returned. |

`PUBLIC_SHARE_ORIGIN` remains a hard override: when set, both modes return that origin and `configured_override` is `true`. The frontend hides the toggle in that case.

The previous top-level `share_origin` field has been removed. Frontend clients must read `modes.<mode>.share_origin`.

### Frontend

- A "Share links use: [Local] [Tailscale]" pill toggle lives in the dashboard toolbar (hidden when `configured_override` is `true`).
- Copying a project link uses the persisted mode. If the user has chosen Tailscale but Tailscale is unavailable, the copy is aborted and an inline help message + toast point to the right next step (install, run `tailscale up`, etc.).
- The reader page reads the same persisted mode for its own "Copy Project Link" action; it relies on the dashboard for changing the mode rather than duplicating the toggle UI.

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
- No per-project share mode override; the toggle is a single global preference.
- No backend-side change to anything outside `/share-info` and its helper functions.

## Acceptance Criteria

- `/share-info` returns the `modes` shape above; legacy `share_origin` field still works.
- Dashboard renders a Local / Tailscale pill toggle that persists across reloads.
- Tailscale-unavailable selection surfaces a clear next-step hint linking to the install page and mentioning `tailscale up`.
- When `PUBLIC_SHARE_ORIGIN` is set, the toggle is hidden and both modes return the override.
- New backend tests cover the four `_tailscale_status()` branches and the override path.
- README has a "Sharing" section that documents both modes and the install command.
