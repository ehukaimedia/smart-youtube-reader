import ffmpeg
from pathlib import Path
import os
import uuid
import zipfile
import shutil
from .jobs import JobStore

def generate_preview(job_id: str, start: float, end: float, fps: int, job_store: JobStore):
    """
    Extracts all frames in the range to a temporary preview directory.
    Returns preview_id and list of frame filenames.
    """
    if not job_store:
        raise ValueError("JobStore required")

    # Validation: Max 10 seconds
    if (end - start) > 10.0:
        raise ValueError("Slice duration cannot exceed 10 seconds")

    job = job_store.get(job_id)
    if not job.data_dir:
        raise ValueError("Job data directory not found")

    video_path = job.data_dir / "video.mp4"
    if not video_path.exists():
        videos = list(job.data_dir.glob("video.*"))
        if videos:
            video_path = videos[0]
        else:
             raise FileNotFoundError("Video file not found in job directory")

    preview_id = str(uuid.uuid4())[:8]
    preview_dir = job.data_dir / "previews" / preview_id
    preview_dir.mkdir(parents=True, exist_ok=True)

    # Extract all frames
    output_pattern = str(preview_dir / "%04d.jpg")
    
    try:
        (
            ffmpeg
            .input(str(video_path), ss=start, t=end-start)
            .filter('fps', fps=fps)
            .output(output_pattern, qscale=2)
            .run(quiet=True, overwrite_output=True)
        )
    except ffmpeg.Error as e:
        print(e.stderr.decode() if e.stderr else str(e))
        raise RuntimeError("FFmpeg frame extraction failed")

    # List generated files
    frames = sorted([f.name for f in preview_dir.glob("*.jpg")])
    
    # Save metadata for later timestamp calculation
    import json
    with open(preview_dir / "preview_meta.json", "w") as f:
        json.dump({"start": start, "end": end, "fps": fps}, f)
    
    # Cleanup old previews (Aggressive: delete ALL old previews)
    try:
        cleanup_old_previews(job.data_dir / "previews", keep=0, exclude=preview_id)
    except Exception as e:
        print(f"Cleanup warning: {e}")

    return {
        "preview_id": preview_id,
        "frames": frames,
        "base_url": f"previews/{preview_id}"
    }

def cleanup_old_previews(previews_dir: Path, keep: int = 1, exclude: str = None):
    """
    Deletes old preview directories, keeping only the most recent 'keep' count.
    """
    if not previews_dir.exists():
        return

    # List all subdirectories
    dirs = []
    for d in previews_dir.iterdir():
        if d.is_dir() and d.name != exclude:
            # Get modification time
            dirs.append((d.stat().st_mtime, d))
    
    # Sort by time descending (newest first)
    dirs.sort(key=lambda x: x[0], reverse=True)
    
    # Delete those beyond 'keep'
    for _, d in dirs[keep:]:
        shutil.rmtree(d, ignore_errors=True)

def finalize_sequence(job_id: str, preview_id: str, selected_files: list[str], job_store: JobStore):
    """
    Zips the selected frames from the preview directory.
    """
    job = job_store.get(job_id)
    preview_dir = job.data_dir / "previews" / preview_id
    if not preview_dir.exists():
        raise ValueError("Preview session expired or not found")

    slice_id = str(uuid.uuid4())[:8]
    slices_dir = job.data_dir / "slices" / slice_id
    slices_dir.mkdir(parents=True, exist_ok=True)

    zip_path = slices_dir / "sequence.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for filename in selected_files:
            file_path = preview_dir / filename
            if file_path.exists():
                zf.write(file_path, filename)
    
    # Optional: Clean up preview? Maybe keep for a bit.
    # shutil.rmtree(preview_dir) 

    return {
        "id": slice_id,
        "path": f"slices/{slice_id}/sequence.zip"
    }

def create_slice(job_id: str, start: float, end: float, format_type: str, fps: int = 24, job_store: JobStore = None):
    """
    Legacy/Direct MP4 Slicing.
    """
    # Quick fix to keep MP4 working
    if format_type == "mp4":
        if not job_store: raise ValueError("JobStore required")
        job = job_store.get(job_id)
        video_path = job.data_dir / "video.mp4" # Simplify for brevity, full check in real code
        
        slice_id = str(uuid.uuid4())[:8]
        slices_dir = job.data_dir / "slices" / slice_id
        slices_dir.mkdir(parents=True, exist_ok=True)
        output_path = slices_dir / "clip.mp4"
        
        (
            ffmpeg
            .input(str(video_path), ss=start, t=end-start)
            .output(str(output_path), c="copy") 
            .run(quiet=True, overwrite_output=True)
        )
        return { "id": slice_id, "path": f"slices/{slice_id}/clip.mp4", "format": "mp4" }
        raise ValueError("For sequences, please use the preview flow.")

def save_slice_to_project(job_id: str, preview_id: str, selected_files: list[str], job_store: JobStore):
    """
    Saves selected frames into a permanent project slice directory with timing metadata.
    """
    import json
    
    job = job_store.get(job_id)
    preview_dir = job.data_dir / "previews" / preview_id
    
    # We need to recover the start time and fps to calculate timestamps. 
    # Ideally, we should have stored this in the preview dir or pass it in.
    # For now, let's assume valid files are there. 
    # A robust way is to store a metadata.json in generate_preview.
    
    # Let's try to read metadata from the preview dir if it existed, 
    # OR we just re-calculate it if we assume files are named 0001.jpg etc.
    # But we need 'start' and 'fps'. 
    # HACK: We will look for a 'preview_meta.json' which we will Add to generate_preview now.
    
    meta_path = preview_dir / "preview_meta.json"
    if not meta_path.exists():
         raise ValueError("Preview metadata missing. Cannot calculate timings.")
         
    with open(meta_path, 'r') as f:
        meta = json.load(f)
        
    start_time = meta['start']
    fps = meta['fps']
    
    slice_id = str(uuid.uuid4())[:8]
    slice_dir = job.data_dir / "slices" / slice_id
    frames_dir = slice_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    
    saved_frames = []
    
    for filename in selected_files:
        src = preview_dir / filename
        if src.exists():
            shutil.copy(src, frames_dir / filename)
            
            # Calculate timestamp
            # filename is like "0001.jpg". Frame 1 is at start + 0.
            try:
                frame_num = int(Path(filename).stem)
                # Frame 1 is index 0
                time_offset = (frame_num - 1) / fps
                absolute_time = start_time + time_offset
                
                saved_frames.append({
                    "filename": filename,
                    "timestamp": round(absolute_time, 3),
                    "relative_time": round(time_offset, 3)
                })
            except:
                pass

    # Save Manifest for this slice
    manifest = {
        "id": slice_id,
        "source_job": job_id,
        "created_at": str(uuid.uuid1()), # simple timestamp
        "fps": fps,
        "base_start_time": start_time,
        "frames": saved_frames
    }
    
    with open(slice_dir / "slice.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    return {
        "id": slice_id,
        "path": f"slices/{slice_id}",
        "manifest": manifest
    }

def list_slices(job_id: str, job_store: JobStore):
    """
    Lists all saved slices for a job.
    """
    import json
    
    job = job_store.get(job_id)
    slices_dir = job.data_dir / "slices"
    if not slices_dir.exists():
        return []

    slices = []
    # Sort by creation time if possible, or just name
    for path in sorted(slices_dir.iterdir()):
        if path.is_dir():
            manifest_path = path / "slice.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r') as f:
                        data = json.load(f)
                        slices.append(data)
                except:
                    pass
    return slices
