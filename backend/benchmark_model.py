#!/usr/bin/env python3
"""
Benchmark the Smart YouTube Reader archive model and image selector.

Usage:
    python3 backend/benchmark_model.py
    python3 backend/benchmark_model.py data/jobs/<project-folder>
    python3 backend/benchmark_model.py data/jobs/<project-folder> --runs 2
"""

from __future__ import annotations

import argparse
import json
import re
import signal
import statistics
import sys
import time
from pathlib import Path

import ollama

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPO_ROOT = ROOT.parent

from app.frames import FrameManager
from app.intelligence import (
    _choose_representative_frames,
    _extract_json_list,
    _format_transcript_chunk,
)

MODEL = "smart-reader:latest"
REQUIRED_KEYS = {"title", "summary", "content", "start_time", "end_time"}
FLUFF_RE = re.compile(
    r"\b(insane|secret|ultimate|never|always|guaranteed|massive|crazy|best|shocking|profits?|millionaire)\b",
    re.I,
)

SYSTEM_PROMPT = (
    "You are a Smart YouTube Reader archive planner. Convert timestamped transcript evidence into "
    "compact AI-learning chapters.\n"
    "Return ONLY a raw JSON array. No markdown, no prose.\n"
    "Each object must contain exactly: title, summary, content, start_time, end_time.\n"
    "Use numeric seconds for timestamps. Derive them from the bracketed transcript ranges.\n"
    "Create 3-5 chapters for a 5-minute segment when the segment contains enough substance. Merge tiny transitions into nearby chapters.\n"
    "Do not create standalone chapters for intros, sponsor chatter, calls to action, jokes, or repetition.\n"
    "Preserve durable concepts, definitions, procedures, examples, caveats, and references to visible charts, slides, or tools.\n"
    "The content field must use transcript wording from the provided segment, ordered chronologically. "
    "Keep the teaching evidence dense; target 400-900 characters per chapter when possible. "
    "Do not invent facts or add outside knowledge.\n"
    "Keep titles no-fluff: specific lesson names, no hype, no YouTube-style phrasing."
)

SAMPLE_TRANSCRIPT = [
    {"start": 0.0, "duration": 12.0, "text": "The YouTube algorithm is not a spreadsheet of CTR and retention anymore."},
    {"start": 12.0, "duration": 16.0, "text": "The platform predicts viewer satisfaction and matches content to viewers instead of simply pushing videos."},
    {"start": 28.0, "duration": 20.0, "text": "Every video has a semantic fingerprint that captures topic, tone, pacing, emotional arc, and likely viewer behavior."},
    {"start": 48.0, "duration": 20.0, "text": "Two videos with different titles can have similar semantic IDs, which is why channels are less important than matching the viewer's current demand."},
    {"start": 68.0, "duration": 22.0, "text": "Videos expand when demand spikes, timing windows, external traffic, and session resonance make the fingerprint useful."},
    {"start": 90.0, "duration": 18.0, "text": "Session resonance means the video keeps a viewer on YouTube longer than the next best recommendation would have."},
]


class Timeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise Timeout("timed out")


def load_transcript(path: str | None) -> tuple[list[dict], Path | None]:
    if not path:
        return SAMPLE_TRANSCRIPT, None

    job_dir = Path(path)
    if not job_dir.exists():
        job_dir = REPO_ROOT / "data" / "jobs" / path
    transcript_path = job_dir / "transcript.json"
    if not transcript_path.exists():
        raise FileNotFoundError(f"transcript.json not found: {transcript_path}")
    return json.loads(transcript_path.read_text()), job_dir


def source_words(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z]{4,}", text.lower()))


