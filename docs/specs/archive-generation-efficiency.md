# Archive Generation Efficiency Spec

## Context

The first archive pass should produce useful AI-readable chapters and representative images without requiring app-managed API keys or per-frame vision calls. The app's model dropdown should expose supported MLX Gemma 4 models, defaulting to `mlx-community/gemma-4-e4b-it-4bit`.

## Expected Behavior

- Archive generation uses local MLX chat only.
- `mlx-community/gemma-4-e4b-it-4bit` is the default in-app archive model.
- API-backed NVIDIA/NIM models are not shown in `/models` and are not routed by `backend/app/intelligence.py`.
- The model receives compact timestamped transcript evidence so it can choose chapter boundaries from explicit seconds rather than guessing from a plain text blob.
- The prompt tells the model to create no-fluff learning chapters, merge low-value transitions, preserve durable concepts, and return XML only.
- Initial chapter images are selected from `frames.json` metadata using timestamp proximity, visual signal, duplicate avoidance, and fallback nearest-frame behavior.
- `FrameManager` records cheap local visual quality metadata while it already has each frame open for pHash indexing.
- Archive chapters may include `_image_context` metadata for selected frames so the reader can show timestamp and quality signals without another backend call.
- The reader gives operators a chapter-level slicer entry point plus per-image replace/remove controls, so poor initial visual context can be corrected without deleting source files.

## Non-Goals

- Do not reintroduce backend-hosted AI digest generation.
- Do not use app-managed cloud API keys for initial archive generation.
- Do not ask a model to remove or replace poor images; human image curation remains a reader/slicer workflow.
