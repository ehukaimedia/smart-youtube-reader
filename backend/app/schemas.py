from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    failed = "failed"

class JobCreateRequest(BaseModel):
    video_url: str
    interval_sec: int = 15
    min_width: int = 1280
    max_width: int = 1920
    model: str = "gemini-3-flash-preview"

class JobResponse(BaseModel):
    id: str
    status: JobStatus
    video_url: str
    title: Optional[str] = None
    created_at: float
    error: Optional[str] = None
    package_path: Optional[str] = None
    transcript_preview: Optional[str] = None
    data_folder_name: Optional[str] = None
    current_step: Optional[str] = None
    video_ext: Optional[str] = None

class SliceRequest(BaseModel):
    start: float
    end: float
    format: str = "mp4" # mp4 or sequence
    fps: int = 24

class PreviewRequest(BaseModel):
    start: float
    end: float
    fps: int

class FinalizeRequest(BaseModel):
    preview_id: str
    selected_files: List[str]

class SaveSliceRequest(BaseModel):
    preview_id: str
    selected_files: List[str]