def score_archive_response(raw: str, transcript_text: str, window_start: float, window_end: float) -> dict:
    result = {
        "valid_json": False,
        "chapters": 0,
        "keys_ok": False,
        "timestamps_ok": False,
        "count_ok": False,
        "no_markdown": "```" not in raw,
        "no_fluff_titles": False,
        "content_grounded": False,
        "avg_content_chars": 0,
        "coverage_chars": 0,
        "quality": 0,
        "titles": [],
        "error": "",
    }
    try:
        chapters = _extract_json_list(raw)
    except Exception as exc:
        result["error"] = str(exc)
        return result

    words = source_words(transcript_text)
    result["valid_json"] = True
    result["chapters"] = len(chapters)
    result["count_ok"] = 2 <= len(chapters) <= 5
    result["keys_ok"] = all(isinstance(chapter, dict) and REQUIRED_KEYS <= set(chapter.keys()) for chapter in chapters)

    timestamp_checks = []
    grounded_scores = []
    coverage = 0
    titles = []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        title = str(chapter.get("title", ""))
        titles.append(title)
        start = chapter.get("start_time")
        end = chapter.get("end_time")
        timestamp_checks.append(
            isinstance(start, (int, float))
            and isinstance(end, (int, float))
            and window_start <= start < end <= window_end + 20
        )
        content = str(chapter.get("content", ""))
        coverage += len(content)
        content_words = re.findall(r"[a-zA-Z]{4,}", content.lower())
        if content_words:
            grounded_scores.append(sum(1 for word in content_words if word in words) / len(content_words))

    result["titles"] = titles
    result["timestamps_ok"] = bool(timestamp_checks) and all(timestamp_checks)
    result["no_fluff_titles"] = bool(titles) and all(not FLUFF_RE.search(title) for title in titles)
    result["avg_content_chars"] = round(coverage / max(len(chapters), 1))
    result["coverage_chars"] = coverage
    min_content_chars = min(250, max(120, len(transcript_text) // max(len(chapters), 1) // 2))
    result["content_grounded"] = (
        bool(grounded_scores)
        and statistics.mean(grounded_scores) >= 0.84
        and result["avg_content_chars"] >= min_content_chars
    )

    gates = [
        "valid_json",
        "keys_ok",
        "timestamps_ok",
        "count_ok",
        "no_markdown",
        "no_fluff_titles",
        "content_grounded",
    ]
    result["quality"] = sum(1 for gate in gates if result[gate])
    return result


def benchmark_text(transcript: list[dict], runs: int, timeout: int) -> list[dict]:
    chunk = [item for item in transcript if 0 <= float(item.get("start", 0)) < 300]
    if not chunk:
        chunk = transcript[:60]
    chunk_text = _format_transcript_chunk(chunk)
    user_prompt = f"Transcript segment 0.0-300.0s:\n{chunk_text}"

    results = []
    signal.signal(signal.SIGALRM, _timeout_handler)
    for run in range(1, runs + 1):
        start = time.time()
        signal.alarm(timeout)
        try:
            response = ollama.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            signal.alarm(0)
            raw = response["message"]["content"]
            results.append({
                "run": run,
                "seconds": round(time.time() - start, 1),
                "raw_chars": len(raw),
                **score_archive_response(raw, chunk_text, 0.0, 300.0),
            })
        except Exception as exc:
            signal.alarm(0)
            results.append({"run": run, "seconds": round(time.time() - start, 1), "error": str(exc), "quality": 0})
    return results


def benchmark_images(job_dir: Path | None) -> list[dict]:
    if not job_dir:
        return []
    archive_path = job_dir / "archive.json"
    frames_path = job_dir / "frames.json"
    if not archive_path.exists() or not frames_path.exists():
        return []

    frame_manager = FrameManager(job_dir)
    frame_manager.scan_and_hash(interval_sec=15)
    all_frames = frame_manager.get_context_frames(0, float("inf"))
    archive = json.loads(archive_path.read_text())
    rows = []
    used: set[str] = set()
    for index, chapter in enumerate((archive.get("archive") or [])[:8]):
        start = float(chapter.get("timestamp_start", 0))
        end = float(chapter.get("timestamp_end", start + 60))
        candidates = frame_manager.get_context_frames(max(0, start - 20), end + 20)
        selected = _choose_representative_frames(candidates, all_frames, start, end, used)
        selected_meta = [frame for frame in candidates if frame.get("filename") in selected]
        avg_score = 0
        if selected_meta:
            avg_score = sum(float(frame.get("visual_score", 0)) for frame in selected_meta) / len(selected_meta)
        rows.append({
            "chapter": index + 1,
            "selected": selected,
            "candidate_count": len(candidates),
            "avg_visual_score": round(avg_score, 3),
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("job", nargs="?", help="Optional data/jobs project folder or folder name")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    transcript, job_dir = load_transcript(args.job)
    print(f"Model: {MODEL}")
    print(f"Transcript items: {len(transcript)}")
    if job_dir:
        print(f"Project: {job_dir}")

    print("\nText archive benchmark")
    text_results = benchmark_text(transcript, args.runs, args.timeout)
    for result in text_results:
        print(json.dumps(result, indent=2))

    image_results = benchmark_images(job_dir)
    if image_results:
        print("\nImage selection benchmark")
        for result in image_results:
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
