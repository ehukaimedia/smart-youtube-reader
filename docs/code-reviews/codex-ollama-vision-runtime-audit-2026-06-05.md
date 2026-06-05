# Ollama Vision Runtime Audit

Date: 2026-06-05
Reviewer: Codex
Standard: `/Users/ehukaimedia/.codex/skills/ehukai-oss-standard/SKILL.md`
Scope: local update replacing the MLX runtime with regular Ollama Gemma 4, adding vision-assisted frame selection, updating docs/launchers/tests/benchmarking, and removing stale MLX references.

## Resolution Status

Resolved on 2026-06-05:
- `.gitignore` now explicitly unignores this audit artifact, `docs/specs/ollama-vision-runtime.md`, and `docs/playgrounds/architecture/ollama-vision-runtime.html`.
- `/models` now returns only installed Ollama tags in `models`; uninstalled catalog entries remain in `model_details` for metadata.
- `/jobs` now validates the requested model before creating a new background job.
- The New Project UI disables uninstalled catalog entries instead of presenting them as ready-to-run choices.

## Findings

### P1 - Required architecture/spec artifacts are ignored and will not travel with the change

Evidence:
- `.gitignore:52` ignores `docs/playgrounds/`.
- `.gitignore:53` ignores `docs/specs/`.
- `git check-ignore -v docs/specs/ollama-vision-runtime.md docs/playgrounds/architecture/ollama-vision-runtime.html` reports both files ignored by those rules.

Impact:
The update correctly created non-obvious architecture context under the repository-mandated locations, but those files will not be staged or reviewed in a normal PR. That breaks the updated OSS standard's "non-obvious design is captured in a spec / architecture doc, kept current" requirement, because future agents and reviewers can merge the runtime change without the architecture source of truth.

Fix:
Unignore the specific new files or stop ignoring the relevant docs directories. At minimum:
- `!docs/specs/ollama-vision-runtime.md`
- `!docs/playgrounds/architecture/ollama-vision-runtime.html`

Then verify `git status --short --ignored` shows them as normal untracked/staged files rather than `!!` ignored files.

### P1 - The model picker exposes uninstalled Ollama models that the job pipeline cannot run

Evidence:
- `backend/app/model_runtime.py:15-48` defines a static catalog of four Gemma 4 models.
- `backend/app/main.py:394-405` returns every catalog entry in `models`, while only adding `installed` as metadata under `model_details`.
- `frontend/src/app/page.tsx:21-28` stores `data.models` as the selectable list and ignores the `installed` flag.
- `frontend/src/app/page.tsx:85-95` renders all returned models as enabled `<option>` entries.
- `backend/app/model_runtime.py:99-104` raises only when the selected model is missing locally.
- `backend/app/pipeline.py:171-183` discovers that error inside the background archive-generation step, after the job has already been accepted.

Impact:
The launch scripts only ensure `gemma4:12b`, but a cold-clone user can choose `gemma4:e4b`, `gemma4:26b`, or `gemma4:31b` from the UI before those models exist locally. The `/jobs` request returns a created job, the pipeline can spend time downloading/transcribing/extracting frames, and only then fails during archive generation with "ollama pull <model>". That is a user-facing trap and violates the standard's cold-clone honesty bar.

Fix:
Choose one explicit behavior:
- Return only installed models in `models`, while keeping the catalog in `model_details` for informational UI.
- Or disable uninstalled options in the frontend with a clear "pull first" label.
- Or validate/pull the requested model synchronously before accepting `/jobs`, returning a structured 400 or a tracked "pulling model" step instead of failing late in the background job.

## Verification Evidence

Commands run after the update:
- `git diff --check`: passed.
- `rg -n "MLX|mlx|mlx-vlm|mlx_runtime|mlx_chat|Apple Silicon|gemma4:.*-mlx|MLX-runtime" README.md CONTRIBUTING.md start.sh start.command start.ps1 backend frontend/src docs/specs docs/playgrounds -S`: no matches.
- `.venv/bin/ruff check .` from `backend/`: passed.
- `.venv/bin/python -m pytest` from `backend/`: 46 passed.
- `npm run lint` from `frontend/`: passed with `eslint --max-warnings 0`.
- `npm run build` from `frontend/`: passed with Next.js production build.
- `backend/.venv/bin/python backend/benchmark_model.py data/jobs/claude-code-just-leaked-youtubes-algorithm_a95e368e --first-chunk-only --formats xml --runs 1 --timeout 240`: text benchmark quality 7/7; image selection produced eight rows, all with `selection.method: "ollama_vision"`.

Dependency quarantine check:
- No third-party package was introduced or upgraded for the runtime swap. The backend runtime uses Python stdlib `urllib` for Ollama. `backend/requirements.lock` removes the MLX/Hugging Face/transitive stack and does not add a replacement package.

## Residual Risks

- I did not run `start.ps1` in a native Windows environment. The Windows launcher was linted by inspection only, so the Windows quickstart remains unproven until run on Windows PowerShell.
- I did not run a fresh YouTube download-to-archive job end to end in this audit pass. The existing real job benchmark exercises the local Ollama text and vision paths, but not a new network download.
