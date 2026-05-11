import os
import traceback
import yt_dlp
import ffmpeg
import json
import re
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from .jobs import JobStore, JobStatus
# from .intelligence import deduplicate_frames REMOVED
from .frames import FrameManager # [NEW]
from .schemas import JobCreateRequest

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "jobs"

def _ensure_js_runtime_in_path():
    """Prepend known JS runtime bin dirs to PATH so yt-dlp can solve YouTube's n-challenge.
    The uvicorn worker process may not inherit the user's full shell PATH."""
    candidates = [
        Path.home() / '.volta' / 'bin',
        Path('/usr/local/bin'),
        Path('/opt/homebrew/bin'),
    ]
    # nvm: resolve the active version from ~/.nvm/alias/default
    nvm_default = Path.home() / '.nvm' / 'alias' / 'default'
    if nvm_default.exists():
        version = nvm_default.read_text().strip()
        candidates.insert(0, Path.home() / '.nvm' / 'versions' / 'node' / version / 'bin')

    for bin_dir in candidates:
        if bin_dir.exists() and str(bin_dir) not in os.environ.get('PATH', ''):
            os.environ['PATH'] = str(bin_dir) + ':' + os.environ['PATH']

def run_pipeline(job_id: str, payload: JobCreateRequest, job_store: JobStore):
    _ensure_js_runtime_in_path()

    job = job_store.get(job_id)
    job.status = JobStatus.processing
    job.current_step = "Initializing..."

    # Create job directory
    job_dir = DATA_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = job_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    job.data_dir = job_dir

    # Read cookies browser from env — keeps this portable across machines.
    # Set YDL_COOKIES_BROWSER=chrome (or firefox) locally if needed for private videos.
    _cookies_browser = os.environ.get('YDL_COOKIES_BROWSER')

    try:
        # 1. Download Video Info & Audio
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(job_dir / 'video.%(ext)s'),
            'quiet': True,
            'js_runtimes': {'node': {}},  # explicit opt-in; yt-dlp 2026+ defaults to deno only
        }
        if _cookies_browser:
            ydl_opts['cookiesfrombrowser'] = (_cookies_browser,)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(payload.video_url, download=True)
            video_path = str(job_dir / f"video.{info['ext']}")
            video_id = info['id']
            job.title = info.get('title', 'Unknown Video')
            job.video_ext = info['ext']

        # 2. Get Transcript (via yt-dlp to be robust)
        job.current_step = "Extracting Transcript..."
        ydl_opts_subs = {
            'skip_download': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'outtmpl': str(job_dir / 'subs'),
            'quiet': True,
            'js_runtimes': {'node': {}},  # explicit opt-in; yt-dlp 2026+ defaults to deno only
        }

        transcript = []
        try:
             fetched = YouTubeTranscriptApi().fetch(video_id)
             transcript = [{'text': s.text, 'start': s.start, 'duration': s.duration} for s in fetched]

             with open(job_dir / "transcript.json", "w") as f:
                json.dump(transcript, f)

             preview_text = " ".join([t['text'] for t in transcript[:5]]) + "..."
             job.transcript_preview = preview_text

        except Exception as e:
             print(f"Transcript API failed: {e}. Trying yt-dlp subs...")
             try:
                 with yt_dlp.YoutubeDL(ydl_opts_subs) as ydl:
                     ydl.download([payload.video_url])

                 vtt_path = job_dir / "subs.en.vtt"
                 if not vtt_path.exists():
                     found = list(job_dir.glob("subs.*.vtt"))
                     if found:
                         vtt_path = found[0]

                 if vtt_path.exists():
                     with open(vtt_path, 'r', encoding='utf-8') as f:
                         content = f.read()

                     pattern = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3}).*?\n(.*?)(?=\n\n|\Z)', re.DOTALL)
                     matches = pattern.findall(content)

                     def timestamp_to_seconds(ts):
                         h, m, s = ts.split(':')
                         return int(h) * 3600 + int(m) * 60 + float(s)

                     parsed_transcript = []
                     for start, end, text in matches:
                         clean_text = re.sub(r'<[^>]+>', '', text).strip().replace('\n', ' ')
                         if not clean_text:
                             continue

                         if parsed_transcript and parsed_transcript[-1]['text'] == clean_text:
                             continue

                         parsed_transcript.append({
                             'text': clean_text,
                             'start': timestamp_to_seconds(start),
                             'duration': timestamp_to_seconds(end) - timestamp_to_seconds(start)
                         })

                     transcript = parsed_transcript
                     if not transcript:
                         raise RuntimeError("Parsed VTT but got empty transcript")

                     with open(job_dir / "transcript.json", "w") as f:
                        json.dump(transcript, f)
                 else:
                     raise RuntimeError("No subtitles downloaded by yt-dlp")

             except Exception as inner_e:
                 job.error = f"Transcript failed (API & yt-dlp): {str(e)} | {str(inner_e)}"
                 raise inner_e

        # 3. Extract Frames
        try:
            (
                ffmpeg
                .input(video_path)
                .filter('fps', fps=1/payload.interval_sec)
                .filter('scale', w=payload.min_width, h=-1)
                .output(str(frames_dir / '%04d.png'))
                .run(quiet=True, overwrite_output=True)
            )
        except ffmpeg.Error as e:
            raise RuntimeError(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")

        # 4. Smart Deduplication (Using FrameManager)
        job.current_step = "Indexing & Deduplicating Frames..."

        # Initialize FrameManager
        frame_manager = FrameManager(job_dir)

        # Scan and Hash (Compute Once)
        new_hashed = frame_manager.scan_and_hash(interval_sec=payload.interval_sec)
        print(f"Hashed {new_hashed} new frames.")

        # Deduplicate
        removed = frame_manager.deduplicate(threshold=5)
        print(f"Removed {removed} duplicate frames.")

        # 5. Create AI Archive (Intelligence Step)
        job.current_step = "Generating AI Archive (Thinking)..."
        archive_stats = 0
        archive_result = None
        try:
             from .intelligence import create_ai_archive
             # Pass frame_manager instead of frames_dir
             archive_result = create_ai_archive(job_id, transcript, frame_manager, model=payload.model)

             if archive_result.get('archive'):
                 archive_stats = len(archive_result['archive'])
                 print(f"Generated AI Archive with {archive_stats} chapters.")
             # archive.json is written after rename below, once the final folder name is known

        except Exception as e:
            traceback.print_exc()
            print(f"Archive generation failed: {e}")

        # 6. Rename Directory to readable slug (must happen before writing archive.json)
        try:
           from .jobs import slugify
           slug = slugify(job.title)
           short_id = job_id[:8]
           new_dir_name = f"{slug}_{short_id}"
           new_job_dir = DATA_ROOT / new_dir_name

           if not new_job_dir.exists():
               job_dir.rename(new_job_dir)
               job.data_dir = new_job_dir
               job.package_path = new_job_dir
               job_dir = new_job_dir
               print(f"Renamed job directory to: {new_job_dir}")
        except Exception as e:
            print(f"Could not rename directory: {e}")

        # 7. Write archive.json now that final folder name is known
        # Images stored as relative paths (frames/<filename>) so they work regardless of host/port
        if archive_result and archive_result.get('archive'):
            final_folder = job_dir.name
            for chapter in archive_result['archive']:
                image_context = chapter.get('_image_context') or {}
                chapter['images'] = [
                    f"frames/{img}" for img in chapter.get('images', [])
                ]
                if image_context:
                    chapter['_image_context'] = {
                        f"frames/{image_path}": metadata
                        for image_path, metadata in image_context.items()
                    }
            archive_result['folder'] = final_folder
            with open(job_dir / "archive.json", "w") as f:
                json.dump(archive_result, f)

        # 8. Package manifest
        manifest = {
            "job_id": job_id,
            "url": payload.video_url,
            "title": job.title,
            "created_at": job.created_at,
            "removed_duplicates": removed,
            "archive_chapters": archive_stats,
            "status": "complete",
            "video_ext": job.video_ext or "mp4"
        }
        with open(job_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        job.package_path = job_dir
        job.status = JobStatus.complete
        job.current_step = "Complete"

    except Exception as e:
        traceback.print_exc()
        job.status = JobStatus.failed
        job.error = str(e)
