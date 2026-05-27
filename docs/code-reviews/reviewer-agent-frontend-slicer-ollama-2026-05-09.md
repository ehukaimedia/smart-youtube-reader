# Frontend Slicer and Ollama Digest Audit

> **Superseded — 2026-05-27.** This review covers frontend issues tied to the Ollama-based digest path. That path has been replaced: archive generation now uses MLX-VLM (see `docs/specs/mlx-gemma4-archive-runtime.md`) and digest creation is handled by an external-agent CLI with no local Ollama model (see README §AI Digest Workflow). The following artifacts referenced here no longer exist: `tools/benchmark_digest_model.py`, `docs/specs/ollama-ai-digest.md`. The "key required" label and benchmark findings below applied to the Ollama path and are not actionable against the current codebase.

Date: 2026-05-09
Agent: reviewer-agent
Role: Reviewer B
Scope: `frontend/src/app/slicer/[jobId]/page.tsx`, digest specs/plans, `docs/playground/index.html`, and `README.md`.

## Findings

### P2 - Unavailable Ollama digest still appears as "key required" in the browser

The new Ollama spec says unavailable local models should show as unavailable instead of requiring an API key (`docs/specs/ollama-ai-digest.md:18`). The current reader UI still renders every unavailable digest model with the suffix `(key required)` (`frontend/src/app/reader/[jobId]/page.tsx:285-288`). For the new `Local Gemma AI Digest` path, that sends users toward the wrong fix: they need Ollama running and the `smart-youtube-digest` model built, not an API key.

This is user-visible and contradicts the updated local-only docs. It also weakens the browser behavior for the primary digest model because the dropdown no longer describes the actual availability failure.

Recommended direction: make the unavailable label provider-aware, for example `Ollama model unavailable` / `build local model`, while keeping any future hosted-provider key wording separate.

### P2 - Saving a replacement slice can report success even when no replacement image was saved

`handleSaveToProject` only checks `res.ok`, discards the response body, shows `Slice saved to project`, and returns to the reader (`frontend/src/app/slicer/[jobId]/page.tsx:232-244`). The backend response includes `images_added`, and `save_slice_to_project` can return `images_added: 0` when selected preview files are missing or no image paths are copied (`backend/app/slicing.py:180-196`, `backend/app/slicing.py:241-246`).

In the human-managed replacement flow, this can look like a successful replacement while the reader reopens without the new visual attached. That is exactly the kind of unclear image replacement behavior the UX should avoid.

Recommended direction: treat `images_added === 0` as a failed save with a clear toast, and include backend `detail` text for non-OK responses before navigating back to the reader.

### P2 - Slicer finalize/save errors still hide backend details

The preview/export path now surfaces backend error details (`frontend/src/app/slicer/[jobId]/page.tsx:115-132`), but the other two user-facing slicer actions still collapse failures to generic messages. `handleFinalize` throws `Finalize failed` and then always toasts `Failed to create zip` (`frontend/src/app/slicer/[jobId]/page.tsx:166-172`). `handleSaveToProject` throws `Save failed` and then always toasts `Failed to save slice` (`frontend/src/app/slicer/[jobId]/page.tsx:240-248`).

For replacement workflows, common failures such as expired preview metadata, missing files, or an invalid project are actionable only if the UI preserves the backend detail. The current partial error handling means users get clear messages before review, then vague messages at the point where they actually try to save the curated image.

Recommended direction: parse `errorData?.detail` for finalize/save the same way preview/export now does, and toast the thrown message.

### P3 - The benchmark quality gate overstates image preservation coverage

The Ollama spec lists `Preserved image count equals images from kept source chapters` as a benchmark quality gate (`docs/specs/ollama-ai-digest.md:31`), and the README tells users to benchmark before review-sensitive work (`README.md:98-104`). The benchmark script does not actually verify the backend's preserved image output; it computes `expected_images` from selected `source_indices` and then sets `preserved_images = expected_images` unconditionally (`tools/benchmark_digest_model.py:234-235`).

That means the benchmark can pass even if the backend normalization later drops, duplicates, or rewrites image references. Given the new product stance that digest generation must preserve images and leave removal/replacement to humans, the docs currently promise a stronger quality gate than exists.

Recommended direction: either document this as a source-index gate only, or extend the benchmark to run the same backend normalization/preservation logic used by digest creation and compare actual resulting `images`.

### P3 - The architecture playground omits the runtime model availability path

The playground now shows the local digest model and benchmark nodes (`docs/playground/index.html:289-292`) and the digest-to-Ollama call (`docs/playground/index.html:338-340`), but it still does not represent the reader's `/digest-models` fetch or the backend's Ollama `/api/tags` availability check. Those are the pieces that drive whether the browser presents `Local Gemma AI Digest` as usable.

This omission matters because the updated architecture is meant to prevent drift. The stale browser label above is exactly the kind of issue that would be easier to catch if the playground represented the digest model discovery flow, not just digest creation.

Recommended direction: add a reader-to-API `GET /digest-models` connection and an API/digest-to-Ollama availability check connection, or otherwise annotate the digest model node as supplying browser availability state.

## Verification

- Ran `npm run lint -- 'src/app/slicer/[jobId]/page.tsx'` from `frontend/`.
- Result: 0 errors, 2 existing warnings for `<img>` usage at `frontend/src/app/slicer/[jobId]/page.tsx:389` and `frontend/src/app/slicer/[jobId]/page.tsx:474`.
- I did not run a browser reproduction or modify implementation files.
