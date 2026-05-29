# Codex Manual Application Review - 2026-05-27

## Findings

- Fixed: the active install was running from a branch behind public `main`, so it did not include the merged Local/Tailscale sharing toggle or default WebP AI digest workflow.
- Fixed: after bringing the feature commits into the active install, `Copy AI Digest CLI Task` was still easy to miss because it lived in the reader overflow menu. It is now a visible source-project action in the reader toolbar; the text-only fallback remains in overflow.

## Manual Verification

- Dashboard loads at `http://localhost:3001/dashboard`.
- Local/Tailscale share mode toolbar renders with `Local` as the default.
- Switching to `Tailscale` persists `smart-reader-share-mode=tailscale` in `localStorage`.
- Switching back to `Local` persists `smart-reader-share-mode=local`.
- `/share-info` reports `default_mode: local`, `configured_override: false`, and available Local/Tailscale origins on this machine.
- Source reader loads for job `68116872-0a46-40bc-8c54-6819a988bbbf` (`This One Prompt Unlocks ChatGPT Images 2.0`).
- Reader toolbar renders `Copy AI Digest CLI Task` as a visible default action.
- Default digest clipboard prompt includes generated WebP teaching images, recommends Codex with GPT 2.0 image generation, and does not include `--text-only`.
- Reader overflow still renders `Copy Text-Only AI Digest Task`; its clipboard prompt includes `--text-only`.
- `Copy Project Link` respects the selected share mode:
  - Tailscale: `http://100.100.104.91:3001/reader/...`
  - Local: `http://localhost:3001/reader/...`
- Source-project `Open Slicer` route opens successfully.
- Mobile dashboard and reader render without action-bar overflow at 390px width.

Screenshots captured during review:

- `/tmp/syr-dashboard-share-toggle.png`
- `/tmp/syr-reader-default-ai-digest.png`
- `/tmp/syr-slicer.png`
- `/tmp/syr-dashboard-mobile.png`
- `/tmp/syr-reader-mobile.png`

## Automated Verification

- Backend: `31 passed in 0.34s`
- Frontend lint: `0 errors, 5 warnings`
  - Existing `@next/next/no-img-element` warnings remain in reader and slicer image rendering.
- Frontend build: passed with Next.js 16.1.3 / Turbopack.

## Residual Risk

- This machine has Tailscale available, so the not-installed/not-running dashboard help path was not reproduced by changing system state during manual QA. Backend tests cover `not_installed`, `not_running`, `no_tailnet_ip`, available, and override behavior in `backend/tests/test_share_info.py`.
