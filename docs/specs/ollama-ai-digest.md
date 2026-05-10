# Ollama AI Digest Spec

## Context

AI digest creation should not require OpenAI or Anthropic API keys. Smart YouTube Reader should offer a local Ollama-backed Gemma digest model that cuts transcript fluff while leaving image replacement and removal to the human curation flow.

## Expected Behavior

- The app exposes `Local Gemma AI Digest` as the primary AI digest model.
- The Ollama model is created from `backend/modelfiles/smart-youtube-digest.Modelfile`.
- The model uses `gemma4:latest` as its base.
- The backend calls local Ollama through `/api/chat`; no provider API key is required.
- The model returns raw JSON with `title`, `chapters`, and `changes_summary`.
- Digest chapters include `source_indices`, `concept`, `summary`, `content`, `timestamp_start`, and `timestamp_end`.
- The backend preserves image references from kept source chapters.
- The backend must not remove, replace, or judge images during AI digest creation.
- Human users handle image removal and replacement through the reader and slicer workflows.
- If the Ollama model is missing or Ollama is unavailable, the model should show as unavailable instead of requiring an API key.

## Quality Gates

The benchmark must pass before treating the local model as ready:

- Output parses as a JSON object.
- Output has a no-fluff title that does not reuse common hype words.
- Output has at least one chapter and fewer chapters than the source when the source has more than three chapters.
- Every digest chapter maps to valid source indices.
- Every timestamp is numeric and ordered.
- Average content length is sufficient for teaching context.
- Changes summary explicitly describes the digest edits.
- Preserved image count equals images from kept source chapters.

## Non-Goals

- Do not use OpenAI, Anthropic, or other paid hosted model APIs for digest generation.
- Do not automate poor-image removal in the digest agent.
- Do not make summary thumbnail generation part of the backend digest request.
