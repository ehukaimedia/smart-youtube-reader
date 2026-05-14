# Group AI Digest Spec

## Context

Users need to combine several Smart YouTube Reader projects into one higher-level learning artifact. A group digest is not a playlist export and not a merge of source archives. It is a new project built from multiple source transcripts and frame evidence, with a novel transcript and novel teaching images.

## Expected Behavior

- Dashboard lets the user select completed projects into a temporary group.
- Dashboard exposes `Copy Group AI Digest CLI Task` for the selected group.
- The copied task runs a local CLI that prints a complete external-agent workflow.
- The external agent reads every selected source `archive.json` and inspects the attached frame images before writing the combined draft.
- The group digest draft creates a new transcript, not a concatenation of source transcripts.
- The new transcript must be intuitive and teach durable facts, theory, and testable hypotheses.
- The group prompt uses the same specificity-preservation policy as single-video digests: numeric claims, proper nouns, dataset/benchmark names, named teams/companies, and concrete examples that materially support the lesson must survive synthesis.
- Each source chapter in the group task includes `preservation_items`; agents use these as a merge checklist when many source chapters collapse into one cross-video chapter.
- Each chapter must include:
  - `facts`: compact source-grounded facts
  - `theory`: why the facts fit together into a reusable model
  - `hypothesis`: what the model predicts, or what would invalidate it
- The group digest output uses exactly three new generated teaching images.
- The three output images must be created from the new combined transcript and visual evidence; they must not be copied source frames, YouTube thumbnails, or screenshots.
- Source frames are allowed only as evidence during synthesis.
- The group digest materializer creates a new completed project under `data/jobs/` with:
  - `kind: group_ai_digest`
  - `digest_model: external-agent-cli`
  - `source_job_ids`
  - `source_folders`
  - `source_titles`
  - `generated_images`
  - `summary_image` set to the first generated teaching image
- Each archive chapter references one of the three generated images.
- The reader and dashboard show a `Group AI Digest` badge.
- The original projects and their AI digest versions are never modified.
- Group digests retain normal Tailscale sharing, ZIP download, learning prompt, and dashboard behavior.

## CLI Behavior

`tools/create_group_ai_digest_version.py` accepts two or more project references. Without `--draft`, it prints the task and creates a staging folder for the draft and image files. With `--draft`, it validates the draft, checks that exactly three generated image files exist, and materializes the new group digest project.

The draft must include:

- `title`
- `learning_objective`
- `changes_summary`
- `images`: exactly three objects with `path`, `title`, and `alt`
- `chapters`: one or more chapters with `concept`, `summary`, `content`, `facts`, `theory`, `hypothesis`, `image_path`, `source_refs`, `timestamp_start`, and `timestamp_end`

The materializer rejects drafts that are too extractive from the source text. Shared technical terms are expected, but long copied source phrasing indicates the output is not a novel transcript.

## Non-Goals

- Do not build a backend-hosted group digest model.
- Do not use original frame paths in the group output archive.
- Do not generate deterministic fallback images.
- Do not overwrite or mutate source projects.
- Do not create a shallow summary that lacks facts, theory, or hypotheses.
