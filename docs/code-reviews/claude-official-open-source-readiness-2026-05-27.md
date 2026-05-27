# Independent Release Review — Official Open-Source Publication

**Date:** 2026-05-27
**Reviewer:** Claude (`d67a6ba9`)
**Scope:** Final pass on the diff produced by Task 1 (Sonnet, `fd537f1d`) and Task 2 (Gemini, `2e0176f4`) against `docs/specs/official-open-source-production-readiness.md` and `docs/plans/official-open-source-production-readiness-plan.md`.
**Source branch:** `codex/digest-preserve-specifics`
**Reference commits / state:** committed `4fec45c` (bytecode removal); staged-but-uncommitted packaging changes (LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, `.github/**`, `README.md`, `frontend/README.md`).

---

## TL;DR

| Lane | Source task | Review task | Verdict |
|---|---|---|---|
| Task 1 — Production hardening | `fd537f1d` (Sonnet) | `31178dd6` | **go** |
| Task 2 — Open-source packaging | `2e0176f4` (Gemini) | `9b90f741` | **no_go** — three required actions below |

Sonnet's hardening is clean and verifiable. Gemini's packaging covers most of the spec but ships with one **CRITICAL** CI defect that defeats the purpose of the gate, **HIGH** packaging artifacts still un-committed at review time, and a **HIGH** documented verification path that fails on a fresh clone. None require redesign; all are mechanical fixes.

> **Publish gate update (2026-05-27, Codex):** A new Task 5 — `removing-regression-context` audit — has been added to the spec/plan. Any final "ready to publish" call must remain **conditional** on Task 5 closing with its own go decision. The two verdicts in this review cover only Task 1 and Task 2 deliverables; they do not by themselves authorize publication.

---

## Verification I Performed

| Check | Command | Result |
|---|---|---|
| Tracked bytecode removed | `git ls-files '*__pycache__*' '*.pyc'` | empty — confirmed |
| `.gitignore` covers pycache | `.gitignore:11-13` | `__pycache__/` and `*.py[cod]` present |
| Backend tests | `cd backend && /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 -m pytest -q` | **23 passed** in 0.50s |
| Frontend lint | `cd frontend && npm run lint` | 0 errors, 5 pre-existing `no-img-element` warnings |
| Frontend build | `cd frontend && npm run build` | success — 5 routes generated via Turbopack |
| Next.js engines | `frontend/node_modules/next/package.json` | declares `engines.node: ">=20.9.0"` |
| Branch commits ahead of `main` | `git log --oneline main..HEAD` | `4fec45c`, `080c2b4`, `e06ccac` |
| Staged but uncommitted | `git status --short` | All Task 2 packaging files have `A`/`M` (staged) — not in a commit |

I did **not** push to a GitHub PR, so the CI workflow has not been exercised end-to-end. The Node-18 finding below is grounded in the `engines` declaration shipped with `next@16.1.3` and the Next.js 16 release line's runtime requirements, not in an observed CI failure.

---

## Required Actions Before Publish (block Task 2 go)

### CRITICAL — CI uses an unsupported Node line

- **File:** `.github/workflows/ci.yml:23`
- **Setting:** `node-version: 18`
- **Evidence:** `frontend/node_modules/next/package.json` ships `engines.node: ">=20.9.0"`. Next 16.x dropped Node 18 from its supported runtimes; using Node 18 violates the stated minimum even if `npm ci` doesn't strictly enforce engines.
- **Impact:** CI is gated on a Node line Next 16 does not support, so any green CI badge would be misleading — and any build/runtime feature Next 16 uses from Node 20 will silently break the lint/build steps the release standard relies on.
- **Required fix:** set `node-version: '20'` (or `'22'`, current LTS). Optionally pin via `frontend/.nvmrc` and use `node-version-file: frontend/.nvmrc` so local dev and CI agree.

### HIGH — Packaging changes are not yet committed

