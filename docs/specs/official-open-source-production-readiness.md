# Official Open Source Production Readiness Spec

**Date:** 2026-05-27
**Owner:** Ehukai Media
**Status:** Active

## Goal

Prepare Smart YouTube Reader for production-quality publication as an official Ehukai Media open-source repository.

## Release Standard

The repository is ready to publish when a fresh contributor can clone it, understand what it does, install the documented prerequisites, run verification commands, and see project governance and licensing clearly represented.

## Current Evidence

- Product docs describe a local-first FastAPI and Next.js app.
- Existing specs, plans, reviews, and playgrounds live under `docs/`.
- `README.md` declares MIT licensing, but no root `LICENSE` file is present.
- No `.github/` project automation or community-health files are present.
- `frontend/README.md` still contains the default Next.js starter text.
- Python bytecode under `backend/app/__pycache__/` is tracked and currently dirty.
- Existing architecture playground context includes:
  - `docs/playgrounds/smart-reader-ui-workflow-playground.html`
  - `docs/playgrounds/project-zip-download-flow.md`
  - `docs/playgrounds/group-ai-digest-flow.md`

## Requirements

1. The repository must include explicit Ehukai Media open-source identity:
   - Root `LICENSE` matching the README license claim.
   - Clear README attribution to Ehukai Media.
   - Contribution, security, and project conduct guidance suitable for public GitHub use.

2. Generated and local-only artifacts must not be versioned:
   - Remove tracked Python bytecode.
   - Preserve or improve ignore rules for Python, Node, local agent state, media downloads, generated data, and local environment files.
   - Do not delete user-owned untracked state unless it is intentionally promoted or explicitly excluded.

3. Verification must be repeatable:
   - Backend tests must have a documented command.
   - Frontend lint and production build must have documented commands.
   - CI must run the practical verification suite for pull requests and `main`.

4. Documentation must match the app:
   - Root README should describe the local-first architecture, prerequisites, quick start, verification, and artifact outputs without stale framework boilerplate.
   - `frontend/README.md` should be either removed or replaced with project-specific frontend notes.
   - Any architecture-relevant behavior changes must update specs, plans, or playgrounds in the same change.

5. Public release risk must be reviewed independently:
   - One implementation lane owns production hardening.
   - One documentation/release lane owns public packaging.
   - A separate reviewer records findings under `docs/code-reviews/`.

6. Regression context must be removed before publishing:
   - Active docs must not preserve stale framework boilerplate, obsolete setup paths, or retired behavior as current guidance.
   - Active code, tests, and scripts must not retain dead compatibility paths, TODOs, deprecated names, or unsupported examples that would teach future contributors the wrong pattern.
   - Large or user-owned local state must be classified explicitly instead of silently deleted.
   - The audit must be recorded under `docs/code-reviews/` per the repository instruction for code audits.

## Non-Goals

- No product redesign.
- No hosted SaaS deployment.
- No rewrite of archive generation, digest generation, or video slicing.
- No destructive cleanup of user-local agent state.

## Acceptance Criteria

- `git status --short` shows only intentional release changes.
- No tracked `__pycache__` or `*.pyc` files remain.
- A fresh clone has clear install, run, and verify instructions.
- CI workflow files are present and aligned with documented commands.
- Backend tests, frontend lint, and frontend build are run or any environment blocker is documented.
- Final independent review is recorded in `docs/code-reviews/`.
- Regression-context audit is complete and any blocking stale context is removed or documented as intentionally retained.
- The orchestrator reports the final verification evidence and remaining publish steps to the operator.
