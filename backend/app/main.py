from dotenv import load_dotenv
load_dotenv()

import os
import socket
import subprocess
import tempfile
import zipfile
from ipaddress import ip_address, ip_network

from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .jobs import JobStore
from .schemas import JobCreateRequest, JobResponse, SliceRequest, PreviewRequest, FinalizeRequest, SaveSliceRequest, ArchiveImageUpdateRequest
from .pipeline import run_pipeline
from .slicing import create_slice, generate_preview, finalize_sequence
from .mlx_runtime import AVAILABLE_MODELS, DEFAULT_MODEL, list_loaded_models

# Adjust path to point to project_root/data/jobs
# main.py is in backend/app/main.py
# parents[0] = app
# parents[1] = backend
# parents[2] = project_root
DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "jobs"
DATA_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Smart YouTube Reader", version="1.0.0")

# CORS — the dashboard/reader is served by the Next.js frontend on port 3001 and
# calls this API on port 8001 (cross-origin by port). Allow only the local frontend
# and, when sharing over a tailnet, the same host on the 100.x range — never a
# wildcard origin. No cookie/credential flow exists, so credentials are disabled
# (a wildcard origin with credentials would let any visited site read local data).
_cors_kwargs = dict(
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|\[::1\]|100\.\d{1,3}\.\d{1,3}\.\d{1,3}):3001$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
_public_share_origin = os.environ.get("PUBLIC_SHARE_ORIGIN")
if _public_share_origin:
    _cors_kwargs["allow_origins"] = [_public_share_origin.rstrip("/")]
app.add_middleware(CORSMiddleware, **_cors_kwargs)

app.mount("/data/jobs", StaticFiles(directory=DATA_ROOT), name="jobs_data")

job_store = JobStore()


TAILSCALE_NETWORK = ip_network("100.64.0.0/10")
TAILSCALE_INSTALL_URL = "https://tailscale.com/download/macos"


def _scan_ifconfig_for_tailnet_ip() -> str | None:
    try:
        result = subprocess.run(
            ["ifconfig"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0] == "inet":
            try:
                if ip_address(parts[1]) in TAILSCALE_NETWORK:
                    return parts[1]
            except ValueError:
                continue
    return None


def _scan_hostname_for_tailnet_ip() -> str | None:
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidate = info[4][0]
            try:
                if ip_address(candidate) in TAILSCALE_NETWORK:
                    return candidate
            except ValueError:
                continue
    except Exception:
        return None
    return None


def _tailscale_status() -> dict[str, str | None]:
    """Probe Tailscale state, distinguishing not-installed / not-running / no-ip."""
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except FileNotFoundError:
        # No `tailscale` binary on PATH. Fall back to scanning interfaces so
        # users on a tailnet without the CLI still get a working share IP,
        # but report not_installed when nothing turns up.
        ip = _scan_ifconfig_for_tailnet_ip() or _scan_hostname_for_tailnet_ip()
        if ip:
            return {"ip": ip, "status": "available"}
        return {"ip": None, "status": "not_installed"}
    except Exception:
        ip = _scan_ifconfig_for_tailnet_ip() or _scan_hostname_for_tailnet_ip()
        if ip:
            return {"ip": ip, "status": "available"}
        return {"ip": None, "status": "not_running"}

    if result.returncode != 0:
        ip = _scan_ifconfig_for_tailnet_ip() or _scan_hostname_for_tailnet_ip()
        if ip:
            return {"ip": ip, "status": "available"}
        return {"ip": None, "status": "not_running"}

    for line in result.stdout.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        try:
            if ip_address(candidate) in TAILSCALE_NETWORK:
                return {"ip": candidate, "status": "available"}
        except ValueError:
            continue

    ip = _scan_ifconfig_for_tailnet_ip() or _scan_hostname_for_tailnet_ip()
    if ip:
        return {"ip": ip, "status": "available"}
    return {"ip": None, "status": "no_tailnet_ip"}


def _build_job_zip(job_dir: Path, zip_path: Path) -> None:
    top_level = job_dir.name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for path in sorted(job_dir.rglob("*")):
            if not path.is_file():
                continue
            archive_name = Path(top_level) / path.relative_to(job_dir)
            zf.write(path, archive_name)


def _validate_job_relative_path(job_dir: Path, relative_path: str, require_exists: bool = True) -> Path:
    if not relative_path or Path(relative_path).is_absolute():
        raise HTTPException(status_code=400, detail="Invalid image path")

    resolved = (job_dir / relative_path).resolve()
    if not resolved.is_relative_to(job_dir.resolve()):
        raise HTTPException(status_code=400, detail="Invalid image path")

    if require_exists and (not resolved.exists() or not resolved.is_file()):
        raise HTTPException(status_code=404, detail="Image file not found")

    if require_exists and resolved.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="Path is not an image")

    return resolved


