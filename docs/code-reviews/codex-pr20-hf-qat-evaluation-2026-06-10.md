# PR #20 Audit: HF Gemma 4 QAT Evaluation

Date: 2026-06-10
Reviewer: Codex
Branch reviewed: `docs/hf-gemma4-qat-model-evaluation`
Initial head reviewed: `dc82924cb102db71b7f0c44f9b5a841996d2fe84`

## Review Result

Evidence holds for the NO-GO on replacing `gemma4:12b` with
`hf.co/google/gemma-4-12B-it-qat-q4_0-gguf:latest`. I did not find an undisclosed
methodology flaw that could plausibly flip the benchmark verdict.

## Must-Fix Findings

None remaining.

## Resolved During Implementation

1. Playground DATA now matches `summary.json` exactly.

   The initial review found that the playground's inline DATA block was a reduced chart
   projection while claiming to be copied verbatim from `summary.json`. The implementation
   now embeds the full `summary.json` object at
   `docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html:178-550` and derives chart
   cells at render time from that exact object
   (`docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html:552-648`). A programmatic
   extraction of `const DATA` now deep-equals
   `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json`.

## Optional Cleanup

1. Mention the `.gitignore` exception if summarizing scope as "docs and evidence only".

   The PR does include a non-runtime metadata change to unignore the plan artifact
   (`.gitignore:64-66`). This does not contradict "zero runtime code changes", and it
   appears necessary for the plan to be tracked, but PR/body summaries should avoid implying
   every changed path is under `docs/`.

## Evidence Chain Verification

- Ran
  `backend\.venv\Scripts\python.exe docs\benchmarks\gemma4-12b-qat-vs-q4km-2026-06-10\parse_logs.py`.
  It rewrote `summary.json` byte-identically: SHA256 stayed
  `BBBDCC669344A975DD41613963706A4866684FB212FB3E1638ABB85F3DDFB5AA`.
- `git diff --stat -- docs\benchmarks\gemma4-12b-qat-vs-q4km-2026-06-10\summary.json`
  was empty after regeneration.
- `git status --short --untracked-files=no` was clean before writing this audit. Full
  status had only pre-existing untracked `.agents/`.

## Numeric Spot Checks

- Overall text table: spec reports baseline 29.6% (16/54), avg quality 4.74, 10.80 s/call,
  10 errors, and candidate 20.4% (11/54), avg quality 4.41, 10.77 s/call, 14 errors
  (`docs/specs/hf-gemma4-qat-model-evaluation.md:91-98`). These match `summary.json`
  baseline overall text (`docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:176-184`)
  and candidate overall text
  (`docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:361-368`).
