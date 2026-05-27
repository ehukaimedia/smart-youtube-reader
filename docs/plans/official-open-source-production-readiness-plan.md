# Official Open Source Production Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `.ehukaiconnect/skills/task-agent/SKILL.md` before executing an assigned task. Use `.ehukaiconnect/skills/code-reviewer/SKILL.md` for review tasks. Use `.ehukaiconnect/skills/playground-architect/SKILL.md` if changing architecture docs or playgrounds.

**Goal:** Prepare Smart YouTube Reader for production-quality publication as an official Ehukai Media open-source repository.

**Architecture:** Preserve the current local-first architecture: FastAPI backend, Next.js frontend, local filesystem storage, and external-agent digest tooling. Production readiness is achieved through release hygiene, verification automation, and public-facing docs rather than product rewrites.

**Tech Stack:** FastAPI, pytest, Next.js 16, React 19, ESLint, GitHub Actions, local macOS launch scripts, yt-dlp, FFmpeg, MLX-VLM.

---

## Context For Workers

- Follow `AGENTS.md`: specs in `docs/specs/`, plans in `docs/plans/`, reviews in `docs/code-reviews/`.
- Treat the existing dirty worktree as user-owned. Do not revert unrelated changes.
- Existing open-source blockers observed on 2026-05-27:
  - `README.md` says MIT but no root `LICENSE` exists.
  - `.github/` is absent.
  - `frontend/README.md` is default Next.js boilerplate.
  - Tracked Python bytecode exists under `backend/app/__pycache__/`.
  - `skills/impeccable/` is deleted and `skills/playground/impeccable/` is untracked; classify this move before touching it.
- Use the active architecture/playground context before changing app behavior:
  - `docs/playgrounds/smart-reader-ui-workflow-playground.html`
  - `docs/playgrounds/project-zip-download-flow.md`
  - `docs/playgrounds/group-ai-digest-flow.md`

## Task 1: Production Hardening

**Assignee:** Sonnet

**Files likely touched:**
- Modify: `.gitignore`
- Delete from tracking: `backend/app/__pycache__/*.pyc`
- Modify only if verification proves necessary: `backend/app/*.py`, `backend/tests/*.py`, `frontend/src/**`, `frontend/package.json`, `frontend/package-lock.json`
- Update if behavior changes: `docs/playgrounds/*`, `docs/specs/*`, `docs/plans/*`

Steps:

- [ ] Read `.ehukaiconnect/skills/task-agent/SKILL.md`, this plan, and `docs/specs/official-open-source-production-readiness.md`.
- [ ] Inspect current status with `git status --short` and classify each dirty path as release cleanup, user-owned local state, or implementation work.
- [ ] Confirm tracked bytecode with `git ls-files '*__pycache__*' '*.pyc'`.
- [ ] Remove tracked bytecode from the repository using `git rm` for tracked files only. Do not remove untracked local cache directories unless needed for verification.
- [ ] Run backend tests:

```bash
cd backend
python3 -m pytest
```

Expected result: tests pass, or the task records exact missing dependency / runtime blocker and the smallest fix.

- [ ] Run frontend lint:

```bash
cd frontend
npm run lint
```

Expected result: lint passes, or failures are fixed with focused changes.

- [ ] Run frontend production build:

```bash
cd frontend
npm run build
```

Expected result: build passes, or failures are fixed with focused changes.

- [ ] If implementation changes alter routes, job state, archive shape, digest behavior, or UI workflow, update the matching spec/plan/playground in the same task.
- [ ] Finish with a task update summarizing changed files and verification evidence.

## Task 2: Official Open Source Packaging

**Assignee:** Gemini

