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

The dashboard and completed project page must also expose a project share link. The dashboard must show the actual Tailscale URL on each card, not only a local "Open Project" route. When the app is opened from `localhost`, the backend must resolve the machine's Tailscale IP and return a share origin such as `http://<tailscale-ip>:3001`, so copied links work from another computer.

## Non-Goals

- Do not zip the source-code repository from this action.
- Do not persist generated ZIP files in `data/jobs/`.
- Do not change the existing static `/data/jobs/.../archive.json` route.
