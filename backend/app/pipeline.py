import os
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

def run_pipeline(job_id: str, payload: JobCreateRequest, job_store: JobStore):
    job = job_store.get(job_id)
    job.status = JobStatus.processing
    job.current_step = "Initializing..."
    
    # Create job directory
    job_dir = DATA_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = job_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    job.data_dir = job_dir
    
    try:
        # 1. Download Video Info & Audio
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(job_dir / 'video.%(ext)s'),
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(payload.video_url, download=True)
            video_path = str(job_dir / f"video.{info['ext']}")
            video_id = info['id']
            job.title = info.get('title', 'Unknown Video')

        # 2. Get Transcript (via yt-dlp to be robust)
        job.current_step = "Extracting Transcript..."
        ydl_opts_subs = {
            'skip_download': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'outtmpl': str(job_dir / 'subs'),
            'quiet': True,
        }
        
        transcript = []
        try:
             from youtube_transcript_api import YouTubeTranscriptApi
             transcript = YouTubeTranscriptApi.get_transcript(video_id)
             
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
                     import re
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
        try:
             from .intelligence import create_ai_archive
             # Pass frame_manager instead of frames_dir
             archive_result = create_ai_archive(job_id, transcript, frame_manager)
             
             if archive_result.get('archive'):
                 with open(job_dir / "archive.json", "w") as f:
                     json.dump(archive_result, f)
                 archive_stats = len(archive_result['archive'])
                 print(f"Generated AI Archive with {archive_stats} chapters.")
             
        except Exception as e:
            print(f"Archive generation failed: {e}")
        
        # 6. Package
        manifest = {
            "job_id": job_id,
            "url": payload.video_url,
            "title": job.title,
            "created_at": job.created_at,
            "removed_duplicates": removed,
            "archive_chapters": archive_stats,
            "status": "complete"
        }
        with open(job_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)
            
        job.package_path = job_dir
        job.package_path = job_dir
        job.status = JobStatus.complete
        job.current_step = "Complete"
        
        # 7. Rename Directory to readable slug
        try:
           from .jobs import slugify
           slug = slugify(job.title)
           short_id = job_id[:8]
           new_dir_name = f"{slug}_{short_id}"
           new_job_dir = DATA_ROOT / new_dir_name
           
           if not new_job_dir.exists():
               import shutil
               # We need to be careful with rename if open handles exist (though usually python handles are closed)
               # Renaming the directory invalidates frame_manager paths if we don't update it.
               # But job is done, so it's fine.
               
               job_dir.rename(new_job_dir)
               job.data_dir = new_job_dir
               job.package_path = new_job_dir
               print(f"Renamed job directory to: {new_job_dir}")
        except Exception as e:
            print(f"Could not rename directory: {e}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        job.status = JobStatus.failed
        job.error = str(e)

