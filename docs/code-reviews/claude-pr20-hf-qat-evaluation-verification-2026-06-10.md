# PR #20 Verification Audit: HF Gemma 4 QAT Evaluation

Date: 2026-06-10
Reviewer: Claude
Branch reviewed: `docs/hf-gemma4-qat-model-evaluation`
Head reviewed: `a8f8585881549899170cfb1ff0e02a0bebe3199c`
Prior audit: `docs/code-reviews/codex-pr20-hf-qat-evaluation-2026-06-10.md` (re-verified
independently; its commands were re-run, not trusted)

## Review Result

**The evidence holds.** I attempted to falsify the NO-GO on replacing `gemma4:12b` with
`hf.co/google/gemma-4-12B-it-qat-q4_0-gguf:latest` across all seven requested checks and
found no must-fix defects. The verdict rests on multiple independent regressions (schema
pass rate, error count, chapter-count contract compliance, vision method rate), so no
single methodology nit can plausibly flip it.

## Must-Fix Findings

None.

## Optional Cleanup

1. Gate rule 1's latency branch is stricter than it likely intends
   (`docs/specs/hf-gemma4-qat-model-evaluation.md:163-164`). "equal pass rate with >= 20%
   lower avg seconds/call" rejects a candidate that is, e.g., +9 pp on schema pass rate
   *and* 50% faster (fails both branches). Rewording the branch to "pass rate >= baseline
   with >= 20% lower avg seconds/call" keeps the gate conservative while not rejecting a
   strictly-better candidate. Deterministic either way; not blocking. Resolved by follow-up
   commit: the active spec and playground now use the baseline-or-better latency branch.
2. Process note on the prior audit: `codex-pr20-hf-qat-evaluation-2026-06-10.md` verified
   the rewritten playground's DATA block programmatically but did not record a browser
   render of the rewritten explorer (commit `a8f8585` replaced the chart-derivation code).
   I closed that gap below; no defect found, so this is a note for future audits, not a
   finding against the PR.

## What Was Verified (commands re-run at head a8f8585)

1. **Evidence chain.** `backend\.venv\Scripts\python.exe
   docs\benchmarks\gemma4-12b-qat-vs-q4km-2026-06-10\parse_logs.py` rewrote `summary.json`
   byte-identically — SHA256 unchanged:
   `BBBDCC669344A975DD41613963706A4866684FB212FB3E1638ABB85F3DDFB5AA` (matches the prior
   audit's recorded hash). `git status --short --untracked-files=no` clean after
   regeneration; full status shows only pre-existing untracked `.agents/`.
2. **Playground data equality.** Extracted `const DATA` from
   `docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html` by brace-matching; it
   parses as strict JSON and deep-equals
   `docs/benchmarks/gemma4-12b-qat-vs-q4km-2026-06-10/summary.json` exactly (Python `==`
   on the parsed objects). Additionally render-verified the rewritten explorer in a
   browser (static server over `docs/`): derived cells match `summary.json` for
   schema_total (44% (8/18) / 17% (3/18), 3.72 / 2.83, 10.33s / 11.41s, 8 / 10), overall
   (30% (16/54) / 20% (11/54), 4.74 / 4.41, 10.80s / 10.77s, 10 / 14), teded+schema_json
   (2/3 vs 0/3, 14.57s vs 18.73s), and trading_run2+xml (1/6 both, 10.37s vs 9.55s);
   format selector disables on aggregate views; zero console errors or warnings.
3. **Spec tables vs raw logs.** Re-extracted from the raw logs directly (independent of
   `summary.json` and of both audits): TED-Ed schema chapter counts — candidate 6, 7, 6
   with `count_ok` false in all three runs; baseline 5, 6, 5 with two of three passing
   (`qat-teded.txt`, `baseline-teded.txt`), matching
   `docs/specs/hf-gemma4-qat-model-evaluation.md:128-134`. Trading pass counts from the
   harness's own printed summaries — 2/18 vs 1/18 (round 1), 3/18 vs 1/18 (round 2),
   matching spec lines 112-119. Vision methods counted across all image-selection rows —
   baseline 22x `ollama_vision`, candidate 21x + 1 `deterministic`, matching spec lines
   121-126.
4. **Runtime scope.** `git diff main...HEAD --stat -- backend frontend start.sh start.ps1
   start.command` empty; same against `origin/main`. Non-doc changes are limited to the
   `.gitignore` negation for `docs/plans/` tracking (`.gitignore:64-66`), as the PR body
   discloses.
5. **Tests and lint.** From `backend/`: pytest `60 passed in 1.69s`; ruff `All checks
   passed!`.
6. **Standing gate quality** (`docs/specs/hf-gemma4-qat-model-evaluation.md:159-169`).
   Every criterion is measurable (thresholds, non-regression checks, binary pinning and
   evidence requirements; matched sampling and same harness/suites in the preamble). It
   rejects this candidate on three independent rules: rule 1 (16.7% vs required >= 54.4%,
   and not equal-with-20%-faster), rule 2 (overall 20.4% < 29.6%; errors 14 > 10), rule 3
   (21/22 < 22/22). It accepts a genuinely better candidate (e.g. schema pass >= 54.4%
   with no overall/error/vision regression). See Optional Cleanup 1 for one strictness
   wording nit.
7. **Lifecycle and contradictions.** `docs/specs/ollama-vision-runtime.md` remains the
   active runtime contract (`gemma4:12b` default, lines 7/14) and routes default-model
   decisions to the gate (line 22). A repo-wide search for `qat|q4_0|hf.co` over README,
   CONTRIBUTING, launchers, skills, frontend source, and backend app code returned zero
   matches — the candidate exists only in the evaluation artifacts that document its
   rejection. No active doc contradicts the NO-GO.
8. **CI.** All 9 checks green at head `a8f8585` (Backend, Frontend, Launchers on
   ubuntu/macos/windows).

## Methodology Attack (beyond prior audits)

- Re-examined the strongest undisclosed-flaw candidates: sequential baseline-first run
  ordering (disclosed risk is timing-only; the verdict does not depend on the timing
  signal), shared max-tokens truncation in the harness (affects both models identically;
  candidate still errors more in both trading rounds), and the visual-score table (the
  playground correctly labels it transparency-only, not a quality verdict —
  `docs/playgrounds/specs/hf-gemma4-qat-model-evaluation.html:121-123`).
- The four disclosed caveats (unmatched top-k/top-p, single machine, small per-cell n,
  candidate GGUF template roughness) remain the honest boundary of the claim; none is
  undisclosed, and the params-matched re-run is already a plan follow-up.