- **Evidence:** `git status --short` shows `A` for every new file (`LICENSE`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/**`) and `M` for `README.md`, `frontend/README.md`. Codex's bus note confirms they're staged, not committed.
- **Impact:** The Task 2 deliverable is index-only. A `git push` of the branch would currently publish only `4fec45c` plus the prior two digest commits, omitting LICENSE / governance docs / CI. Acceptance criterion "fresh clone has clear install, run, and verify instructions" is not met by the published commit graph.
- **Required fix:** commit the staged packaging set as one cohesive Task 2 commit (suggested message: `Add open-source packaging: LICENSE, governance docs, CI, READMEs`) before completing the review-complete step. Verify with `git log --oneline main..HEAD` showing the new commit.

### HIGH — Documented backend verification path fails on a fresh clone

- **File:** `CONTRIBUTING.md:52-54` ("Run tests to verify the setup: `python3 -m pytest`") immediately after `pip install -r requirements.txt`.
- **File:** `README.md` Verification & Testing block runs `python -m pytest` in the venv.
- **Evidence:** `backend/requirements.txt` does **not** include `pytest`, `pytest-asyncio`, or `anyio`. Sonnet's note confirms the issue ("homebrew python3/python3.13 lack pytest"). The CI workflow papers over this with `pip install pytest pytest-asyncio anyio`, which is undocumented elsewhere.
- **Impact:** A fresh contributor following the documented path hits `ModuleNotFoundError: No module named 'pytest'` immediately after install. That violates the release standard ("a fresh contributor can clone it … run verification commands and see project governance and licensing clearly represented").
- **Required fix (pick one):**
  - Add `backend/requirements-dev.txt` containing `pytest`, `pytest-asyncio`, `anyio`; reference it from `CONTRIBUTING.md` and (optionally) `README.md`; have CI install from it instead of inlining the list.
  - Or add the same lines to `requirements.txt` with an `# Development / test dependencies` comment.
  Either way, update `.github/workflows/ci.yml` to install via the canonical file, not the inline list, so CI and docs stay in sync.

---

## Non-blocking Findings (Task 2)

- **MEDIUM — Untracked spec/plan.** `docs/specs/official-open-source-production-readiness.md` and `docs/plans/official-open-source-production-readiness-plan.md` are untracked. Their tracked siblings under `docs/specs/` and `docs/plans/` are versioned. For consistency and so the release record is reproducible, commit them with the packaging commit. This is an orchestration call (Codex's lane) — flagging it for the close-out, not blocking the review.
- **LOW — `SECURITY.md:9` "Supported Versions" table.** The only row is `< 1.0.x — Supported / Current Release`, which reads oddly (there are no prior versions). Replace with `0.x — Supported` or `main` until a versioning scheme is chosen.
- **LOW — README/CONTRIBUTING duplicate setup commands.** Not a blocker, but a future cleanup pass can collapse the duplication via a "see CONTRIBUTING" link in the README.
- **LOW — `start.command:49,55` binds `--host 0.0.0.0`.** Pre-existing, not introduced by Task 1/2, so it is out of scope for this review. Worth noting once for a future hardening pass: the launcher exposes the FastAPI and Next dev servers on every interface, which is surprising default behavior for a "local-first" tool. Spec doesn't require a fix here.
- **LOW — Pre-existing ESLint warnings (5 × `@next/next/no-img-element`).** Unrelated to this work; not introduced by Task 1/2. Track in a follow-up issue if desired.

---

## Findings on Task 1 (Sonnet) — Production Hardening

- **Bytecode commit (`4fec45c`).** Removes the six tracked `.pyc` files cleanly via `git rm`. No accidental tree changes. `.gitignore` already covers `__pycache__/` and `*.py[cod]`, so the regression won't re-occur on the next `pytest` run. ✅
- **Backend tests.** I reproduced Sonnet's evidence: `23 passed in 0.50s` with framework Python 3.13. Pytest discovery handles `backend/app/` despite the absence of `__init__.py`/`conftest.py`. ✅
- **Frontend lint.** Reproduced: 0 errors, 5 pre-existing warnings. None are net-new. ✅
- **Frontend build.** Reproduced: Next 16 Turbopack build succeeded; 5 routes. ✅
- **User-owned dirty paths.** Sonnet correctly left `skills/impeccable/*` deletions and the untracked `skills/playground/impeccable/` tree alone, matching the plan's "user-owned" classification. ✅
- **Scope.** No unrelated code/file changes. ✅

**Task 1 verdict: go.** The hardening pass is complete and the verification evidence holds up on independent re-run. The pytest dependency gap is documentation surface in `CONTRIBUTING.md` (Task 2 lane), not Sonnet's responsibility.

---

## Findings on Task 2 (Gemini) — Open-Source Packaging

What was delivered (and is correct):

- `LICENSE` — MIT, attributed to Ehukai Media, year 2026. Matches README's existing license claim. ✅
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1 with `conduct@ehukaimedia.com` enforcement contact. ✅
- `CONTRIBUTING.md` — covers reporting, feature requests, PR flow, backend and frontend setup, code style. ✅
- `SECURITY.md` — clear private-disclosure path to `security@ehukaimedia.com`, acknowledgement and patch SLAs. ✅
- `.github/ISSUE_TEMPLATE/bug_report.yml`, `feature_request.yml`, `pull_request_template.md` — well-formed YAML/Markdown, scoped to this app. ✅
- `.github/workflows/ci.yml` — backend and frontend jobs, correct working directories, sensible Linux-CI filter for `mlx-vlm`, runs `pytest`, `npm run lint`, `npm run build`. Structure is right; the Node version (and the inline dev-dep install) are the blockers above.
- `README.md` rewrite — adds Ehukai Media ownership, Local-First Architecture section, Apple-Silicon prereq, Verification & Testing section, link block to LICENSE/CONTRIBUTING/SECURITY/CODE_OF_CONDUCT. ✅
- `frontend/README.md` — boilerplate replaced with project-specific frontend notes that defer to the root README. ✅

What blocks the verdict: see the three Required Actions above.

**Task 2 verdict: no_go.** Required actions are mechanical, not structural — a second pass after the fixes should be quick.

---

## Recommended Sequence for Operator / Codex Close-Out

1. Fix `node-version: '20'` in `.github/workflows/ci.yml`.
2. Add `backend/requirements-dev.txt` (or document dev deps in `requirements.txt`); update `CONTRIBUTING.md` and `.github/workflows/ci.yml` to use it.
3. (Optional) Track the spec and plan: `git add docs/specs/official-open-source-production-readiness.md docs/plans/official-open-source-production-readiness-plan.md`.
4. Commit the packaging set as one Task 2 commit.
5. Push, observe CI green on `main` or a PR.
6. Reopen review `9b90f741` once `git status` is clean of release-related state and CI is green; reviewer confirms `go` with the new commit SHA and the green-CI URL as evidence.
7. Complete Task 5 (`removing-regression-context` audit) and its independent review before flipping the repo to public. Task 1 + Task 2 go decisions do not, by themselves, authorize publication.

---

---

## Re-review Addendum — Commit `470bf99`

**Re-review task:** `3f280b13`
**Scope:** Verify the three required actions from the original Task 2 no_go were addressed. Operator-owned worktree changes (notably the `docs/playground/index.html` → `docs/playgrounds/index.html` playground-lifecycle move, handled by Task `507049da`) are explicitly excluded from this scope per Codex's instruction.

### Required-Action Verification

| # | Required action | Evidence in `470bf99` | Status |
|---|---|---|---|
| 1 | CI Node version aligned with `next@16.1.3` engines (`>=20.9.0`) | `frontend/.nvmrc` = `20`; `.github/workflows/ci.yml:24` uses `node-version-file: frontend/.nvmrc` | ✅ resolved |
| 2 | Dev test deps documented and wired into CI | `backend/requirements-dev.txt` lists `pytest>=9.0.0`, `pytest-asyncio>=0.23.0`, `anyio>=4.0.0`; `CONTRIBUTING.md:49` installs `requirements.txt -r requirements-dev.txt`; `README.md:76` mirrors the same; CI installs `requirements-dev.txt` (no inline list) | ✅ resolved |
| 3 | Packaging files committed | `git log --oneline main..HEAD` shows `470bf99` containing LICENSE, CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, README/frontend README updates, `.github/**`, and the spec/plan; `git status --short` no longer lists these as `A`/`M` | ✅ resolved |
| Bonus | `SECURITY.md` Supported Versions row wording | Row now reads `0.x — Supported / Current Release` instead of `< 1.0.x` | ✅ resolved |

### Re-run Evidence

- `cd backend && python3.13 -m pytest -q` → **23 passed in 0.27s**.
- CI workflow inspected statically; no inline dev-dep list remains. (Not pushed to a runner; verdict relies on the same evidence chain as before.)
- `git log --oneline main..HEAD` shows two intentional release commits (`470bf99` + `4fec45c`) plus the two prior digest commits; no stray release state.

### New / Carry-over Findings

- **MEDIUM (new, before public flip) — Documented Node prereq still says "Node.js 18+".**
  - **Files:** `README.md:55` and `CONTRIBUTING.md:35`.
  - **Conflict:** CI is now correctly pinned to Node 20 via `frontend/.nvmrc`, and `next@16.1.3` requires `>=20.9.0`. The README and CONTRIBUTING tell fresh contributors to install Node 18, which contradicts both. `npm ci` may install due to advisory engines, but the verification path the release standard relies on becomes unreliable.
  - **Recommended fix:** change both occurrences to `Node.js 20+` (and optionally reference `frontend/.nvmrc` as the canonical version).
  - **Why not a re-no_go:** this finding was not in the original three required actions, and the runtime gate (CI) is now correct. Calling it out as a publish-conditional rather than blocking this re-review.
- **MEDIUM (carry-over, orchestration) — Task 5 `removing-regression-context` audit.** Final publication remains gated on Task `507049da` closing with its own go. This re-review does not, by itself, authorize publication.

### Re-review Verdict

**Task 2 re-review (`3f280b13`) → go**, conditional on:

1. The Node 18 → 20 doc fix above (cheap, one-line in each file).
2. Task `507049da` regression-context audit closing with go.

The original three blockers are cleanly resolved at `470bf99`. The orchestrator's separation of the operator-owned playground move from this review is honored.

---

## Re-review Addendum 2 — Commits `173eed2` and `e57f60b`

### Node prereq doc fix — `173eed2` (review task `e131a0da`)

Verified the publish-conditional from Addendum 1 is now closed.

- `CONTRIBUTING.md:35` — `Python 3.10+ and Node.js 20+ (see frontend/.nvmrc)`.
- `README.md:55` — `Node.js 20+ (pinned in frontend/.nvmrc)`.
- Repo-wide sweep `grep -rnE "Node\.?js? ?18|node 18|node:18"` over `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `frontend/README.md`, `docs/`, `.github/` (excluding `docs/code-reviews/`) → no hits.

**Verdict: `e131a0da → go`.**

### Regression-context audit — `e57f60b` (review task `c60f04d0`)

Sonnet's audit (`docs/code-reviews/sonnet-regression-context-audit-2026-05-27.md`) is thorough and survives independent verification.

| Claim | Verification | Result |
|---|---|---|
| No Ollama refs in active code | `grep -rn -iE '(ollama\|smart-youtube-digest\|Modelfile\|_call_ollama_agent\|_ollama_model_available)' backend/app/ tools/ frontend/src/` | empty |
| Referenced deleted artifacts truly gone | `ls backend/modelfiles tools/benchmark_digest_model.py docs/specs/ollama-ai-digest.md` | all "No such file" |
| Superseded blockquotes added to three Ollama-era reviews | `git show e57f60b` diff | three correct insertions identifying replaced paths and deleted artifacts |
| No tracked bytecode | `git ls-files '*__pycache__*' '*.pyc'` | empty |
| Old `docs/playground/` path stale-refs outside that move | `grep -rn 'docs/playground/' …` (filtered for non-`docs/playgrounds/`) | empty in active scope |
| Classification of "fallback / temporary / compat" hits as active behavior | Spot-checked `frontend/src/lib/clipboard.ts`, `backend/app/intelligence.py`, `README.md:117` "no deterministic fallback" claim against current architecture | all consistent — these are active behavior, not stale guidance |

Two non-blocking observations:

- The audit's "LEAVE" table includes `docs/playground/index.html` as containing an active `fallback()` clipboard reference, but that file was moved to `docs/playgrounds/index.html` (Codex's note). Sonnet's text mentions both paths in adjacent sections and the move is internally consistent; just a minor naming inconsistency inside the audit's own LEAVE table. Not an action item.
- The two non-Ollama 2026-05-09 reviews (cache-flow, image-curation) are correctly left as-is; spot-checking confirms they reference current `backend/app/main.py` lines and current image-curation behavior, not deleted artifacts.

**Verdict: `c60f04d0 → go`.** The regression-context gate is satisfied.

### Cumulative Publish Status

With `31178dd6 → go`, `3f280b13 → go`, `c60f04d0 → go`, and `e131a0da → go`, all my assigned review gates are clear. No outstanding required actions from this reviewer remain before public flip.

---

## What I Did Not Verify

- I did not push to GitHub Actions, so the CI workflow has not been exercised end-to-end against a real runner. The Node version, dev-dep install, and `working-directory` config are all reviewed statically.
- I did not test the public release as a fresh-clone install (no clean clone in `/tmp`). The "fresh contributor" claim above is grounded in reading the documented steps against `requirements.txt`, not in actually performing them in a clean shell.
- I did not classify the `skills/playground/impeccable/` untracked tree against its Apache 2.0 attribution requirements (its `SKILL.md` references a missing `NOTICE.md`). It is untracked and therefore not part of the release surface, so it's outside this review's blocking scope, but the operator should decide whether that tree is ever published before flipping the repo to public.
