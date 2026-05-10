# Ollama AI Digest Plan

## Steps

1. Add a Gemma-based Ollama Modelfile dedicated to AI digest editing.
2. Replace headless API-required digest model options with a local Ollama provider.
3. Route `ollama:smart-youtube-digest` through the local Ollama `/api/chat` endpoint.
4. Preserve image references from kept source chapters and leave removal/replacement to humans.
5. Add a benchmark script that builds the Modelfile and checks digest quality gates against real archives.
6. Update the AI digest specs and architecture playground to show the local Ollama digest path.
7. Run the benchmark until the local model passes quality gates.
8. Run backend and frontend verification before committing.
