---
name: smart-youtube-reader-help-demo
description: Create, repair, or update the bundled Smart YouTube Reader help/demo digest that teaches the app and showcases the default Codex + GPT 2.0 generated-WebP digest deliverable. Use when Codex is asked to make the default help digest, README showcase visuals, first-run demo project, demo AI digest assets, or proof-of-value onboarding content for this repository.
---

# Smart YouTube Reader Help Demo

## Overview

Build a shipped proof project, not just documentation. The help demo should appear in the dashboard, open from the top-nav Help link, teach how to use Smart YouTube Reader, and show a polished generated-image AI digest deliverable.

## Required Shape

- Store tracked source assets under `examples/demo-jobs/smart-youtube-reader-demo-digest_demo/`.
- Do not commit runtime `data/` output. `data/` is ignored and should be seeded from `examples/demo-jobs/`.
- Use stable job id `demo-smart-youtube-reader-digest` unless a migration explicitly requires a new id.
- Keep the demo `kind` as `ai_digest`, `digest_model` as `Codex + GPT 2.0 images`, and `media_policy` as `lightweight_generated_images_only`.
- Save teaching visuals as WebP under `generated/`; target 16:9, 1280x720, and roughly 50-100 KB per image.
- Keep generated images novel teaching visuals. Do not copy source frames, YouTube thumbnails, product logos, OpenAI logos, Tailscale logos, or copyrighted UI.

## Workflow

1. Inspect current app behavior and schema:
   - `backend/app/jobs.py`
   - `frontend/src/app/components/Navbar.tsx`
   - `frontend/src/app/dashboard/page.tsx`
   - `frontend/src/app/reader/[jobId]/page.tsx`
   - existing examples under `examples/demo-jobs/`
2. If visuals are missing or stale, use the `imagegen` skill to generate raster teaching visuals.
   - Convert selected outputs to WebP with `cwebp -q 82 -resize 1280 720`.
   - Copy final WebP assets into `examples/demo-jobs/smart-youtube-reader-demo-digest_demo/generated/`.
   - Leave original generated images in `$CODEX_HOME/generated_images/`.
3. Create or update:
   - `manifest.json`
   - `archive.json`
   - `transcript.json`
   - `generated/*.webp`
4. Ensure the backend seeds example jobs:
   - `backend/app/jobs.py` should copy missing folders from `examples/demo-jobs/` into `data/jobs/` before loading jobs.
   - Never overwrite a user's existing runtime demo folder.
5. Ensure the frontend exposes the proof:
   - Top nav `Help` link opens `/reader/demo-smart-youtube-reader-digest`.
   - Dashboard should show the seeded demo card after `/jobs` loads.
   - README should include the demo visuals near the top so GitHub visitors see the proof immediately.
6. Update specs when behavior changes:
   - `docs/specs/ai-digest-version.md`
   - `docs/specs/share-mode-toggle.md` if the demo teaches global Local/Tailscale behavior.
   - relevant playground docs if the dashboard or reader architecture changes.

## Demo Content

The demo should teach five jobs-to-be-done:

1. Turn a video URL into a structured local archive.
2. Use Reader chapters, transcript, timestamps, and evidence images as AI-ready context.
3. Create the default AI digest with Codex and GPT 2.0 generated WebP teaching images.
4. Combine multiple archives into a group digest that creates a new lesson.
5. Use the global Local/Tailscale app mode to open the dashboard through localhost or a private tailnet IP.

Keep writing concrete and product-facing. The demo is both help content and a marketing proof point, so each chapter should explain the time-saving deliverable rather than describing implementation trivia.

## Validation

Run the relevant checks after changes:

- `python3 -m pytest tests` from `backend/` when backend logic changes.
- `npm run lint` from `frontend/`.
- `npm run build` from `frontend/`.
- Render the running app and verify:
  - `/dashboard` shows `Smart YouTube Reader Demo Digest`.
  - `/reader/demo-smart-youtube-reader-digest` opens from the Help link.
  - Demo images load from `/data/jobs/smart-youtube-reader-demo-digest_demo/generated/*.webp`.
  - The README image paths render from `examples/demo-jobs/...`.

## Safety

- Do not touch user-owned dirty workspace moves such as `skills/impeccable/**` relocations unless explicitly asked.
- Do not commit `data/`, `node_modules/`, `.next/`, or temporary screenshots.
- Keep repo-bundled visuals small. If the example folder grows beyond about 1 MB, reduce WebP dimensions or quality.
- Avoid claiming the demo was generated from a real video. It is a bundled help digest and should say so honestly.
