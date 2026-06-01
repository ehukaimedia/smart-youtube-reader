import ffmpeg
from pathlib import Path
import os
import json
import logging
import uuid
import zipfile
import shutil
from .jobs import JobStore

logger = logging.getLogger(__name__)

def _slice_id_from_image_path(image_path: str) -> str | None:
    parts = image_path.split("/")
    if len(parts) >= 2 and parts[0] == "slices" and parts[1]:
        return parts[1]
    return None


def _resolve_preview_file(preview_dir: Path, filename: str) -> Path:
    """Resolve a caller-supplied preview filename safely, rejecting path traversal.

    Selected frame files are always bare basenames like "0001.jpg" (produced by the
    "%04d.jpg" ffmpeg pattern). Anything with a directory component, an absolute path,
    or a name that escapes ``preview_dir`` is rejected so a malicious ``selected_files``
    entry (e.g. "../../../etc/passwd") cannot be read into a slice or zip.
    """
    if not filename or filename != os.path.basename(filename):
        raise ValueError(f"Invalid frame filename: {filename!r}")
    candidate = (preview_dir / filename).resolve()
    if not candidate.is_relative_to(preview_dir.resolve()):
        raise ValueError(f"Frame path escapes the preview directory: {filename!r}")
    return candidate


def _append_unique(values: list[str], value: str | None) -> None:
    if value and value not in values:
        values.append(value)


def generate_preview(job_id: str, start: float, end: float, fps: int, job_store: JobStore):
    """
    Extracts all frames in the range to a temporary preview directory.
    Returns preview_id and list of frame filenames.
    """
    if not job_store:
        raise ValueError("JobStore required")

    if end <= start:
        raise ValueError("Slice end time must be after start time")
    if fps <= 0 or fps > 60:
        raise ValueError("Preview FPS must be between 1 and 60")

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
        detail = e.stderr.decode(errors="replace") if e.stderr else str(e)
        logger.error("FFmpeg frame extraction failed: %s", detail)
        raise RuntimeError(f"FFmpeg frame extraction failed: {detail[-500:]}")

    # List generated files
    frames = sorted([f.name for f in preview_dir.glob("*.jpg")])
    if not frames:
        raise ValueError("No preview frames were generated for that time range")

    # Save metadata for later timestamp calculation
    with open(preview_dir / "preview_meta.json", "w") as f:
        json.dump({"start": start, "end": end, "fps": fps}, f)

    # Cleanup old previews (Aggressive: delete ALL old previews)
    try:
        cleanup_old_previews(job.data_dir / "previews", keep=0, exclude=preview_id)
    except Exception as e:
        logger.warning("Preview cleanup warning: %s", e)

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
            file_path = _resolve_preview_file(preview_dir, filename)
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
        if not job_store:
            raise ValueError("JobStore required")
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

def save_slice_to_project(
    job_id: str,
    preview_id: str,
    selected_files: list[str],
    job_store: JobStore,
    target_chapter_index: int | None = None,
    replace_image_path: str | None = None,
):
    """
    Saves selected frames into the job's archive.json, updating the matching chapter's images.
    The operator uses this to curate the visual evidence shown to agents and readers.
    """
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
        src = _resolve_preview_file(preview_dir, filename)
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
            except (ValueError, ZeroDivisionError):
                # Non-numeric frame name or zero fps — keep the image, skip timing.
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

        best_chapter = None
        chapter_index = None
        if target_chapter_index is not None:
            if target_chapter_index < 0 or target_chapter_index >= len(chapters):
                raise ValueError("Target chapter is no longer available")
            best_chapter = chapters[target_chapter_index]
            chapter_index = target_chapter_index
        else:
            # Find the chapter whose time window best contains the slice start time
            for index, chapter in enumerate(chapters):
                c_start = chapter.get('timestamp_start', 0)
                c_end = chapter.get('timestamp_end', c_start + 60)
                if c_start <= start_time <= c_end:
                    best_chapter = chapter
                    chapter_index = index
                    break

            # Fallback: nearest chapter by start time
            if best_chapter is None and chapters:
                chapter_index, best_chapter = min(
                    enumerate(chapters),
                    key=lambda item: abs(item[1].get('timestamp_start', 0) - start_time)
                )

        if best_chapter is not None:
            # Stash original AI-generated images so delete can restore them
            if '_original_images' not in best_chapter:
                best_chapter['_original_images'] = best_chapter.get('images', [])
            existing_images = list(best_chapter.get('images', []))
            existing_slice_ids = []
            for slice_id_value in best_chapter.get('_slice_ids') or []:
                _append_unique(existing_slice_ids, slice_id_value)
            _append_unique(existing_slice_ids, best_chapter.get('_slice_id'))
            for image in existing_images:
                _append_unique(existing_slice_ids, _slice_id_from_image_path(image))
            if replace_image_path:
                if replace_image_path not in existing_images:
                    raise ValueError("Image being replaced is no longer attached to this chapter")
                next_images = []
                for image in existing_images:
                    if image == replace_image_path:
                        next_images.extend(image_paths)
                    else:
                        next_images.append(image)
                best_chapter['images'] = next_images
                _append_unique(existing_slice_ids, slice_id)
                best_chapter['_slice_ids'] = existing_slice_ids
                best_chapter['_slice_id'] = slice_id
            else:
                # Replace existing images with operator-curated ones
                best_chapter['images'] = image_paths
                _append_unique(existing_slice_ids, slice_id)
                best_chapter['_slice_ids'] = existing_slice_ids
                best_chapter['_slice_id'] = slice_id  # legacy single-owner field

            with open(archive_path, 'w') as f:
                json.dump(archive, f)

    return {
        "id": slice_id,
        "path": f"slices/{slice_id}",
        "manifest": manifest,
        "images_added": len(image_paths),
        "chapter_index": chapter_index,
        "replaced_image_path": replace_image_path,
    }

def list_slices(job_id: str, job_store: JobStore):
    """
    Lists all saved slices for a job.
    """
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
                except (OSError, json.JSONDecodeError):
                    logger.warning("Skipping unreadable slice manifest: %s", manifest_path)
    return slices
