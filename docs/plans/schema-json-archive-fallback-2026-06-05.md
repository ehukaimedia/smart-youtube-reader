# Schema JSON Archive Fallback Plan

Date: 2026-06-05

## Goal

Make Gemma 4 12B archive generation more reliable on Windows without changing the local-first Ollama runtime that already works on macOS.

## Plan

1. Route chaptering through Ollama JSON Schema structured output first.
2. Keep prompt-only JSON and XML parsing as compatibility fallbacks for older runtimes or ignored format instructions.
3. Replace parse-only chunk failure with transcript-grounded deterministic chapters so one malformed model response does not fail a full archive.
4. Preserve hard failures for missing models, Ollama connection errors, and other runtime failures.
5. Update tests, README, changelog, runtime spec, and the architecture playground.

## Cross-Platform Notes

- Use the existing Ollama HTTP API path on Windows, macOS, and Linux.
- Do not add Hugging Face, Torch, MLX, or platform-specific model dependencies.
- Avoid Unix-only benchmark timeout behavior by falling back to HTTP request timeouts on Windows.
