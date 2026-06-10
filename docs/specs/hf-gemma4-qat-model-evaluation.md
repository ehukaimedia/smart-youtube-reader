# HF Gemma 4 12B QAT Model Evaluation Spec

Date: 2026-06-10

## Intent

Evaluate replacing the default local model `gemma4:12b` (Ollama library, Q4_K_M) with the
Hugging Face QAT release `hf.co/google/gemma-4-12B-it-qat-q4_0-gguf` (Q4_0,
quantization-aware trained), on the claim that the QAT model is faster and more accurate.
Encode the result as a standing, evidence-based **model-candidate benchmark gate** so the
default model is only ever swapped on local proof, never on release-notes claims.

This spec prevents the anti-pattern of changing the production model contract on
marketing or benchmark claims measured on other hardware, other runtimes, or other tasks.

## Decision

**NO-GO.** Keep `gemma4:12b` as `DEFAULT_MODEL`. On this app's own workload and harness the
QAT candidate is not faster and is measurably less accurate on the production-primary
schema-JSON chaptering path. The integration path is proven and documented below, so any
future candidate that passes the gate can be adopted through the focused runtime, catalog,
launcher, test, and doc updates in the dormant migration recipe.

Runner-up considered: adopting the QAT model as a non-default catalog entry for its lower
VRAM footprint (7.7 GB vs 8.1 GB resident). Rejected: ~400 MB does not change the hardware
class a 12B model needs, and a second 12B catalog entry that loses on the primary path
invites accidental selection.

## Baseline and Candidate Identity

| | Baseline | Candidate |
|---|---|---|
| Tag | `gemma4:12b` | `hf.co/google/gemma-4-12B-it-qat-q4_0-gguf:latest` |
| Source | Ollama library | Hugging Face, Google official (Apache-2.0, published 2026-06-04/05) |
| Architecture | gemma4, 11.9B params, 262144 ctx | gemma4, 11.9B params, 262144 ctx |
| Quantization | Q4_K_M | Q4_0 (quantization-aware trained) |
| Vision projector | clip 52.38M | clip 52.38M (`mmproj-gemma-4-12b-it-qat-q4_0.gguf`) |
| Disk / resident VRAM | 7.6 GB / 8.1 GB | 7.2 GB / 7.7 GB |
| Ollama id | `4eb23ef187e2` | `18a4d9511d99` |

## Integration Contract (verified 2026-06-10)

The candidate runs through the existing runtime unchanged — no new Python dependencies, no
runtime replacement, consistent with `docs/plans/schema-json-archive-fallback-2026-06-05.md`
("no Hugging Face/Torch/MLX dependencies"; the GGUF is pulled *through Ollama's* native
`hf.co/` registry support):

- `ollama pull hf.co/google/gemma-4-12B-it-qat-q4_0-gguf` downloads weights + mmproj;
  Ollama 0.30.7 registers `vision` capability and the clip projector automatically.
- The exact model string must include the `:latest` tag —
  `hf.co/google/gemma-4-12B-it-qat-q4_0-gguf:latest` — because
  `check_model()` (`backend/app/model_runtime.py:149`) and both launchers
  (`start.sh:42`, `start.ps1:196-197`) exact-match names returned by `ollama list`
  / `/api/tags`, which always carry the tag.
- `/api/chat` with `stream: false`, `format` JSON Schema, and base64 `images` all work
  against the candidate through `model_runtime.chat()` (`backend/app/model_runtime.py:168`),
  verified by smoke test and by the full benchmark below.
- A swap would require only: `DEFAULT_MODEL` env default (`backend/app/model_runtime.py:13`),
  an `AVAILABLE_MODELS` catalog entry (`backend/app/model_runtime.py:15`) so
  `runtime_metadata()` provenance records `capabilities: ["text", "image"]`
  (`backend/app/intelligence.py:1264`), launcher defaults (`start.sh:37`, `start.ps1:191`),
  and doc lines (`README.md`, `CONTRIBUTING.md:33`). The frontend follows `/models`
  automatically (`backend/app/main.py:436-450`, `frontend/src/app/page.tsx:71`).

## Benchmark Protocol

Environment, raw logs, and machine identity:
`docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/` (`environment.txt`, `summary.json`,
six raw suite logs plus a second trading round per model). Harness:
`backend/benchmark_model.py` at commit `62215b5`, unmodified. Host: i9-14900KF, 32 GB RAM,
RTX 5070 12 GB, Windows 11, Ollama 0.30.7. Both models ran 100% GPU (see `*-ollama-ps.txt`);
one untimed warm-up call per model preceded its timed suites; suites ran sequentially on an
otherwise idle machine.

Suites (identical commands per model, only `--model` differs):

- **A. sample** — built-in transcript, 1 chunk x 3 formats x 3 runs (9 calls)
- **B. teded** — real job `3-tips-to-boost-your-confidence-ted-ed_06a6dae9` (238 s),
  1 chunk x 3 formats x 3 runs (9 calls) + vision image-selection over 6 chapters
- **C. trading** — real job
  `copy-this-5-rule-smc-trading-strategy-backtested-results_318c1b44` (1641 s),
  6 chunks x 3 formats, two independent rounds (36 calls) + vision image-selection
  over 8 chapters per round

Quality is the harness's 7-gate score (valid format, required keys, timestamps in window,
2-5 chapter count, no markdown fences, no fluff titles, >=0.84 transcript word-overlap
grounding); "pass" means 7/7. Timing is wall-clock seconds per call.

## Results

### Text chaptering — all formats, 54 calls per model

