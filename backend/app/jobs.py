import json
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Dict
from urllib.parse import parse_qs, urlparse

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
        self.video_ext = None
        self.kind = None
        self.source_job_id = None
        self.digest_model = None
        self.summary_image = None
        self.media_policy = None
        self._manifest_mtime = None

    @property
    def data_folder_name(self) -> str:
         if self.data_dir:
             return self.data_dir.name
         return self.id

    def refresh_manifest_metadata(self):
        if not self.data_dir:
            return

        manifest_path = self.data_dir / "manifest.json"
        if not manifest_path.exists():
            return

        try:
            mtime = manifest_path.stat().st_mtime
        except OSError:
            return

        if self._manifest_mtime == mtime:
            return

        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
        except Exception:
            return

        self._manifest_mtime = mtime
        self.title = data.get("title", self.title)
        self.kind = data.get("kind", self.kind)
        self.source_job_id = data.get("source_job_id", self.source_job_id)
        self.digest_model = data.get("digest_model", self.digest_model)
        self.summary_image = data.get("summary_image", self.summary_image)
        self.media_policy = data.get("media_policy", self.media_policy)

    def to_response(self) -> JobResponse:
        self.refresh_manifest_metadata()
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
            current_step=self.current_step,
            video_ext=self.video_ext,
            kind=self.kind,
            source_job_id=self.source_job_id,
            digest_model=self.digest_model,
            summary_image=self.summary_image,
            media_policy=self.media_policy
        )

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "jobs"
DATA_ROOT.mkdir(parents=True, exist_ok=True)
EXAMPLE_JOBS_ROOT = Path(__file__).resolve().parents[2] / "examples" / "demo-jobs"


def ensure_demo_jobs() -> None:
    if not EXAMPLE_JOBS_ROOT.exists():
        return

    for source_dir in EXAMPLE_JOBS_ROOT.iterdir():
        if not source_dir.is_dir() or not (source_dir / "manifest.json").exists():
            continue
        target_dir = DATA_ROOT / source_dir.name
        if target_dir.exists():
            continue
        shutil.copytree(source_dir, target_dir)

def normalized_video_key(video_url: str | None) -> str:
    if not video_url:
        return ""
    try:
        parsed = urlparse(video_url)
        host = parsed.netloc.lower().replace("www.", "")
        if "youtu.be" in host:
            video_id = parsed.path.strip("/").split("/")[0]
        elif "youtube.com" in host:
            parts = [part for part in parsed.path.split("/") if part]
            if parts and parts[0] in {"shorts", "embed"} and len(parts) > 1:
                video_id = parts[1]
            else:
                video_id = parse_qs(parsed.query).get("v", [""])[0]
        else:
            video_id = ""
        return video_id or video_url.strip()
    except Exception:
        return video_url.strip()

class JobStore:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """Reconstruct job state from disk."""
        ensure_demo_jobs()
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
                    job.created_at = data.get('created_at', job.created_at)
                    job.video_ext = data.get('video_ext', 'mp4')
                    job.kind = data.get('kind')
                    job.source_job_id = data.get('source_job_id')
                    job.digest_model = data.get('digest_model')
                    job.summary_image = data.get('summary_image')
                    job.media_policy = data.get('media_policy')

                    self._jobs[job_id] = job
                except Exception as e:
                    print(f"Failed to load job from {job_dir}: {e}")

    def create_job(self, payload: JobCreateRequest) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(job_id, payload)
        self._jobs[job_id] = job
        return job

    def find_reusable_job(self, payload: JobCreateRequest) -> Job | None:
        self._load_from_disk()
        requested_key = normalized_video_key(payload.video_url)
        if not requested_key:
            return None

        matches = [
            job for job in self._jobs.values()
            if not job.kind
            and job.status != JobStatus.failed
            and normalized_video_key(job.payload.video_url) == requested_key
        ]
        if not matches:
            return None

        status_rank = {
            JobStatus.complete: 0,
            JobStatus.processing: 1,
            JobStatus.pending: 2,
        }
        return sorted(
            matches,
            key=lambda job: (status_rank.get(job.status, 9), -job.created_at)
        )[0]

    def register_completed_job(
        self,
        job_id: str,
        video_url: str,
        data_dir: Path,
        title: str,
        created_at: float | None = None,
        video_ext: str | None = "mp4",
        kind: str | None = None,
        source_job_id: str | None = None,
        digest_model: str | None = None,
        summary_image: str | None = None,
        media_policy: str | None = None,
    ) -> Job:
        payload = JobCreateRequest(video_url=video_url)
        job = Job(job_id, payload)
        job.status = JobStatus.complete
        job.created_at = created_at or time.time()
        job.data_dir = data_dir
        job.package_path = data_dir
        job.title = title
        job.video_ext = video_ext
        job.kind = kind
        job.source_job_id = source_job_id
        job.digest_model = digest_model
        job.summary_image = summary_image
        job.media_policy = media_policy
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job:
        if job_id not in self._jobs:
            self._load_from_disk()
        if job_id not in self._jobs:
            raise KeyError(f"Job {job_id} not found")
        return self._jobs[job_id]
        
    def list_jobs(self) -> list[Job]:
        self._load_from_disk()
        deduped: dict[tuple[str, str], Job] = {}
        status_rank = {
            JobStatus.complete: 0,
            JobStatus.processing: 1,
            JobStatus.pending: 2,
            JobStatus.failed: 3,
        }
        for job in self._jobs.values():
            key = (job.kind, job.id) if job.kind else ("source", normalized_video_key(job.payload.video_url) or job.id)
            existing = deduped.get(key)
            if existing is None:
                deduped[key] = job
                continue
            current_rank = (status_rank.get(job.status, 9), -job.created_at)
            existing_rank = (status_rank.get(existing.status, 9), -existing.created_at)
            if current_rank < existing_rank:
                deduped[key] = job

        return sorted(deduped.values(), key=lambda j: j.created_at, reverse=True)
        
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
