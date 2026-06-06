# Deliverable Provenance and Quality Evals Spec

Date: 2026-06-05

## Intent

Smart YouTube Reader deliverables must explain how they were produced. A reader,
maintainer, or reviewer should be able to open a generated `archive.json` or
`manifest.json` and answer:

- Which local runtime and model generated the chapters?
- Was chapter image selection model-assisted or deterministic?
- Which candidate frames were considered and why was the selected image accepted?
- Did the pipeline repair transcript gaps, parse fallbacks, or missing visual data?

This closes the current provenance gap where an archive can show
`_image_selection.method: ollama_vision` but cannot prove the exact text model
runtime used for the deliverable.

## Six-Month Durability

Even if local model runners, YouTube tools, or AI assistants improve over the
next six months, this remains useful because the durable layer is the verified
artifact contract: local provenance, image-selection evidence, and quality gates
that make a digest auditable after generation. Better models make this evidence
more important, not less, because users need to compare outputs and trust what
changed.

## Contract

New archive-generation jobs write a top-level `provenance` object to both
`archive.json` and `manifest.json`.

Required shape:

```json
{
  "schema_version": 1,
  "app": {
    "name": "smart-youtube-reader",
    "commit": "git-or-env-sha-or-null"
  },
  "runtime": {
    "provider": "ollama",
    "model": "gemma4:12b",
    "host": "http://127.0.0.1:11434",
    "capabilities": ["text", "image"],
    "installed": true,
    "digest": "ollama-model-digest-if-known"
  },
  "generation": {
    "archive_prompt_version": "archive-schema-json-v1",
    "archive_response_format": "schema_json",
    "archive_schema_attempts": 2,
    "archive_json_attempts": 1,
    "archive_xml_attempts": 1,
    "vision_prompt_version": "vision-frame-selection-v1",
    "vision_frame_candidates": 6,
    "max_images_per_chapter": 2
  }
}
```

Fields may be omitted only when the source runtime cannot provide them. Missing
optional data must not fail generation.

Each chapter writes `_image_selection` with:

- `schema_version`
- `method`: `ollama_vision` or `deterministic`
- `model` and `provider` when a model call was attempted
- `selected_images`
- bounded candidate frame evidence (`filename`, timestamp, quality signals)
- `fallback_reason` when deterministic selection replaced vision

## Cross-Platform Requirements

- Persist portable relative frame paths such as `frames/0001.png`; never persist
  absolute local filesystem paths in archive or manifest provenance.
- Use JSON primitives only: strings, numbers, booleans, arrays, objects, and
  `null`.
- Use POSIX-style archive paths in JSON (`frames/name.png`) regardless of
  Windows, macOS, or Linux host path separators.
- Do not require `git`, `ollama show`, or an internet connection to write a
  valid archive. Optional details may be `null` or absent.
- Existing archives without `provenance` remain readable.

## Non-Goals

- No remote telemetry.
- No cloud analytics.
- No raw audio model path.
- No fallback to retired Hugging Face, MLX, or text-only local model providers.
- No broad UI workflow for rating deliverables in this first slice.

## Acceptance Gates

- Backend tests prove model/runtime provenance is JSON-safe and cross-platform.
- Backend tests prove image-selection metadata records selected images and
  candidate evidence for both vision and deterministic fallback paths.
- Backend tests prove archive path rewriting uses `frames/...` paths and does
  not introduce OS-specific separators.
- `backend/.venv/bin/python -m pytest` passes locally.
- `backend/.venv/bin/ruff check .` passes locally.
- GitHub Actions backend CI passes on Ubuntu, macOS, and Windows.