| Metric | Baseline Q4_K_M | Candidate QAT Q4_0 |
|---|---|---|
| Pass rate (7/7 gates) | **29.6%** (16/54) | 20.4% (11/54) |
| Avg quality (0-7) | **4.74** | 4.41 |
| Avg seconds/call | 10.80 | 10.77 |
| Parse/format errors | **10** | 14 |

### Production-primary path — schema_json only, 18 calls per model

The app requests Ollama structured output (JSON Schema `format`) first; this is the path
that decides real archive quality.

| Metric | Baseline Q4_K_M | Candidate QAT Q4_0 |
|---|---|---|
| Pass rate | **44.4%** (8/18) | 16.7% (3/18) |
| Avg quality | **3.72** | 2.83 |
| Avg seconds/call | **10.33** | 11.41 (+10.5%) |
| Malformed-output errors | **8** | 10 |

### Per-suite pass counts (passed/calls, all formats)

| Suite | Baseline | Candidate |
|---|---|---|
| A sample | 6/9 | 6/9 |
| B teded | **5/9** | 3/9 |
| C trading round 1 | **2/18** | 1/18 |
| C trading round 2 | **3/18** | 1/18 |

### Vision image selection — 22 chapters per model

| Metric | Baseline | Candidate |
|---|---|---|
| `ollama_vision` selections | **22/22** | 21/22 (1 deterministic fallback) |
| Avg visual score per suite | 0.185 / 0.175 / 0.183 | 0.132 / 0.155 / 0.153 |

### Characterized failure mode

On the 238 s TED-Ed video the contract expects 2-5 chapters. The candidate over-segmented
in **all three** schema runs (6, 7, 6 chapters — `count_ok` gate); the baseline complied in
two of three (5, 6, 5). On the trading job both models produce malformed JSON under schema
constraints (shared harness/runtime weakness, max-tokens truncation among the causes), but
the candidate errored more often in both rounds (5 vs 4, 5 vs 4 in round 2 per-format logs).

## Caveats (stated, not hidden)

- **Sampling parameters were not identical.** The Ollama-library baseline carries modelfile
  defaults `top_k=64, top_p=0.95`; the HF import has no sampling params, so Ollama runtime
  defaults applied. Both ran at the app's explicit `temperature=0.1`, where top-k/top-p
  influence is small but nonzero. A params-matched re-run is listed as follow-up in the plan.
- **Single machine.** Speed conclusions are specific to RTX 5070/Windows/Ollama 0.30.7
  kernels; the accuracy gap (schema pass rate, systematic over-segmentation) is unlikely to
  flip on other hardware.
- **Sample size** is 54 text calls + 22 vision selections per model. Small per-cell, but
  every directional signal points the same way; nothing supports "faster and more accurate".
- **Candidate GGUF template roughness.** `ollama show` reports irregular stop tokens for the
  HF import (`<|turn>`, `<turn|>`, `<|turn>user`), suggesting early GGUF chat-template
  conversion; a revised upload could change results — see re-evaluation triggers.

## Artifact Pinning Note

The 7-day module quarantine in the OSS standard applies to code dependencies (npm/pip
packages, GitHub Actions, container images), not to model weights from a first-party
vendor; no quarantine applied to this evaluation. Model artifacts are still identity-pinned:
any adopted model records its exact digest (`ollama show` id — here `18a4d9511d99`) in the
spec so provenance and reproductions reference one immutable artifact.

## Standing Model-Candidate Gate

A future candidate may replace `DEFAULT_MODEL` only when, on the same machine class, same
harness, same suites, and matched sampling parameters:

1. schema_json pass rate >= baseline + 10 percentage points, or equal pass rate with
   >= 20% lower avg seconds/call;
2. no regression in overall pass rate or error count;
3. vision selection keeps `ollama_vision` method rate >= baseline on the same chapters;
4. artifact is digest-pinned (record the `ollama show` id) and license-compatible;
5. results are committed under `docs/benchmarks/` with environment identity and raw logs.

## Non-Goals

- No replacement of the Ollama runtime (llama.cpp server, transformers, MLX are out of scope).
- No new Python or Node dependencies for model serving.
- No removal of the deterministic chaptering/image fallbacks regardless of model choice.
- No catalog expansion with additional 12B-class quants that lose on the primary path.

## Six-Month Durability

Models in this class churn quarterly; any specific "best local 12B" claim decays in weeks.
The durable artifact is the **gate + protocol + committed evidence**: when the next
candidate appears (Gemma 4 QAT re-upload, Gemma 5, a better community quant), this spec
turns the swap decision into a ~30-minute reproducible measurement instead of a debate.
That value grows as model releases accelerate.

## Re-Evaluation Triggers

- Google re-uploads the QAT GGUF (template/stop-token fixes) or Ollama ships a library
  `gemma4:12b-it-qat` tag.
- Ollama runtime changes Q4_0 vs Q4_K_M kernel performance materially.
- The app's chaptering contract changes (chunk size, chapter-count bounds, schema).

## Acceptance Gates for This Spec

- Raw benchmark logs, summary, and environment identity are committed alongside this spec.
- Commands in `environment.txt` reproduce the suites byte-for-byte in intent (model tags,
  runs, jobs).
- The playground `docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html` and plan
  `docs/plans/hf-gemma4-qat-evaluation-and-model-gate-2026-06-10.md` cite this spec and
  agree with its verdict.
- No code, launcher, or README change ships from this evaluation (NO-GO), and
  `docs/specs/ollama-vision-runtime.md` remains the active runtime contract.
