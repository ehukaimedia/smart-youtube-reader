---
name: smart-youtube-reader-help-demo
description: Use when building, repairing, or updating the bundled Smart YouTube Reader help/demo digest that teaches the app and showcases the default generated-WebP digest deliverable — including the Claude Opus 4.8 demo variant, the dashboard/Help-link first-run proof project, README showcase visuals, or demo AI digest assets for this repository.
---

# Smart YouTube Reader Help Demo

## Overview

Build a shipped proof project, not just documentation. The help demo should appear in the dashboard, open from the top-nav Help link, teach how to use Smart YouTube Reader, and show a polished generated-image AI digest deliverable.

**Required gate:** the Impeccable skill governs all AI digest image work. Before generating or updating any teaching image, load the design context (`IMPECCABLE_CONTEXT_DIR=docs/impeccable`) and follow the "Generated Image Art Direction" section of `docs/impeccable/DESIGN.md`. The bar is premium product-marketing quality. Every image must pass that section's acceptance checklist before it ships. This is not optional and is the difference between a proof point and AI slop.

## Required Shape

- Store tracked source assets under `examples/demo-jobs/<demo-folder>/`. The backend example loader copies every folder there into `data/jobs/`, so each demo folder must be self-contained.
- The bundled demo ships in provider variants so users can compare image outputs. Keep the existing folders intact and add new providers alongside them:
  - `smart-youtube-reader-demo-digest_demo` -> job id `demo-smart-youtube-reader-digest` (Codex GPT 5.5 variant).
  - `smart-youtube-reader-gemini` -> job id `demo-smart-youtube-reader-gemini` (Gemini variant).
  - `smart-youtube-reader-claude` -> job id `demo-smart-youtube-reader-claude` (Claude Opus 4.8 variant).
- Do not commit runtime `data/` output. `data/` is ignored and should be seeded from `examples/demo-jobs/`.
- Use stable job ids; do not rename an existing variant's id unless a migration explicitly requires it.
- Keep the demo `kind` as `ai_digest`, `media_policy` as `lightweight_generated_images_only`, and set `digest_model` to the variant's honest pipeline label (for the Claude Opus 4.8 variant: `Claude Opus 4.8 images`; never imply a model the variant did not use).
- Save teaching visuals as WebP under `generated/`; target 16:9, 1280x720, and roughly 30-100 KB per image.
- Keep generated images novel teaching visuals. Do not copy source frames, YouTube thumbnails, product logos, source-brand logos, or copyrighted UI.
- The bundled demo should show both infographic modes when assets are available: a simple text-led card strip and a premium image-led card strip for each chapter.

## Workflow

1. Inspect current app behavior and schema:
   - `backend/app/jobs.py`
   - `frontend/src/app/components/Navbar.tsx`
   - `frontend/src/app/dashboard/page.tsx`
   - `frontend/src/app/reader/[jobId]/page.tsx`
   - existing examples under `examples/demo-jobs/`
2. If visuals are missing or stale, generate new teaching visuals. The Impeccable skill is required for this step:
   - First load the design context: run Impeccable with `IMPECCABLE_CONTEXT_DIR=docs/impeccable` and read the "Generated Image Art Direction" section of `docs/impeccable/DESIGN.md`.
   - Build each image with either the `simple-infographic` or `premium-infographic` skill, bound to the project bar in `docs/impeccable/DESIGN.md` §7. Simple images are quiet text-led card strips. Premium images are image-led card strips. In both modes: one calm idea per image, an eyebrow label plus one bold tight headline (Inter, large and tight), generous whitespace, a restrained palette with Operator Blue `#3b82f6` at most, and no static plus buttons, carousel arrows, pagination dots, or navigation controls.
   - Produce the bitmap with the path the harness supports. **Claude Opus 4.8 variant:** author each card as a complete HTML/CSS/SVG editorial composition and render it to 1280x720 raster with headless Chrome (Playwright `channel="chrome"`, or the chrome-devtools MCP). This is the genuine Claude Opus 4.8-generated artifact — never a thin vector placeholder. A harness with a native image model may instead generate the focal bitmap with that model.
   - Every image must pass the section's acceptance checklist before use. If an image cannot meet the bar, ship fewer images and note the gap in `operator_image_note`; never ship an off-brand image to fill a slot.
   - Convert selected outputs to WebP with `cwebp -q 82 -resize 1280 720`.
   - Copy final WebP assets into `examples/demo-jobs/<demo-folder>/generated/`.
3. Create or update for the variant:
   - `manifest.json`
   - `archive.json`
   - `transcript.json`
   - `generated/*.webp`
