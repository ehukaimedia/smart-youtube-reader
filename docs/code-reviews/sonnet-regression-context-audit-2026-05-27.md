# Regression Context Audit — 2026-05-27

**Agent:** Sonnet  
**Task:** 507049da — Regression context audit and cleanup before publication  
**Branch:** codex/digest-preserve-specifics  
**Skill:** `.ehukaiconnect/skills/removing-regression-context/SKILL.md`

---

## Searches Run

```bash
rg -n "TODO|FIXME|XXX|HACK|DEPRECATED|LEGACY|for now|temporary|will remove|remove after|compat|fallback|partly out of date|mostly correct|old version|legacy version|Ollama|Next.js project bootstrapped|Vercel" \
  README.md frontend/README.md backend frontend/src docs tools .github \
  skills/smart-youtube-reader skills/youtube-archive-playground

grep -rn "Ollama|ollama|smart-youtube-digest|Modelfile" \
  backend/app/ docs/ tools/ README.md skills/

# Old playground path after operator-confirmed move of docs/playground/index.html → docs/playgrounds/index.html
grep -rn "docs/playground/" docs/ skills/ README.md \
  | grep -v "docs/playgrounds/"

git ls-files '*__pycache__*' '*.pyc'
git ls-files 'tools/__pycache__/'
```

---

## Findings and Classification

### REFRESH — Stale Ollama-era code reviews (3 files)

All three files below describe the Ollama-based digest implementation. That path has been fully removed (see `docs/plans/mlx-gemma4-archive-runtime-plan.md` and `docs/specs/mlx-gemma4-archive-runtime.md`). The following artifacts they reference no longer exist in the repository:

| Deleted artifact | Referenced by |
|---|---|
| `backend/modelfiles/smart-youtube-digest.Modelfile` | all three reviews |
| `tools/benchmark_digest_model.py` | all three reviews |
| `docs/specs/ollama-ai-digest.md` | backend and frontend reviews |
| `_call_ollama_agent()` / `_ollama_model_available()` | backend review |

Action: Added a `> **Superseded — 2026-05-27.**` blockquote to the top of each file identifying: what path it covered, what replaced it, which artifacts referenced here no longer exist, and that findings are historical only.

- `docs/code-reviews/ollama-digest-benchmark-2026-05-09.md` — benchmark of the Ollama `smart-youtube-digest` model. Modelfile and benchmark tool gone.
- `docs/code-reviews/reviewer-agent-backend-ollama-digest-2026-05-09.md` — backend audit of `_call_ollama_agent()` and `_ollama_model_available()`. All Ollama code gone from `backend/app/digest.py` and `backend/app/intelligence.py`. Required actions are not actionable.
- `docs/code-reviews/reviewer-agent-frontend-slicer-ollama-2026-05-09.md` — frontend audit of "key required" label and benchmark verification. Ollama digest path gone; benchmark tool gone.

---

### LEAVE — Active technical `fallback` patterns (not stale context)

| File | Pattern | Rationale |
|---|---|---|
| `backend/app/intelligence.py` | `_fallback_chapter_title`, `_fallback_gap_summary`, `_fallback: "transcript_gap"`, JSON fallback after XML parse | Active behavior: transcript gaps get conservative chapter fills; XML parse failure falls back to JSON. Current production paths. |
| `frontend/src/lib/clipboard.ts` | `fallbackCopy` | Browser compatibility shim — `navigator.clipboard` not available in all contexts. Active code. |
| `backend/tests/test_digest_prompt.py` | `"Vercel removed tools"` | Test input data for `_append_unique_specific` dedup logic. Not a provider reference. |
| `backend/tests/test_intelligence_archive_parsing.py` | `_fallback` field assertions | Tests for the active transcript-gap chapter field. |
| `docs/specs/archive-generation-efficiency.md` | `fallback nearest-frame`, `fallback chapters` | Current spec describing active image selection and gap fill behavior. |
| `docs/specs/ai-digest-version.md` | "Do not provide a deterministic digest fallback" | Current spec: external-agent digest has no local fallback by design. |
| `docs/specs/group-ai-digest.md` | "temporary group", "Do not generate deterministic fallback images" | Current spec: temporary group selection and no fallback image policy. |
| `docs/specs/dashboard-youtube-thumbnails.md` | "fallback thumbnail surface" | Current UX spec for malformed or missing thumbnail URLs. |
| `docs/specs/mlx-gemma4-archive-runtime.md` | "Do not require Ollama" | Current spec explicitly prohibiting the old pattern. Keeps the constraint legible. |
| `docs/plans/project-zip-download-plan.md` | "temporary ZIP" | Current behavior: ZIP is created outside the project tree and deleted after response. |
| `docs/playgrounds/index.html` | `fallback()` in clipboard copy | Active clipboard fallback in the playground UI. |
| `docs/playgrounds/project-zip-download-flow.md` | "temporary ZIP" | Matches current implementation behavior. |
| `skills/youtube-archive-playground/SKILL.md` | `onerror` img fallback recommendation | Active guidance for playground image error handling. |
| `skills/smart-youtube-reader/SKILL.md` | "Only images available" message | Describes current system state when cookies or node aren't discoverable. |
| `README.md:117` | "app does not run a local digest model or deterministic fallback in the backend" | Accurate: digest is external-agent CLI; archive is MLX-VLM local. Not contradictory. Verified consistent with README lines 15, 19 (MLX-VLM = archive generation only). |

