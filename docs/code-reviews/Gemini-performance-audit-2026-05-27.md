# Performance Audit: Smart YouTube Reader

**Auditor:** Gemini
**Date:** 2026-05-27
**Scope:** Performance audit of the Next.js frontend, FastAPI backend, video timeline slicing, startup/Tailscale sharing, and local MLX VLM model execution.

---

## Executive Summary
This audit outlines key architectural bottlenecks and performance inefficiencies in the **Smart YouTube Reader** workspace. The main findings focus on synchronous blocking calls in the FastAPI event loop, video slicing routes that run FFmpeg inline, MLX inference concurrency limits, and a now-fixed cross-origin sharing toggle regression.

---

## Critical Severity Findings

### 1. Synchronous Subprocess Blocking in API Event Loop (Tailscale/Interface Checks)

* **Location:**
  - `_scan_ifconfig_for_tailnet_ip()` at [backend/app/main.py:50-71](file:///Volumes/Extreme%20SSD/AI-Applications/smart-youtube-reader/backend/app/main.py#L50-L71)
  - `_tailscale_status()` at [backend/app/main.py:88-132](file:///Volumes/Extreme%20SSD/AI-Applications/smart-youtube-reader/backend/app/main.py#L88-L132)
* **Impact:** Freezes the single-threaded FastAPI backend during startup checks and status requests. If Tailscale is offline or slow, the entire server freezes for up to 4 seconds, blocking all concurrent API routes and client requests.
* **Observed Evidence:**
  - `_scan_ifconfig_for_tailnet_ip()` calls `subprocess.run(["ifconfig"], timeout=2)` synchronously.
  - `_tailscale_status()` calls `subprocess.run(["tailscale", "ip", "-4"], timeout=2)` synchronously.
  - Both helpers are executed directly within the `async def get_share_info` endpoint without yielding control to the event loop, causing Uvicorn to freeze.
* **Recommended Fix:**
  Offload the network interface and Tailscale status probing to a separate worker thread using AnyIO's thread pool:
  ```python
  from anyio import to_thread

  @app.get("/share-info")
  async def get_share_info(request: Request):
      # ...
      status = await to_thread.run_sync(_tailscale_status)
      # ...
  ```

---

### 2. Synchronous Blocking FFmpeg Slice and Frame Extraction

* **Location:**
  - [backend/app/slicing.py:21-91](file:///Volumes/Extreme%20SSD/AI-Applications/smart-youtube-reader/backend/app/slicing.py#L21-L91) (within `generate_preview()`)
  - [backend/app/main.py:398-409](file:///Volumes/Extreme%20SSD/AI-Applications/smart-youtube-reader/backend/app/main.py#L398-L409) (`create_new_slice`)
  - [backend/app/main.py:417-420](file:///Volumes/Extreme%20SSD/AI-Applications/smart-youtube-reader/backend/app/main.py#L417-L420) (`create_preview`)
* **Impact:** Blocking CPU/disk operations on the event loop. During frame extraction from local MP4s, the FastAPI event loop is blocked for the duration of the FFmpeg execution (often 1-3 seconds), queueing all concurrent client requests.
* **Observed Evidence:**
  - `generate_preview` runs `ffmpeg.run(quiet=True, overwrite_output=True)` synchronously.
  - `create_slice` follows the same synchronous FFmpeg execution pattern and is invoked directly inside async route `create_new_slice`.
  - Both `create_preview` and `create_new_slice` call these blocking helpers without thread offloading.
* **Recommended Fix:**
  Offload both `generate_preview` and `create_slice` execution to Uvicorn's worker thread pool:
  ```python
  @app.post("/jobs/{job_id}/slicer/preview")
  async def create_preview(job_id: str, request: PreviewRequest):
      return await to_thread.run_sync(
          generate_preview, job_id, request.start, request.end, request.fps, job_store
      )
  ```

## Medium Severity Findings

### 3. Single-Instance MLX VLM Server Limits Concurrent Inference

* **Location:** [backend/app/mlx_runtime.py:147-172](file:///Volumes/Extreme%20SSD/AI-Applications/smart-youtube-reader/backend/app/mlx_runtime.py#L147-L172)
* **Impact:** Concurrency bottleneck in local model work. MLX VLM runs as a separate `subprocess.Popen` server, so it does not freeze Uvicorn's main event loop directly. The remaining performance risk is that the application uses a single local MLX server instance and synchronous HTTP calls to that server from worker-thread background tasks, so concurrent AI digest or question-answering jobs can serialize behind the same model process and consume worker capacity.
* **Observed Evidence:**
  - The runtime starts the model server with `subprocess.Popen([... "-m", "mlx_vlm.server", ...])`.
  - The model server is a single shared process for local inference.
  - Calls into the MLX runtime happen through background-task execution rather than directly on the FastAPI event loop, so the issue is inference throughput and queueing, not event-loop freeze.
* **Recommended Fix:**
  Add explicit inference queueing and status reporting, enforce one active generation per model server unless a multi-worker runtime is introduced, and document expected concurrency. If throughput becomes a target, evaluate multiple model server workers or a purpose-built inference service.

### 4. Cross-Origin LocalStorage State Redirection Loop

* **Location:**
  - `readStoredShareMode()` at [frontend/src/lib/api.ts](file:///Volumes/Extreme%20SSD/AI-Applications/smart-youtube-reader/frontend/src/lib/api.ts)
  - `ShareModeToggle.tsx` at [frontend/src/app/components/ShareModeToggle.tsx](file:///Volumes/Extreme%20SSD/AI-Applications/smart-youtube-reader/frontend/src/app/components/ShareModeToggle.tsx)
* **Impact:** Prevents the user from toggling the share mode back to `local` once they are redirected to a Tailscale IP. It causes a continuous redirection loop between local and Tailscale ports due to the Same-Origin Policy isolating LocalStorage partitions.
* **Observed Evidence:**
  - Toggling "Local" writes `'local'` to the `100.x.x.x` LocalStorage partition and redirects to `localhost:3001`.
  - When `localhost:3001` loads, it accesses the `localhost` LocalStorage partition (which still contains `'tailscale'`), immediately redirecting the user back to the Tailscale URL.
* **Recommended Fix:**
  *(Fixed in commit `36c37ef`)*: Simplify `readStoredShareMode()` to return the inferred mode directly from the URL hostname, and skip redirection in the toggle component if the current host matches the selected mode category.
