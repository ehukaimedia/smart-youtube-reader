from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .jobs import JobStore
from .schemas import JobCreateRequest, JobResponse, SliceRequest, PreviewRequest, FinalizeRequest, SaveSliceRequest
from .pipeline import run_pipeline
from .slicing import create_slice, generate_preview, finalize_sequence

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

@app.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(payload: JobCreateRequest, background_tasks: BackgroundTasks):
    job = job_store.create_job(payload)
    background_tasks.add_task(run_pipeline, job.id, payload, job_store)
    return job.to_response()

@app.get("/jobs", response_model=list[JobResponse])
async def list_jobs():
    return [job.to_response() for job in job_store.list_jobs()]

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
async def download_job(job_id: str):
    try:
        job = job_store.get(job_id)
        if not job.package_path:
             raise HTTPException(status_code=400, detail="Job not ready or package missing")
        # TODO: Implement zip creation if not done in pipeline
        # For now, return a placeholder or file
        return {"message": "Download not fully implemented in pipeline yet, but job is done."}
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
