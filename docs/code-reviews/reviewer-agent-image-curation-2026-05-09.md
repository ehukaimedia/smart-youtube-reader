# Image Curation Reopen/Error Audit

Date: 2026-05-09
Agent: reviewer-agent
Scope: frontend reader archive image loading/removal and backend archive image endpoint.

## Summary

The reported behavior is best explained by stale `archive.json` reads. The backend removal endpoint writes the updated chapter image list to `archive.json`; if the reader later reloads an older cached copy from the static `/data/jobs/.../archive.json` mount, the removed image appears again in the UI. A second remove then reaches the backend with an image that is already absent from the persisted chapter and the backend returns the "Image is not attached to this chapter" error.

The current dirty worktree already contains the right shape of fix for the reader path:

- `frontend/src/app/reader/[jobId]/page.tsx:410` now loads archive data from `GET /jobs/{job_id}/archive` with `{ cache: 'no-store' }`.
- `backend/app/main.py:215` adds `GET /jobs/{job_id}/archive`, and `backend/app/main.py:230` returns `JSONResponse` with `Cache-Control: no-store, max-age=0`, `Pragma: no-cache`, and `Expires: 0`.
- `backend/app/main.py:264` makes repeated image removal idempotent by returning the current `images` list with `removed: false` instead of raising the prior 404 detail.

## Findings

### P1 - Stale static archive reads caused the removed image to reappear

Evidence:

- The project data directory is exposed through `StaticFiles` at `backend/app/main.py:41`.
- The reader image URLs still correctly use static file serving for image bytes at `frontend/src/app/reader/[jobId]/page.tsx:473`, but archive metadata should not be loaded through that cacheable static route.
- The current reader now avoids the static `archive.json` route and uses `fetch(.../jobs/${jobId}/archive, { cache: 'no-store' })` at `frontend/src/app/reader/[jobId]/page.tsx:410`.
- The current backend no-cache archive reader is at `backend/app/main.py:215-237`.

Failure chain:

1. User removes an image.
2. `removeArchiveImage` posts `chapter_index` and `image_path` to `POST /jobs/{job_id}/archive/image` at `frontend/src/app/reader/[jobId]/page.tsx:360-370`.
3. Backend updates `archive.json` at `backend/app/main.py:267-271`.
4. Reopening the project from a cached static `archive.json` can rehydrate old `images`.
5. A later remove posts the stale image path again, but the persisted chapter no longer contains it.

Current status: addressed in the dirty worktree for the reader's archive load path by `frontend/src/app/reader/[jobId]/page.tsx:410` and `backend/app/main.py:215-237`.

### P2 - Learning prompt still advertises the cacheable static archive URL

`copyLearningPrompt` still builds `Archive JSON` from `/data/jobs/${job.data_folder_name}/archive.json` at `frontend/src/app/reader/[jobId]/page.tsx:64-66`. That bypasses the new no-store archive endpoint and can give external readers/agents stale archive metadata after image curation, which conflicts with the spec expectation that learning prompts use the curated image set.

Recommended direction: point the prompt's archive URL at `GET /jobs/{job_id}/archive` or provide another no-store archive metadata endpoint intended for prompt consumption, while keeping static `/data/jobs/.../<image>` URLs for frame bytes.

### P2 - Curated slice removal clears local UI even if backend deletion fails

`deleteSlice` sends `DELETE /jobs/${jobId}/slices/${sliceId}` at `frontend/src/app/reader/[jobId]/page.tsx:347`, does not check `res.ok`, and immediately clears images from local state at `frontend/src/app/reader/[jobId]/page.tsx:348-351`. If the backend returns 404/500 or the request fails, the UI will show the visuals as removed until reload, then they will reappear from persisted `archive.json`.

This is a separate "removed images reappear after reopening" path from the per-image archive removal bug, but it affects the same reader curation surface.

Recommended direction: check the delete response before mutating local state, show the backend error through the toast provider, and optionally refresh the chapter from the no-store archive endpoint after successful deletion.

### P3 - Per-image removal is tied to chapter index only

`ArchiveImageUpdateRequest` contains only `chapter_index` and `image_path` at `backend/app/schemas.py:53-55`, and the backend selects the chapter by array position at `backend/app/main.py:258-263`. This works while the reader is showing the exact current archive array, but stale UI state or future chapter reordering/filtering can target the wrong chapter or produce a false "not attached" result.

Recommended direction: include a stable chapter identity or enough chapter metadata to validate the target, such as timestamp/concept plus index, and have the backend confirm the image is being removed from the intended chapter.

## Notes

I did not edit implementation files. The only file written for this task is this audit.

I did not run the app or browser reproduction. This review is based on code inspection and the current dirty worktree diff.
