# HF Gemma 4 QAT Evaluation and Model-Candidate Gate Plan

Date: 2026-06-10

Spec: `docs/specs/hf-gemma4-qat-model-evaluation.md`
Playground: `docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html`
Evidence: `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/`

## Goal

Decide, on local evidence, whether `hf.co/google/gemma-4-12B-it-qat-q4_0-gguf` should
replace `gemma4:12b` as the Smart YouTube Reader default model — and leave behind a
reusable, dormant migration recipe plus a standing benchmark gate so future candidates
are decided the same way.

## Executed Phases (all complete, 2026-06-10)

1. **Candidate verification.** Confirmed the official Google HF repo ships Q4_0 QAT weights
   plus the `mmproj` vision projector; license Apache-2.0; published 2026-06-04/05
   (inside the 7-day quarantine window — proceeded as an explicit user-approved evaluation;
   the NO-GO outcome ships nothing from the artifact).
2. **Integration proof.** Pulled via `ollama pull hf.co/google/gemma-4-12B-it-qat-q4_0-gguf`;
   Ollama 0.30.7 registered vision + clip projector. Smoke-tested text, JSON-schema
   structured output, and image input through the unchanged `model_runtime.chat()` boundary.
   Confirmed the `:latest`-tagged name satisfies `check_model()` and both launchers'
   exact-match install checks.
3. **Benchmark comparison.** Ran identical suites per model (54 text calls + 22 vision
   selections each) with warm-ups, 100% GPU residency, and committed raw logs. Results and
   protocol are in the spec; verdict below.

## Decision Point — reached

**NO-GO.** The candidate is not faster (10.77 vs 10.80 s/call overall; 11.41 vs 10.33 on
the production schema-JSON path) and is less accurate (schema pass rate 16.7% vs 44.4%;
systematic chapter-count over-segmentation; one vision fallback vs none). `gemma4:12b`
stays the default. No code, launcher, or doc-default change ships.

## Dormant Migration Recipe

Apply only when a candidate passes the standing gate in the spec. The entire swap is:

1. `backend/app/model_runtime.py:13` — change the `SMART_READER_MODEL` fallback to the
   candidate tag (for HF pulls, always the `:latest`-tagged form, e.g.
   `hf.co/google/gemma-4-12B-it-qat-q4_0-gguf:latest`).
2. `backend/app/model_runtime.py:15-48` — replace the superseded catalog entry in
   `AVAILABLE_MODELS` (name, label, size, `recommended: True`,
   `capabilities: ["text", "image"]`) so `/models` and provenance metadata stay truthful.
   Remove the losing entry; do not keep both 12B-class entries.
3. `start.sh:37` and `start.ps1:191` — update the launcher default model string
   (pull logic is generic; `ollama pull` accepts `hf.co/...` refs unchanged).
4. Docs: `README.md` model lines, `CONTRIBUTING.md:33` prerequisite, CHANGELOG entry.
5. Tests: update tags asserted in `backend/tests/test_model_runtime.py` and
   `backend/tests/test_models_api.py`; run
   `backend\.venv\Scripts\python.exe -m pytest` and `ruff check .` from `backend/`.
6. Verification: re-run the spec's benchmark suites on the new default and commit results
   under `docs/benchmarks/`; update `docs/specs/ollama-vision-runtime.md` and the
   architecture playground in the same change (playground-architect supersession rules).
7. Provenance: confirm a fresh job records the new `provenance.runtime.model` and digest.

## Follow-Ups (not started)

- **Params-matched re-run**: extend `backend/benchmark_model.py` with `--top-k/--top-p`
  passthrough to `options` so HF imports compare under Gemma-recommended sampling
  (`top_k=64, top_p=0.95`); re-test the QAT candidate once.
- **Machine-readable benchmark output**: a `--json <path>` flag writing the summary object
  (agent-ergonomics; today's summaries were parsed from stdout logs).
- **Re-evaluation triggers** (watch, no action): Google QAT GGUF re-upload or an Ollama
  library `-it-qat` tag; Ollama kernel changes for Q4_0 vs Q4_K_M; chaptering contract
  changes. Any trigger -> re-run the suites per the spec gate.

## Rollback

Nothing to roll back — the evaluation ships documentation and evidence only. The pulled
candidate model can be removed locally with
`ollama rm hf.co/google/gemma-4-12B-it-qat-q4_0-gguf:latest` to reclaim 7.2 GB.

## Cross-Platform Notes

- The evaluation ran on Windows 11 (the platform the prior fallback plan flagged as least
  proven); macOS/Linux speed ratios may differ but the accuracy verdict is hardware-neutral.
- No Hugging Face, Torch, or MLX Python dependencies were added at any point; the HF
  artifact flows through Ollama's own registry client, keeping
  `docs/plans/schema-json-archive-fallback-2026-06-05.md` constraints intact.
