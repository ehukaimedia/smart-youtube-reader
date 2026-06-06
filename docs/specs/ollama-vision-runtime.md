# Ollama Vision Runtime Spec

Date: 2026-06-05

## Intent

Smart YouTube Reader uses one local model runtime: regular Ollama Gemma 4, defaulting to `gemma4:12b`. The app must not keep a retired local-model provider, retired model dependency, or Apple-only local model path.

This spec exists to prevent runtime drift and to make the image-selection contract explicit.

## Current Contract

- `backend/app/model_runtime.py` owns local model configuration, model listing, model checks, runtime metadata, and chat calls.
- `SMART_READER_MODEL` defaults to `gemma4:12b`.
- `OLLAMA_HOST` defaults to `http://127.0.0.1:11434`.
- Chat calls use Ollama `/api/chat` with `stream: false`.
- Runtime messages preserve `images` arrays so image-capable Gemma 4 tags can be used.
- The backend does not send raw audio to the model.
- `/models` exposes the full Gemma 4 catalog as `model_details`, but `models` contains only locally installed Ollama tags that are ready for job creation.
- `/jobs` checks the requested model before creating a new background job so a missing tag fails immediately with a pull/start-Ollama message instead of failing late after download and frame extraction.

## Archive Flow

1. `backend/app/pipeline.py` extracts transcript text and frame images.
2. `backend/app/intelligence.py::_generate_archive_chunk` sends transcript text to the local model for semantic chaptering.
3. `backend/app/intelligence.py::_choose_vision_representative_frames` selects chapter images:
   - build a bounded candidate pool from local frame metadata;
   - resize each candidate frame for efficient Ollama vision input;
   - send the candidate images plus chapter title, summary, and content to Gemma 4;
   - accept only JSON-selected filenames that were in the candidate set;
   - fall back to deterministic frame scoring if the vision call fails or returns invalid output.
4. `archive.json` records selected images, `_image_context`, `_image_selection`, and top-level `provenance` metadata for transparency.
5. `manifest.json` records the requested model and the same top-level `provenance` object so restored jobs and downloaded packages can prove the runtime path.

## Non-Goals

- No retired local-model runtime provider.
- No text-only Gemma 4 local-model tags.
- No raw audio ingestion path.
- No cloud model requirement for initial archive generation.
- No unaudited source-provenance inheritance for derived AI digest projects.

## Acceptance Gates

- The retired-runtime token scan across backend code, launchers, active docs, and frontend source returns no matches.
- `GET /models` lists only installed tags in `models`; uninstalled catalog entries stay metadata-only.
- `POST /jobs` returns a structured `400` before job creation when the requested model is not installed.
- `backend/.venv/bin/python -m pytest` passes.
- `backend/.venv/bin/ruff check .` passes.
- `backend/.venv/bin/python backend/benchmark_model.py --first-chunk-only --formats xml --runs 1` prints `Runtime: Ollama` and `Model: gemma4:12b`.
- A real project benchmark with `archive.json` and `frames.json` emits image-selection rows whose `selection.method` is `ollama_vision` unless Ollama returns an invalid response, in which case `selection.method` is `deterministic` with a `fallback_reason`.
- New archive-generation jobs persist `provenance.runtime.model`, `provenance.runtime.provider`, prompt version metadata, and portable `frames/...` image-selection evidence.
