# Project ZIP Download Spec

## Context

The reader page had a "Download AI Archive" control that linked directly to a completed job's `archive.json`. That only exported the semantic chapter JSON, not the full generated project.

## Expected Behavior

When a job is complete, the reader page must offer a project ZIP download. The ZIP must include the completed job directory as a top-level folder, including generated files such as:

- `archive.json`
- `manifest.json`
- `transcript.json`
- `frames.json`
- `frames/`
- `slices/`
- `playground.html`
- downloaded video files

The API must serve the ZIP as `application/zip` with an attachment filename so downloads work across the frontend/backend port boundary.

The dashboard and completed project page must also expose a project share link. The dashboard offers a Local / Tailscale toggle (see `docs/specs/share-mode-toggle.md`); copied links use whichever mode the user has selected. When Tailscale is selected, the backend resolves the machine's tailnet IP and returns a share origin such as `http://<tailscale-ip>:3001`, so copied links work from another computer on the same tailnet. When Local is selected (the default), copied links use the same host the browser is currently using.

## Non-Goals

- Do not zip the source-code repository from this action.
- Do not persist generated ZIP files in `data/jobs/`.
- Do not change the existing static `/data/jobs/.../archive.json` route.