4. Ensure the backend seeds example jobs:
   - `backend/app/jobs.py` should copy missing folders from `examples/demo-jobs/` into `data/jobs/` before loading jobs.
   - Never overwrite a user's existing runtime demo folder.
5. Ensure the frontend exposes the proof:
   - Top nav `Help` link opens the demo reader; its active state should cover every demo variant reader path (`/reader/demo-smart-youtube-reader-digest`, `/reader/demo-smart-youtube-reader-gemini`, `/reader/demo-smart-youtube-reader-claude`).
   - A provider switcher in the demo reading experience lets users compare Codex, Gemini, and Claude image versions. Keep it restrained and work-focused, not a marketing page.
   - Dashboard should show the seeded demo cards after `/jobs` loads.
   - README should include the demo visuals and note that the selector compares the provider variants.
6. Update specs when behavior changes:
   - `docs/specs/ai-digest-version.md`
   - `docs/specs/share-mode-toggle.md` if the demo teaches global Local/Tailscale behavior.
   - relevant playground docs if the dashboard or reader architecture changes.

## Reproducible image pipeline (Claude path)

The runnable tooling for the Claude image path lives in this skill's `scripts/`, so you do not rebuild the toolchain each time. This is the fast path; it removes the setup work, not the design judgment.

- `scripts/setup_fonts.sh [dir]` fetches Inter woff2 into `fonts/` (Inter is not installed system-wide).
- `scripts/infographic_kit.py` provides `simple_page`, `premium_page`, `node`, `arrow`, `glyph`, `write_pages`. Its theme tokens, glyph library, and light/dark card templates already satisfy the `docs/impeccable/DESIGN.md` Section 7 checklist (Inter, Operator Blue `#3b82f6` as the only accent, committed theme, no decorative shadows, no rainbow, no fake controls).
- `scripts/render_to_webp.py <html_dir> <out_dir>` renders each HTML with headless Chrome (Playwright `channel="chrome"`) at 2x, then `cwebp` to 1280x720 WebP.

Fast path:

1. `bash <skill>/scripts/setup_fonts.sh fonts`
2. Write a short generator that imports the kit and builds one `simple_page` (light, 4-6 cards) and one `premium_page` (dark, a focal `node()`/`arrow()` flow or panel) per chapter. Keep simple = light, premium = dark; that is the Claude identity. One calm idea, tight headline, fully written labels.
3. Smoke-test the toolchain first: `python3 <skill>/scripts/infographic_kit.py` then `python3 <skill>/scripts/render_to_webp.py _kit_example/html _kit_example/out`. Then render your set into the demo folder's `generated/`.
4. Render one premium card and get a thumbs-up before producing the rest. Validate every image against the Section 7 checklist and confirm 1280x720 WebP.

A harness with a native image model can skip this and use that model instead; the kit is the path for Claude Opus 4.8 when native image generation is unavailable.

## Demo Content

The demo should teach five jobs-to-be-done:

1. Turn a video URL into a structured local archive.
2. Use Reader chapters, transcript, timestamps, and evidence images as AI-ready context.
3. Create the default AI digest with generated WebP teaching images.
4. Combine multiple archives into a group digest that creates a new lesson.
5. Use the global Local/Tailscale app mode to open the dashboard through localhost or a private tailnet IP.

Keep writing concrete and product-facing. The demo is both help content and a marketing proof point, so each chapter should explain the time-saving deliverable rather than describing implementation trivia.

## Validation

Run the relevant checks after changes:

- `python3 -m pytest tests` from `backend/` when backend logic changes.
- `npm run lint` from `frontend/`.
- `npm run build` from `frontend/`.
- Confirm every generated image is 1280x720 WebP and that `archive.json`, `manifest.json`, and `transcript.json` parse as JSON.
- Render the running app and verify:
  - `/dashboard` shows the demo digest cards.
  - The Help link opens the demo reader and the provider switcher reaches each variant.
  - Demo images load from `/data/jobs/<demo-folder>/generated/*.webp`.
  - The README image paths render from `examples/demo-jobs/...`.

## Safety

- Do not touch user-owned dirty workspace moves such as `skills/impeccable/**` relocations unless explicitly asked.
- Do not commit `data/`, `node_modules/`, `.next/`, or temporary screenshots.
- Keep repo-bundled visuals small. If a demo folder grows beyond about 1 MB, reduce WebP dimensions or quality.
- Avoid claiming the demo was generated from a real video. It is a bundled help digest and should say so honestly.
- Keep each variant's metadata honest about which agent and image pipeline produced it.
