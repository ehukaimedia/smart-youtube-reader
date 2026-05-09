# Archive Image Deletion Persistence Flow Review

Date: 2026-05-09
Reviewer: reviewer-agent
Scope: Archive image deletion persistence flow, including cache, static route, state update, index mismatch, and race behavior.

## Findings

### P1 - Curated slice removal lies locally and restores images on reopen

References:
- `frontend/src/app/reader/[jobId]/page.tsx:343`
- `frontend/src/app/reader/[jobId]/page.tsx:347`
- `frontend/src/app/reader/[jobId]/page.tsx:349`
- `backend/app/main.py:381`
- `backend/app/main.py:382`
- `backend/app/main.py:384`

`deleteSlice` removes a saved curated slice, then immediately clears `images` in local React state. The backend does not persist that empty image set. It restores `_original_images` back into the chapter and writes those restored images to `archive.json`.

That creates the exact user-visible persistence failure for the "curated - remove" path: images disappear immediately, but reopening the project loads `archive.json` and shows the restored images again. The confirmation copy says "The AI-selected images will be cleared", and the frontend state update clears them, but the backend behavior restores them.

Recommended fix:
- Align one persisted semantic across frontend and backend.
- If "remove curated visuals" should leave the chapter empty, set `chapter["images"] = []` and clear slice metadata.
- If it should restore AI originals, update the confirmation text and local state to use the backend-returned restored images instead of clearing locally.
- Return the updated chapter/images from the delete endpoint and only update local state after checking `res.ok`.

### P1 - Image deletion still relies on render index, so stale UI can target the wrong chapter

References:
- `frontend/src/app/reader/[jobId]/page.tsx:435`
- `frontend/src/app/reader/[jobId]/page.tsx:479`
- `frontend/src/app/reader/[jobId]/page.tsx:487`
- `backend/app/schemas.py:53`
- `backend/app/main.py:258`
- `backend/app/main.py:262`

The remove/replace flow identifies the chapter by array position (`idx` -> `chapter_index`). The backend then trusts that index against the current on-disk `archive.json`. If the client has stale archive data, if another tab edited the archive, or if any process rewrites chapter order/content between load and click, the request can remove from the wrong chapter or report/no-op because the image is not attached to the chapter at that index.

This is also why a stale reopen can produce the old "Image is not attached to this chapter" symptom: the image path exists in the UI, but not at the submitted chapter index in the server's current archive.

Recommended fix:
- Use a stable chapter identifier in `archive.json` and in curation requests.
- At minimum, include a server-side guard that searches for the image path across chapters when the supplied chapter index does not contain it, and returns a conflict if multiple matches exist.
- Consider returning the full updated archive from mutation endpoints so the client can resync after each edit.

### P2 - No-op image removals are treated as successful, masking stale-cache failures

References:
- `backend/app/main.py:263`
- `backend/app/main.py:264`
- `backend/app/main.py:265`
- `frontend/src/app/reader/[jobId]/page.tsx:377`
- `frontend/src/app/reader/[jobId]/page.tsx:378`
- `frontend/src/app/reader/[jobId]/page.tsx:379`

The current delete endpoint returns `200` with `{ "removed": false }` when the requested image is not attached. The frontend ignores `removed` and updates the rendered chapter images from `data.images`.

That prevents the visible error, but it can also hide a stale or mismatched UI state: the user sees an image, clicks remove, the server changes nothing, and the client may still remove or alter local display based on the wrong chapter's `images`. Reopening can then show the image again because no persisted deletion occurred.

Recommended fix:
- Treat `removed: false` as a stale-state conflict in the frontend and reload the archive immediately.
- Prefer `409 Conflict` for "request does not match current archive state" unless idempotency is intentionally required.
- If idempotency is required, include enough response data for the client to reconcile, such as the current full archive revision.

### P2 - Static archive URL remains in learning prompts and can bypass the no-store archive endpoint

References:
- `backend/app/main.py:41`
- `backend/app/main.py:215`
- `backend/app/main.py:230`
- `backend/app/main.py:233`
- `frontend/src/app/reader/[jobId]/page.tsx:65`
- `frontend/src/app/reader/[jobId]/page.tsx:71`
- `frontend/src/app/reader/[jobId]/page.tsx:410`

The reader preview now fetches `/jobs/{job_id}/archive` with `cache: "no-store"`, and the backend returns no-store headers. That is the correct direction for the reopened-project cache bug.

However, the learning prompt still points consumers at the static `/data/jobs/{folder}/archive.json` route. Static files are mounted separately and do not use the explicit no-store headers from `/jobs/{job_id}/archive`. A user or agent following the copied prompt can still hit the stale/static path rather than the canonical no-store route, which violates the spec's requirement that learning prompts use the curated image set.

Recommended fix:
- Change copied archive URLs to `/jobs/{job_id}/archive`.
- Keep static `/data/jobs/...` for image assets and backward-compatible raw file access, but avoid it as the canonical mutable archive API.

### P2 - Concurrent archive writes can lose deletions

References:
- `backend/app/main.py:255`
- `backend/app/main.py:267`
- `backend/app/main.py:270`
- `backend/app/slicing.py:211`
- `backend/app/slicing.py:235`
- `backend/app/slicing.py:238`

Archive mutations use unsynchronized read-modify-write cycles over the same `archive.json`. Two image removals, or a removal racing with a slicer save, can each read the same old file and then write divergent versions. The later writer wins and can resurrect an image removed by the earlier writer.

The frontend disables image buttons while one action is active, but that only protects one rendered component in one browser tab. It does not protect double-click timing before state is committed, another tab, a copied project link on another machine, or slicer/save actions running in parallel.

Recommended fix:
- Serialize per-job archive mutations with a lock in the backend.
- Add an archive revision/mtime precondition to mutation requests and return `409 Conflict` on stale edits.
- Write JSON atomically via a temp file and rename to avoid partially written archive files.

## Notes

The current code already addresses the primary static route reload issue in the main reader preview by adding `GET /jobs/{job_id}/archive` with no-store headers and using that endpoint from `ArchivePreview`. The remaining risks are mostly stale-state reconciliation, semantic mismatch between local state and persisted archive content, and concurrent writers.
