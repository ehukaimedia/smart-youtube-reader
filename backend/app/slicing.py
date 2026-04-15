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

    ext = getattr(job, 'video_ext', None) or 'mp4'
    video_path = job.data_dir / f"video.{ext}"
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
        ext = getattr(job, 'video_ext', None) or 'mp4'
        video_path = job.data_dir / f"video.{ext}"
        if not video_path.exists():
            videos = list(job.data_dir.glob("video.*"))
            video_path = videos[0] if videos else video_path
        
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
    Saves selected frames into the job's archive.json, updating the matching chapter's images.
    The operator uses this to curate the visual evidence shown to agents and readers.
    """
    import json

    job = job_store.get(job_id)
    preview_dir = job.data_dir / "previews" / preview_id

    meta_path = preview_dir / "preview_meta.json"
    if not meta_path.exists():
        raise ValueError("Preview metadata missing. Cannot calculate timings.")

    with open(meta_path, 'r') as f:
        meta = json.load(f)

    start_time = meta['start']
    fps = meta['fps']

    # Copy frames into a permanent slice directory
    slice_id = str(uuid.uuid4())[:8]
    slice_dir = job.data_dir / "slices" / slice_id
    frames_dir = slice_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    saved_frames = []
    image_paths = []  # relative paths for archive.json

    for filename in selected_files:
        src = preview_dir / filename
        if src.exists():
            shutil.copy(src, frames_dir / filename)
            try:
                frame_num = int(Path(filename).stem)
                time_offset = (frame_num - 1) / fps
                absolute_time = start_time + time_offset
                saved_frames.append({
                    "filename": filename,
                    "timestamp": round(absolute_time, 3),
                    "relative_time": round(time_offset, 3)
                })
            except:
                pass
            image_paths.append(f"slices/{slice_id}/frames/{filename}")

    # Save slice manifest
    manifest = {
        "id": slice_id,
        "source_job": job_id,
        "fps": fps,
        "base_start_time": start_time,
        "frames": saved_frames
    }
    with open(slice_dir / "slice.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Update archive.json — inject images into the best matching chapter
    archive_path = job.data_dir / "archive.json"
    if archive_path.exists() and image_paths:
        with open(archive_path, 'r') as f:
            archive = json.load(f)

        chapters = archive.get('archive', [])

        # Find the chapter whose time window best contains the slice start time
        best_chapter = None
        for chapter in chapters:
            c_start = chapter.get('timestamp_start', 0)
            c_end = chapter.get('timestamp_end', c_start + 60)
            if c_start <= start_time <= c_end:
                best_chapter = chapter
                break

        # Fallback: nearest chapter by start time
        if best_chapter is None and chapters:
            best_chapter = min(chapters, key=lambda c: abs(c.get('timestamp_start', 0) - start_time))

        if best_chapter is not None:
            # Stash original AI-generated images so delete can restore them
            if '_original_images' not in best_chapter:
                best_chapter['_original_images'] = best_chapter.get('images', [])
            # Replace existing images with operator-curated ones
            # Tag each path so we can remove them if the slice is deleted
            best_chapter['images'] = image_paths
            best_chapter['_slice_id'] = slice_id  # track which slice owns these images

            with open(archive_path, 'w') as f:
                json.dump(archive, f)

    return {
        "id": slice_id,
        "path": f"slices/{slice_id}",
        "manifest": manifest,
        "images_added": len(image_paths)
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