def _slice_id_from_archive_image(image_path: str) -> str | None:
    parts = image_path.split("/")
    if len(parts) >= 2 and parts[0] == "slices" and parts[1]:
        return parts[1]
    return None


def _append_unique_slice_id(slice_ids: list[str], slice_id: str | None) -> None:
    if slice_id and slice_id not in slice_ids:
        slice_ids.append(slice_id)


@app.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(payload: JobCreateRequest, background_tasks: BackgroundTasks):
    existing = job_store.find_reusable_job(payload)
    if existing:
        return existing.to_response()

    job = job_store.create_job(payload)
    background_tasks.add_task(run_pipeline, job.id, payload, job_store)
    return job.to_response()

@app.get("/jobs", response_model=list[JobResponse])
async def list_jobs():
    return [job.to_response() for job in job_store.list_jobs()]

@app.get("/share-info")
async def get_share_info(request: Request):
    frontend_port = os.environ.get("FRONTEND_PORT", "3001")
    configured_origin = os.environ.get("PUBLIC_SHARE_ORIGIN")
    scheme = request.url.scheme
    local_origin = f"{scheme}://localhost:{frontend_port}"

    if configured_origin:
        override = configured_origin.rstrip("/")
        return {
            "default_mode": "local",
            "modes": {
                "local": {"share_origin": override, "available": True},
                "tailscale": {"share_origin": override, "available": True},
            },
            "configured_override": True,
            # Legacy field for clients that pre-date the modes shape.
            # Mirrors the override so existing consumers see the same URL.
            "share_origin": override,
        }

    status = _tailscale_status()
    tailscale_available = status["status"] == "available" and bool(status["ip"])
    tailscale_origin = (
        f"{scheme}://{status['ip']}:{frontend_port}" if tailscale_available else None
    )

    return {
        "default_mode": "local",
        "modes": {
            "local": {"share_origin": local_origin, "available": True},
            "tailscale": {
                "share_origin": tailscale_origin,
                "available": tailscale_available,
                "status": status["status"],
                "install_url": TAILSCALE_INSTALL_URL,
            },
        },
        "configured_override": False,
        # Legacy field for clients that pre-date the modes shape. Defaults to
        # the Local origin so legacy consumers track the new default mode and
        # do not silently flip a user to a Tailscale URL they did not choose.
        "share_origin": local_origin,
    }

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    try:
        job = job_store.get(job_id)
        return job.to_response()
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

@app.delete("/jobs/{job_id}", status_code=204)
async def delete_job(job_id: str):
    try:
        job_store.delete_job(job_id)
        return
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

@app.get("/jobs/{job_id}/download")
async def download_job(job_id: str, background_tasks: BackgroundTasks):
    try:
        job = job_store.get(job_id)
        if not job.data_dir or not job.data_dir.exists():
            raise HTTPException(status_code=404, detail="Job files not found")

        data_root = DATA_ROOT.resolve()
        job_dir = job.data_dir.resolve()
        if not job_dir.is_relative_to(data_root):
            raise HTTPException(status_code=400, detail="Invalid job directory")

        fd, temp_name = tempfile.mkstemp(prefix=f"{job.data_folder_name}-", suffix=".zip")
        os.close(fd)
        zip_path = Path(temp_name)

        try:
            _build_job_zip(job_dir, zip_path)
        except Exception:
            zip_path.unlink(missing_ok=True)
            raise

        background_tasks.add_task(zip_path.unlink, missing_ok=True)
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{job.data_folder_name}.zip",
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

