# AI Digest Version Spec

## Context

Smart YouTube Reader projects should preserve the original archive while allowing users to create a separate AI-optimized version for agent learning. The default digest version should reduce wasted context from filler transcript sections and create lightweight generated WebP teaching images, then behave like any other project for reader, dashboard, Tailscale sharing, and ZIP download. A text-only fallback remains available when users intentionally want source image references for human curation.

## Expected Behavior

- Reader exposes `Copy AI Digest CLI Task` as the default generated-WebP image digest action for completed source projects.
- Reader exposes a secondary `Copy Text-Only AI Digest Task` action for completed source projects when users want to preserve source image references.
- Each action copies a CLI-driven workflow that any external agent can run.
- `tools/create_ai_digest_version.py <project>` prints the default image-rich WebP task.
- `tools/create_ai_digest_version.py <project> --text-only` prints the fallback text-only task.
- The backend does not offer local digest model choices or deterministic digest generation.
- Summary images are created outside the backend by Codex after inspecting the current project's real archive text and frame images.
- Prompt-only summary image generation is not acceptable because it can miss visual context from charts, slides, diagrams, and screenshots.
- The reader does not expose a separate image-only CLI task.
- The default AI digest task requires one novel generated WebP teaching image per digest chapter, with at most 6 images total.
- If an agent decides the digest truly needs more than 6 images, it must keep the best 6-image digest and explain the needed count for the operator.
- The summary thumbnail CLI writes `generated/summary.webp` and updates `archive.json` and `manifest.json` with `summary_image`.
- When a digest has a generated summary image, dashboard project cards use that image as the project thumbnail instead of the YouTube thumbnail.
- The digest CLI creates a new completed project directory under `data/jobs/`.
- The original project is not modified.
- The derived project receives a new no-fluff title based on the lesson content, not the source YouTube headline.
- The text-only digest agent preserves image references from kept source chapters. Human users handle image removal and replacement.
- The digest prompt includes deterministic `preservation_items` for each source chapter. These items are extracted from archive text plus the matching transcript slice so small local models see high-signal metrics, named teams, benchmarks, and concrete examples even when a source chapter is aggressively merged.
- When the prompt asks the agent to merge chapters, it treats `preservation_items` as a checklist and preserves claim direction. For example, a source claim that a method used more compute must not be rewritten as less compute.
- Specificity preservation dominates the soft 60-80% chapter-count target. A digest that keeps more chapters to preserve concrete claims is preferable to a more compressed digest that drops names, metrics, benchmark results, or company-specific examples.
- The default digest-with-images agent references only safe generated WebP image paths under `generated/`; source frames remain evidence, not output chapter images.
- Digest-with-images projects use `media_policy: lightweight_generated_images_only`.
- Digest-with-images projects do not copy original source frames, source slices, source frame metadata, copied source video, stale generated images, or the original transcript into the derived project.
- Digest-with-images projects write `transcript.json` from the improved digest chapter text only.
- Text-only AI digest projects also write `transcript.json` from the improved digest chapter text only; the source project remains the place to inspect the original transcript.
- ZIP downloads for digest-with-images projects contain only the derived archive metadata, digest transcript, manifest, and referenced generated WebP teaching images.
- The derived `manifest.json` and `archive.json` store lineage fields:
  - `kind: ai_digest`
  - `source_job_id`
  - `source_folder`
  - `digest_model: external-agent-cli`
  - `digest_agent_status`
  - `transcript_policy: digest_transcript_only`
  - `changes_summary`
  - `summary_image` when Codex attaches a summary image
- Dashboard cards identify derived projects with an `AI Digest` badge.
- Derived projects use the same reader, download, learning prompt, and Tailscale link behavior as regular projects.

## CLI Behavior

The CLI prints an agent task when no draft is provided. After the agent writes the draft JSON, the CLI validates source indices, content thickness, timestamp shape, and chapter-count reduction before materializing the new project. Invalid drafts fail clearly and do not modify the source project.

## Non-Goals

- Do not delete source media or frame files.
- Do not overwrite the original archive.
- Do not run a backend-hosted local digest model.
- Do not provide a deterministic digest fallback.
