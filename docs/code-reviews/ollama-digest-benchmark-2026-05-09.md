# Ollama Digest Benchmark - 2026-05-09

> **Superseded — 2026-05-27.** This benchmark covers the Ollama-based `smart-youtube-digest` model. That path has been replaced: archive generation now uses MLX-VLM (see `docs/specs/mlx-gemma4-archive-runtime.md`) and digest creation is handled by an external-agent CLI (see README §AI Digest Workflow). The following artifacts referenced here no longer exist: `backend/modelfiles/smart-youtube-digest.Modelfile`, `tools/benchmark_digest_model.py`, `docs/specs/ollama-ai-digest.md`. The findings below are historical only.

## Model

- Base: `gemma4:latest`
- Local model: `smart-youtube-digest`
- Modelfile: `backend/modelfiles/smart-youtube-digest.Modelfile`
- Benchmark: `python3 tools/benchmark_digest_model.py --runs 1`

## Quality Gates

- Raw JSON object output.
- No-fluff title.
- Fewer chapters than source when source has more than three chapters.
- Valid integer `source_indices`.
- Numeric ordered timestamps.
- Sufficient teaching content.
- Non-empty `changes_summary`.
- Image references preserved from kept source chapters for human curation.

## Results

| Archive | Source Chapters | Digest Chapters | Compression | Images Preserved | Time | Result |
|---|---:|---:|---:|---:|---:|---|
| `how-to-master-volume-profile-trading-in-less-than-15-minutes-and-never-guess-market-direction-again_e68163e9` | 17 | 6 | 0.35 | 16/16 | 46.6s | PASS |
| `introduction-to-volume-profiles-on-tradingview-tutorial_cb887f63` | 11 | 3 | 0.27 | 17/17 | 44.1s | PASS |

## Notes

The first benchmark attempt failed because Gemma returned one text label in `source_indices` and omitted `changes_summary`. The Modelfile and runtime prompt were tightened with an explicit required JSON shape and integer-only `source_indices`; the rerun passed.