@app.get("/jobs/{job_id}/transcript")
async def get_transcript(job_id: str):
    try:
        job = job_store.get(job_id)
        if not job.data_dir:
             raise HTTPException(status_code=404, detail="Transcript not found (no data dir)")
        
        transcript_path = job.data_dir / "transcript.json"
        if not transcript_path.exists():
            raise HTTPException(status_code=404, detail="Transcript file not found")
            
        return FileResponse(transcript_path)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

@app.get("/jobs/{job_id}/archive")
async def get_archive(job_id: str):
    try:
        import json
        job = job_store.get(job_id)
        if not job.data_dir or not job.data_dir.exists():
            raise HTTPException(status_code=404, detail="Job files not found")

        archive_path = job.data_dir / "archive.json"
        if not archive_path.exists():
            raise HTTPException(status_code=404, detail="Archive file not found")

        with open(archive_path, "r") as f:
            archive = json.load(f)

        return JSONResponse(
            archive,
            headers={
                "Cache-Control": "no-store, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

@app.post("/jobs/{job_id}/archive/image")
async def update_archive_image(job_id: str, request: ArchiveImageUpdateRequest):
    try:
        import json
        job = job_store.get(job_id)
        if not job.data_dir or not job.data_dir.exists():
            raise HTTPException(status_code=404, detail="Job files not found")

        job_dir = job.data_dir.resolve()
        archive_path = job_dir / "archive.json"
        if not archive_path.exists():
            raise HTTPException(status_code=404, detail="Archive file not found")

        _validate_job_relative_path(job_dir, request.image_path, require_exists=False)
        with open(archive_path, "r") as f:
            archive = json.load(f)

        chapters = archive.get("archive", [])
        if request.chapter_index < 0 or request.chapter_index >= len(chapters):
            raise HTTPException(status_code=404, detail="Chapter not found")

        target_index = request.chapter_index
        chapter = chapters[target_index]
        images = list(chapter.get("images", []))
        if request.image_path not in images:
            if request.timestamp_start is not None:
                for index, candidate in enumerate(chapters):
                    candidate_time = candidate.get("timestamp_start")
                    candidate_images = list(candidate.get("images", []))
                    if (
                        candidate_time is not None
                        and abs(float(candidate_time) - request.timestamp_start) < 0.001
                        and request.image_path in candidate_images
                    ):
                        target_index = index
                        chapter = candidate
                        images = candidate_images
                        break

            if request.image_path not in images:
                for index, candidate in enumerate(chapters):
                    candidate_images = list(candidate.get("images", []))
                    if request.image_path in candidate_images:
                        target_index = index
                        chapter = candidate
                        images = candidate_images
                        break

            if request.image_path not in images:
                return {"images": images, "removed": False, "chapter_index": target_index}

        images = [image for image in images if image != request.image_path]

        chapter["images"] = images
        with open(archive_path, "w") as f:
            json.dump(archive, f, indent=2)

        return {"images": images, "removed": True, "chapter_index": target_index}
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

@app.get("/models")
async def list_models():
    loaded = set(list_loaded_models())
    models = [model["name"] for model in AVAILABLE_MODELS]
    return {
        "models": models,
        "default_model": DEFAULT_MODEL,
        "model_details": [
            {**model, "loaded": model["name"] in loaded}
            for model in AVAILABLE_MODELS
        ],
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/jobs/{job_id}/slice")
async def create_new_slice(job_id: str, request: SliceRequest):
    try:
        result = create_slice(
            job_id=job_id,
            start=request.start,
            end=request.end,
            format_type=request.format,
            fps=request.fps,
            job_store=job_store
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Slice error: {e}")
        raise HTTPException(status_code=500, detail="Slicing failed")


@app.post("/jobs/{job_id}/slicer/preview")
async def create_preview(job_id: str, request: PreviewRequest):
    try:
        return generate_preview(job_id, request.start, request.end, request.fps, job_store)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"Preview error: {e}")
        raise HTTPException(status_code=500, detail="Preview generation failed")

@app.post("/jobs/{job_id}/slicer/finalize")
async def finalize_slice(job_id: str, request: FinalizeRequest):
    try:
        return finalize_sequence(job_id, request.preview_id, request.selected_files, job_store)
    except Exception as e:
        print(f"Finalize error: {e}")
        raise HTTPException(status_code=500, detail="Finalization failed")

@app.post("/jobs/{job_id}/slicer/save")
async def save_slicer_to_project(job_id: str, request: SaveSliceRequest):
    try:
        from .slicing import save_slice_to_project
        result = save_slice_to_project(
            job_id,
            request.preview_id,
            request.selected_files,
            job_store,
            target_chapter_index=request.target_chapter_index,
            replace_image_path=request.replace_image_path,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Save error: {e}")
        raise HTTPException(status_code=500, detail="Save failed")

@app.get("/jobs/{job_id}/slices")
async def get_job_slices(job_id: str):
    try:
        from .slicing import list_slices
        return list_slices(job_id, job_store)
    except KeyError:
         raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        print(f"List slices error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list slices")

@app.delete("/jobs/{job_id}/slices/{slice_id}", status_code=204)
async def delete_slice(job_id: str, slice_id: str):
    try:
        import shutil, json
        job = job_store.get(job_id)
        slice_dir = job.data_dir / "slices" / slice_id
        if not slice_dir.exists():
            raise HTTPException(status_code=404, detail="Slice not found")

        # Remove slice images from archive.json
        archive_path = job.data_dir / "archive.json"
        if archive_path.exists():
            with open(archive_path, 'r') as f:
                archive = json.load(f)
            for chapter in archive.get('archive', []):
                images = list(chapter.get('images', []))
                slice_prefix = f"slices/{slice_id}/"
                ordered_slice_ids = []
                for existing_slice_id in chapter.get('_slice_ids') or []:
                    _append_unique_slice_id(ordered_slice_ids, existing_slice_id)
                _append_unique_slice_id(ordered_slice_ids, chapter.get('_slice_id'))
                for image in images:
                    _append_unique_slice_id(ordered_slice_ids, _slice_id_from_archive_image(image))

                has_deleted_slice_images = any(image.startswith(slice_prefix) for image in images)
                if slice_id not in ordered_slice_ids and not has_deleted_slice_images:
                    continue

                remaining_images = [image for image in images if not image.startswith(slice_prefix)]
                remaining_image_slice_ids = []
                for image in remaining_images:
                    _append_unique_slice_id(remaining_image_slice_ids, _slice_id_from_archive_image(image))
                remaining_metadata_slice_ids = [
                    existing_slice_id
                    for existing_slice_id in ordered_slice_ids
                    if existing_slice_id != slice_id
                ]
                for remaining_image_slice_id in remaining_image_slice_ids:
                    _append_unique_slice_id(remaining_metadata_slice_ids, remaining_image_slice_id)
                latest_remaining_image_slice_id = next(
                    (
                        existing_slice_id
                        for existing_slice_id in reversed(remaining_metadata_slice_ids)
                        if existing_slice_id in remaining_image_slice_ids
                    ),
                    None,
                )

                if not has_deleted_slice_images:
                    if remaining_metadata_slice_ids:
                        chapter['_slice_ids'] = remaining_metadata_slice_ids
                    else:
                        chapter.pop('_slice_ids', None)
                    if chapter.get('_slice_id') == slice_id:
                        if latest_remaining_image_slice_id:
                            chapter['_slice_id'] = latest_remaining_image_slice_id
                        else:
                            chapter.pop('_slice_id', None)
                elif latest_remaining_image_slice_id:
                    chapter['images'] = remaining_images
                    chapter['_slice_ids'] = remaining_metadata_slice_ids
                    chapter['_slice_id'] = latest_remaining_image_slice_id
                else:
                    chapter['images'] = chapter.pop('_original_images', remaining_images)
                    chapter.pop('_slice_id', None)
                    if remaining_metadata_slice_ids:
                        chapter['_slice_ids'] = remaining_metadata_slice_ids
                    else:
                        chapter.pop('_slice_ids', None)
            with open(archive_path, 'w') as f:
                json.dump(archive, f)

        shutil.rmtree(slice_dir)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")
