import uuid
import time
from typing import Dict
from .schemas import JobCreateRequest, JobResponse, JobStatus

class Job:
    def __init__(self, job_id: str, payload: JobCreateRequest):
        self.id = job_id
        self.payload = payload
        self.status = JobStatus.pending
        self.created_at = time.time()
        self.error = None
        self.package_path = None
        self.transcript_preview = None
        self.title = None
        self.data_dir = None  # Will be set by pipeline
        self.current_step = None # For UI feedback

    @property
    def data_folder_name(self) -> str:
         if self.data_dir:
             return self.data_dir.name
         return self.id

    def to_response(self) -> JobResponse:
        return JobResponse(
            id=self.id,
            status=self.status,
            video_url=self.payload.video_url,
            title=self.title,
            created_at=self.created_at,
            error=self.error,
            package_path=str(self.package_path) if self.package_path else None,
            transcript_preview=self.transcript_preview,
            data_folder_name=self.data_folder_name,
            current_step=self.current_step
        )

import shutil
import json
import re
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "jobs"
DATA_ROOT.mkdir(parents=True, exist_ok=True)

class JobStore:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """Reconstruct job state from disk."""
        if not DATA_ROOT.exists():
            return
            
        for job_dir in DATA_ROOT.iterdir():
            if not job_dir.is_dir():
                continue
                
            manifest_path = job_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r') as f:
                        data = json.load(f)
                        
                    job_id = data.get('job_id')
                    if not job_id:
                        continue
                        
                    # Reconstruct Job object
                    # We might not have original payload request, but we have url
                    from .schemas import JobCreateRequest 
                    payload = JobCreateRequest(
                        video_url=data.get('url', ''),
                        min_width=640, # defaults
                        interval_sec=1 
                    )
                    
                    job = Job(job_id, payload)
                    job.status = JobStatus.complete if data.get('archive_chapters') else JobStatus.failed # rough guess/restore
                    # A better way is to store 'status' in manifest or a separate state file.
                    # For now, let's assume if manifest exists, it's at least partially done. 
                    # Actually, manifest is written at the END of pipeline.
                    job.status = JobStatus.complete
                    
                    job.data_dir = job_dir
                    job.package_path = job_dir # simplified
                    
                    # Try to get title from transcript or inferred
                    # Ideally manifest should store title. We will update pipeline to store it.
                    job.title = data.get('title') 
                    
                    self._jobs[job_id] = job
                except Exception as e:
                    print(f"Failed to load job from {job_dir}: {e}")

    def create_job(self, payload: JobCreateRequest) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(job_id, payload)
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job:
        if job_id not in self._jobs:
            raise KeyError(f"Job {job_id} not found")
        return self._jobs[job_id]
        
    def list_jobs(self) -> list[Job]:
        # Sort by created_at (newest first)
        # created_at is default time.time() for new jobs.
        # Restored jobs set created_at to now? Or we should store created_at in manifest.
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        
    def delete_job(self, job_id: str):
        if job_id in self._jobs:
            job = self._jobs[job_id]
            # Remove from disk
            if job.data_dir and job.data_dir.exists():
                try:
                    shutil.rmtree(job.data_dir)
                except Exception as e:
                    print(f"Error deleting job directory {job.data_dir}: {e}")
            
            del self._jobs[job_id]

def slugify(value: str) -> str:
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = str(value)
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value