---

### LEAVE — Ollama references in migration artifacts (by design)

| File | Rationale |
|---|---|
| `docs/plans/mlx-gemma4-archive-runtime-plan.md` | Migration plan describing what Ollama artifacts to remove. References are authoritative statements of what was replaced, not active Ollama usage. |
| `docs/specs/mlx-gemma4-archive-runtime.md` | Spec explicitly says "Do not require Ollama". Historical contrast is intentional. |

---

### LEAVE — Historical reviews with no deleted-artifact references

| File | Rationale |
|---|---|
| `docs/code-reviews/reviewer-agent-cache-flow-2026-05-09.md` | References `backend/app/main.py` lines that exist; "backward-compatible raw file access" describes a current recommendation. No deleted artifacts. |
| `docs/code-reviews/reviewer-agent-image-curation-2026-05-09.md` | Historical review of image curation flow. No Ollama or deleted artifact references observed in scan. |

---

### LEAVE — Old playground path references

The operator confirmed that `docs/playground/index.html` was intentionally moved to `docs/playgrounds/index.html` as a playground-lifecycle cleanup. The old `docs/playground/` directory no longer exists.

Search for `docs/playground/` (not `docs/playgrounds/`) in active files finds two hits, both in `docs/code-reviews/reviewer-agent-frontend-slicer-ollama-2026-05-09.md` (lines 8 and 46). That file is already tagged as superseded (Ollama path removed). No active specs, plans, skills, source files, or README reference the old path. The move is clean.

---

### LEAVE — Unscoped / user-owned state (do not touch)

- `skills/impeccable/` deletions and `skills/playground/impeccable/` (untracked): user-owned move, classified in Task 1.
- `.ehukaiconnect/`, `.antigravitycli/`, `.playwright/`: local agent runtime state.
- `frontend/out/`: generated static export output (not versioned source).

---

## Fixes Applied

| File | Change |
|---|---|
| `docs/code-reviews/ollama-digest-benchmark-2026-05-09.md` | Added superseded blockquote at top |
| `docs/code-reviews/reviewer-agent-backend-ollama-digest-2026-05-09.md` | Added superseded blockquote at top |
| `docs/code-reviews/reviewer-agent-frontend-slicer-ollama-2026-05-09.md` | Added superseded blockquote at top |

---

## Verification

```
git ls-files '*__pycache__*' '*.pyc'
```
→ No output. Zero tracked bytecode (removed in commit 4fec45c, Task 1).

```
git ls-files 'tools/__pycache__/'
```
→ No output. tools/__pycache__/ not tracked.

`frontend/README.md` — project-specific content confirmed (no Next.js boilerplate). Contains Quick commands, Tech Stack, port references. This was already replaced before this audit.

Backend tests: 23/23 passed (verified in Task 1; no backend source changes in this task).

---

## Decision

**GO for publication** from regression-context perspective. Active code is clean of dead Ollama paths. The three superseded notices prevent future contributors from searching for deleted artifacts. All other fallback/compat/temporary hits are active behavior, not stale guidance.