**Files likely touched:**
- Create: `LICENSE`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `.github/workflows/ci.yml`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/pull_request_template.md`
- Modify: `README.md`
- Modify or replace: `frontend/README.md`

Steps:

- [ ] Read `.ehukaiconnect/skills/task-agent/SKILL.md`, this plan, and `docs/specs/official-open-source-production-readiness.md`.
- [ ] Add a root MIT `LICENSE` with Ehukai Media attribution.
- [ ] Update `README.md` so it includes:
  - Ehukai Media ownership / official open-source status.
  - Local-first architecture summary.
  - Prerequisites.
  - Quick start.
  - Verification commands for backend and frontend.
  - Notes on MLX-VLM and local model expectations.
  - Link to contribution, security, and code of conduct docs.
- [ ] Replace `frontend/README.md` with project-specific frontend setup notes or remove it if the root README fully covers frontend usage.
- [ ] Add contribution, security, and code-of-conduct documents suitable for a public repo.
- [ ] Add GitHub issue templates and pull request template.
- [ ] Add CI workflow that runs backend tests and frontend lint/build on pull requests and `main`.
- [ ] Do not claim CI is green until local commands or GitHub Actions evidence exists.
- [ ] Finish with a task update summarizing changed files and any verification run.

## Task 3: Independent Release Review

**Assignee:** Claude

**Files likely touched:**
- Create: `docs/code-reviews/claude-official-open-source-readiness-2026-05-27.md`

Steps:

- [ ] Read `.ehukaiconnect/skills/task-agent/SKILL.md`, `.ehukaiconnect/skills/code-reviewer/SKILL.md`, this plan, and the spec.
- [ ] First pass before implementation: identify release risks that Task 1 and Task 2 must address.
- [ ] Final pass after implementation: review the diff for production-readiness, open-source hygiene, CI correctness, stale docs, and playground drift.
- [ ] Record the review in `docs/code-reviews/claude-official-open-source-readiness-2026-05-27.md`.
- [ ] If the decision is not ready to publish, list required actions clearly and mark the review no-go through the task manager.
- [ ] If ready, record a go decision with the exact verification evidence reviewed.

## Task 4: Orchestration Close-Out

**Assignee:** Codex

Steps:

- [ ] Create durable tasks for the three worker lanes.
- [ ] Enable autonomous dispatch.
- [ ] Monitor stalled tasks using `ehukaiconnect task list`, `ehukaiconnect dispatch status`, and peer terminal watch only when needed.
- [ ] Request formal review tasks after implementation lanes finish.
- [ ] Add and complete a regression-context audit gate before publication.
- [ ] Close only when review is recorded, verification evidence is explicit, and operator-facing publish steps are clear.

## Task 5: Regression Context Audit And Cleanup

**Assignee:** Sonnet

**Files likely touched:**
- Create: `docs/code-reviews/sonnet-regression-context-audit-2026-05-27.md`
- Modify if stale context is found: active docs, scripts, tests, or source files that contain obsolete guidance
- Do not modify unless explicitly classified: `.ehukaiconnect/`, `.antigravitycli/`, `.playwright/`, user-owned skill moves under `skills/impeccable/` and `skills/playground/impeccable/`

Steps:

- [ ] Read `.ehukaiconnect/skills/task-agent/SKILL.md`, `.ehukaiconnect/skills/removing-regression-context/SKILL.md`, this plan, and the spec.
- [ ] Scan active code, docs, tests, scripts, GitHub templates, and READMEs for stale context using patterns from the skill:

```bash
rg -n "TODO|FIXME|XXX|HACK|DEPRECATED|LEGACY|for now|temporary|will remove|remove after|compat|fallback|partly out of date|mostly correct|old version|legacy version|Ollama|Next.js project bootstrapped|Vercel" README.md frontend/README.md backend frontend docs tools .github skills
```

- [ ] Classify each hit as remove, migrate, leave with current rationale, or unrelated.
- [ ] Remove or refresh blocking stale context in active project files. Keep changes focused and do not sweep user-owned local state.
- [ ] Verify no tracked bytecode remains:

```bash
git ls-files '*__pycache__*' '*.pyc'
```

Expected result: no output.

- [ ] Write the audit to `docs/code-reviews/sonnet-regression-context-audit-2026-05-27.md`, including searches run, findings, fixes applied, and any intentionally retained context.
- [ ] Update the task with changed files and verification evidence.
