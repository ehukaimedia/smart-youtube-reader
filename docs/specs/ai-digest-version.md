# AI Digest Version Spec

## Context

Smart YouTube Reader projects should preserve the original archive while allowing users to create a separate AI-optimized version for agent learning. The digest version should reduce wasted context from filler transcript sections and low-value images, then behave like any other project for reader, dashboard, Tailscale sharing, and ZIP download.

## Expected Behavior

- Reader exposes a `Create AI Digest Version` action for completed source projects.
- The action offers headless agent model choices:
  - Headless GPT 5.5
  - Headless Opus 4.7
  - Local deterministic digest
- Summary images are created outside the backend by Codex after inspecting the current project's real archive text and frame images.
- Prompt-only summary image generation is not acceptable because it can miss visual context from charts, slides, diagrams, and screenshots.
- AI digest projects provide a `Copy Codex Image Task` action that includes the local CLI command for generating the image from the current archive and frame assets.
- The summary thumbnail CLI writes `generated/summary.png` and updates `archive.json` and `manifest.json` with `summary_image`.
- When a digest has a generated summary image, dashboard project cards use that image as the project thumbnail instead of the YouTube thumbnail.
- The backend creates a new completed project directory under `data/jobs/`.
- The original project is not modified.
- The derived project receives a new no-fluff title based on the lesson content, not the source YouTube headline.
- The derived `manifest.json` and `archive.json` store lineage fields:
  - `kind: ai_digest`
  - `source_job_id`
  - `source_folder`
  - `digest_model`
  - `digest_agent_status`
  - `changes_summary`
  - `summary_image` when Codex attaches a summary image
- Dashboard cards identify derived projects with an `AI Digest` badge.
- Derived projects use the same reader, download, learning prompt, and Tailscale link behavior as regular projects.

## Fallback Behavior

If a selected headless provider is not configured or fails, the backend must fail the digest request clearly. Deterministic compaction is allowed only when the user explicitly selects `Local deterministic digest`.

## Non-Goals

- Do not delete source media or frame files.
- Do not overwrite the original archive.
- Do not require provider keys before showing the digest action.
