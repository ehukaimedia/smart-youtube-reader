# Handoff: HF Gemma 4 QAT Model Evaluation (Claude, 2026-06-10)

Branch: `docs/hf-gemma4-qat-model-evaluation`

## What was asked

Replace the default local model `gemma4:12b` (Ollama) with the Hugging Face QAT release
`hf.co/google/gemma-4-12B-it-qat-q4_0-gguf`, claimed faster and more accurate, and prove
the claim with a benchmark comparison; deliver playground + spec + plan + benchmarks on a
PR branch.

## What actually happened

The claim was tested and **did not hold on this app's workload**, so the deliverables
record an evidence-based **NO-GO** instead of a migration:

- Integration itself works: the HF GGUF (weights + mmproj vision projector) pulls through
  Ollama's native `hf.co/` registry, registers vision, and runs the app's text,
  schema-JSON, and image paths unchanged. The dormant migration recipe is in the plan.
- Across 54 identical text calls + 22 vision selections per model (warm, 100% GPU,
  RTX 5070, Ollama 0.30.7): candidate pass rate 20.4% vs baseline 29.6%; production
  schema-JSON path 16.7% vs 44.4% pass and +10.5% latency; errors 14 vs 10; systematic
  chapter-count over-segmentation (6-7 chapters vs the 2-5 contract, 3/3 schema runs on
  the TED-Ed job); one vision fallback vs none. Speed overall: statistically identical.
- A standing model-candidate benchmark gate now governs any future default-model swap.

## Artifacts on this branch

- `docs/specs/hf-gemma4-qat-model-evaluation.md` — decision spec: identity, integration
  contract, protocol, full results, caveats, standing gate, durability.
- `docs/plans/hf-gemma4-qat-evaluation-and-model-gate-2026-06-10.md` — executed phases,
  decision, dormant migration recipe, verification steps, follow-ups, rollback.
- `docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html` — self-contained decision
  playground with interactive benchmark explorer and Spec Seed (verified rendering, no
  console errors).
- `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/` — environment identity, 8 raw
  suite logs, GPU-residency proofs, `summary.json`, and `parse_logs.py` (re-running it
  reproduces `summary.json` byte-identically — verified).
- `docs/specs/ollama-vision-runtime.md` — one line added pointing default-model decisions
  at the standing gate.

## Known limitations (also in the spec)

- Sampling params not fully matched (library modelfile `top_k=64/top_p=0.95` vs HF-import
  runtime defaults) at the app's `temperature=0.1`; params-matched re-run is a follow-up.
- Single machine (Windows 11, RTX 5070 12 GB); speed ratios are hardware-specific.
- Candidate GGUF shows irregular stop tokens (`<|turn>` variants) — early template
  conversion; a re-upload is a re-evaluation trigger.

## How to verify cold

1. `git checkout docs/hf-gemma4-qat-model-evaluation`
2. Recompute the summary: `backend\.venv\Scripts\python.exe docs\benchmarks\gemma4-12b-qat-vs-q4km-2026-06-10\parse_logs.py`
   then `git diff --stat` must be empty.
3. Cross-check the spec's tables against `summary.json`.
4. Open the playground HTML in a browser; the explorer's `schema_json total` view must
   show 44%/17%, 3.72/2.83, 10.33s/11.41s, 8/10.
5. (Full repro, ~25 min GPU time) run the commands in
   `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/environment.txt` — exact numbers
   vary per run; direction of every signal should hold.
6. Confirm no runtime code changed: `git diff main --stat -- backend frontend start.sh start.ps1 start.command` is empty.
