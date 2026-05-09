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
from .schemas import JobCreateRequest, JobResponse, SliceRequest, PreviewRequest, FinalizeRequest, SaveSliceRequest, ArchiveImageUpdateRequest, DigestCreateRequest
from .pipeline import run_pipeline
from .slicing import create_slice, generate_preview, finalize_sequence
from .digest import create_digest_version, get_digest_agent_models

# Adjust path to point to project_root/data/jobs
# main.py is in backend/app/main.py
# parents[0] = app
# parents[1] = backend
# parents[2] = project_root
DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "jobs"
DATA_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Smart YouTube Reader", version="1.0.0")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/data/jobs", StaticFiles(directory=DATA_ROOT), name="jobs_data")

job_store = JobStore()


def _get_tailscale_ip() -> str | None:
    tailscale_network = ip_network("100.64.0.0/10")

    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                candidate = line.strip()
                if candidate and ip_address(candidate) in tailscale_network:
                    return candidate
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["ifconfig"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[0] == "inet":
                    candidate = parts[1]
                    if ip_address(candidate) in tailscale_network:
                        return candidate
    except Exception:
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidate = info[4][0]
            if ip_address(candidate) in tailscale_network:
                return candidate
    except Exception:
        pass

    return None


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

@app.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(payload: JobCreateRequest, background_tasks: BackgroundTasks):
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
    if configured_origin:
        return {"share_origin": configured_origin.rstrip("/")}

    request_host = request.url.hostname or "localhost"
    local_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    share_host = _get_tailscale_ip() if request_host in local_hosts else request_host
    share_host = share_host or request_host

    return {"share_origin": f"{request.url.scheme}://{share_host}:{frontend_port}"}

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

@app.get("/digest-models")
async def list_digest_models():
    return {"models": get_digest_agent_models()}

@app.post("/jobs/{job_id}/digest", response_model=JobResponse)
async def create_ai_digest(job_id: str, request: DigestCreateRequest):
    job = create_digest_version(job_store, job_id, request.model)
    return job.to_response()

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
    models = []

    # Only expose smart-reader — the tuned Modelfile for archive generation
    try:
        import ollama
        result = ollama.list()
        available = {m.model for m in result.models if m.model}
        if "smart-reader:latest" in available:
            models.append("smart-reader:latest")
    except Exception:
        pass

    # NVIDIA NIM models (curated) — shown when API key is configured
    import os
    if os.environ.get('NVIDIA_API_KEY'):
        models.extend([
            "moonshotai/kimi-k2-instruct",            # free, reasoning + coding + agentic
            "z-ai/glm-4.7",                           # free, multilingual, tool use
            "deepseek-ai/deepseek-v3.2",              # free, 685B reasoning, long context
        ])

    return {"models": models}

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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
        result = save_slice_to_project(job_id, request.preview_id, request.selected_files, job_store)
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
                if chapter.get('_slice_id') == slice_id:
                    chapter['images'] = chapter.pop('_original_images', [])
                    del chapter['_slice_id']
            with open(archive_path, 'w') as f:
                json.dump(archive, f)

        shutil.rmtree(slice_dir)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")
