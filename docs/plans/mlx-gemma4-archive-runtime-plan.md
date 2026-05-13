# MLX Gemma 4 Archive Runtime Plan

## Steps

1. Add a backend MLX runtime module with the Gemma 4 model registry, server lifecycle, health checks, and chat completion call.
2. Route archive intelligence and the benchmark through the MLX runtime instead of the Ollama Python client.
3. Update job request defaults and `/models` to expose MLX model identifiers and metadata.
4. Remove Ollama startup/model-registration behavior and replace it with an MLX availability check.
5. Replace the backend dependency on `ollama` with `mlx-vlm`.
6. Delete the unused Ollama Modelfile.
7. Update README, agent skill docs, and the architecture playground to describe the MLX flow.
8. Switch archive chapter generation from JSON to XML and benchmark XML against JSON.
9. Verify Python modules compile and frontend lint/build checks catch model selector regressions.