- Production schema path: spec reports 44.4% (8/18) vs 16.7% (3/18), avg quality
  3.72 vs 2.83, 10.33 s/call vs 11.41 s/call, and 8 vs 10 malformed-output errors
  (`docs/specs/hf-gemma4-qat-model-evaluation.md:100-110`). These are the sums of the
  per-suite `schema_json` rows in `summary.json`:
  baseline sample/TED/trading/trading2 at
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:12-19`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:50-57`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:95-102`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:140-147`; candidate
  sample/TED/trading/trading2 at
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:196-203`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:234-241`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:280-287`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:325-332`.
- TED-Ed over-segmentation: spec says candidate schema runs produced 6, 7, 6 chapters and
  all failed `count_ok`; baseline produced 5, 6, 5 and passed two of three
  (`docs/specs/hf-gemma4-qat-model-evaluation.md:128-134`). Raw logs confirm candidate
  chapter counts at
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/qat-teded.txt:19-24`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/qat-teded.txt:117-122`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/qat-teded.txt:216-221`, and baseline
  counts at
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/baseline-teded.txt:18-23`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/baseline-teded.txt:114-119`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/baseline-teded.txt:211-216`.
- Trading pass counts: spec reports round 1 as 2/18 vs 1/18 and round 2 as 3/18 vs 1/18
  (`docs/specs/hf-gemma4-qat-model-evaluation.md:112-119`). Raw logs confirm round 1 at
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/baseline-trading.txt:519-526` and
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/qat-trading.txt:511-518`; round 2 at
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/baseline-trading-run2.txt:520-527`
  and `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/qat-trading-run2.txt:512-519`.
- Vision method count: spec reports 22/22 baseline `ollama_vision` selections vs 21/22
  candidate plus one deterministic fallback
  (`docs/specs/hf-gemma4-qat-model-evaluation.md:121-126`). `summary.json` confirms
  candidate TED-Ed had one deterministic and five `ollama_vision` selections
  (`docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:262-268`) while both
  candidate trading rounds had 8 `ollama_vision` selections
  (`docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:308-313`,
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json:353-358`). The raw
  fallback is visible at
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/qat-teded.txt:349` and
  `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/qat-teded.txt:416-417`.

## Scope, Tests, and Lint

- `git diff main --stat -- backend frontend start.sh start.ps1 start.command` returned no
  output. I also checked the same path set against `origin/main`; it was empty.
- Backend tests passed from `backend/`:
  `..\backend\.venv\Scripts\python.exe -m pytest` -> `60 passed in 1.63s`.
- Ruff passed from `backend/`:
  `..\backend\.venv\Scripts\python.exe -m ruff check .` -> `All checks passed!`.

## Claims and Lifecycle Audit

- File-line anchors in the spec, plan, and playground resolve to real code locations:
  `backend/app/model_runtime.py:13`, `backend/app/model_runtime.py:15-48`,
  `backend/app/model_runtime.py:149-154`, `backend/app/model_runtime.py:168`,
  `backend/app/intelligence.py:1264`, `backend/app/main.py:436-450`,
  `frontend/src/app/page.tsx:71`, `backend/benchmark_model.py:203-213`, `start.sh:37`,
  `start.sh:42`, `start.ps1:191`, `start.ps1:196-197`, and `CONTRIBUTING.md:33`.
- The benchmark environment artifact backs the model identity, host, GPU, Ollama version,
  protocol, raw-log reproduction commands, and source/license/publish-date claims
  (`docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/environment.txt:4-57`).
- The new playground is in the active spec bucket
  `docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html`, has an INTENT comment at
  `docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html:56`, and has a visible
  Spec Seed at `docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html:143-161`.
- `docs/specs/ollama-vision-runtime.md` remains the active runtime contract: it still says
  the default is `gemma4:12b` and now points future default-model decisions at this gate
  (`docs/specs/ollama-vision-runtime.md:7`, `docs/specs/ollama-vision-runtime.md:14`,
  `docs/specs/ollama-vision-runtime.md:22`).
- I searched active docs for the candidate and default-model language. I found no active
  document that says to adopt the QAT candidate; references either document the evaluation,
  the NO-GO, or the dormant future-only migration recipe.

## Methodology Attack

- Warm-up, GPU residency, machine identity, and suite definitions are documented in
  `environment.txt` (`docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/environment.txt:28-45`).
  GPU residency is also backed by `baseline-ollama-ps.txt:1-2` and `qat-ollama-ps.txt:1-2`.
- Commands are documented as identical except `--model`
  (`docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/environment.txt:47-52`), and raw log
  headers show matching transcript/project inputs for each baseline/candidate suite.
- The strongest remaining methodology weakness beyond the disclosed caveats is run ordering:
  suites ran sequentially baseline-first, candidate-second
  (`docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/environment.txt:42-45`) rather than
  interleaved/randomized. That can affect timing via thermal/background variance, but it
  does not plausibly flip the NO-GO because the verdict is not based on a fragile speed win:
  candidate schema pass rate is much lower, malformed-output errors are higher, TED-Ed
  schema chapter counts systematically exceed the contract, and the candidate had one
  vision fallback.
- The disclosed caveats are material and correctly stated: unmatched top-k/top-p sampling,
  one machine, small per-cell sample size, and candidate template roughness
  (`docs/specs/hf-gemma4-qat-model-evaluation.md:136-149`). I did not find an additional
  undisclosed flaw that should block the verdict.

## Standing Gate Quality

The standing gate is specific and measurable: same machine class, same harness, same suites,
matched sampling, schema pass-rate threshold, overall pass/error non-regression, vision method
non-regression, digest pinning, license compatibility, and committed raw evidence
(`docs/specs/hf-gemma4-qat-model-evaluation.md:159-169`).

It would reject this candidate on multiple independent gates: schema pass rate is lower
instead of baseline + 10 pp or baseline-matching with a large latency win, schema latency is
slower rather than 20% faster, overall pass rate regresses, error count regresses, and vision
method rate regresses. It would accept a genuinely better default candidate that clears the
primary schema path threshold or at least matches schema quality with a large latency win
while avoiding overall, error, and vision regressions.
