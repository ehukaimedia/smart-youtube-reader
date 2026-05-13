# MLX Gemma 4 Archive Runtime Spec

## Context

Archive generation should run through MLX-hosted Gemma 4 models directly instead of an Ollama-created `smart-reader` model. The backend owns transcript chunking, prompt construction, frame ranking, and archive persistence; the local model runtime should only provide chat completions.

## Expected Behavior

- The default archive model is `mlx-community/gemma-4-e4b-it-4bit`.
- `/models` exposes the supported MLX Gemma 4 model registry and marks which model, if any, is already loaded by the local MLX server.
- Archive generation starts or reuses an `mlx_vlm.server` process on `127.0.0.1:11435`.
- MLX chat calls use the MLX-VLM OpenAI-compatible `/v1/chat/completions` endpoint.
- Archive generation asks Gemma 4 for XML chapters and parses `<archive><chapter>...</chapter></archive>` instead of relying on JSON.
- Model weights are cached under `data/mlx/` by default, with `MLX_MODELS_DIR` available as an override.
- Runtime configuration can override the default model with `SMART_READER_MODEL`.
- The archive prompt remains transcript-grounded and returns XML chapters; JSON is used only as a repair fallback after XML parse retries fail.

## Non-Goals

- Do not require Ollama, Modelfiles, or an `ollama serve` process.
- Do not reintroduce cloud model providers for initial archive generation.
- Do not move image selection into model vision calls; frame ranking remains metadata-driven.
