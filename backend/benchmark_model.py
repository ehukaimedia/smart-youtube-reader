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

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPO_ROOT = ROOT.parent

from app.frames import FrameManager
from app.intelligence import (
    CHUNK_DURATION,
    _archive_system_prompt,
    _choose_representative_frames,
    _extract_archive_chapters,
    _transcript_prompt_chunks,
)
from app.mlx_runtime import DEFAULT_MODEL, chat as mlx_chat

MODEL = DEFAULT_MODEL
REQUIRED_KEYS = {"title", "summary", "content", "start_time", "end_time"}
FLUFF_RE = re.compile(
    r"\b(insane|secret|ultimate|never|always|guaranteed|massive|crazy|best|shocking|profits?|millionaire)\b",
    re.I,
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


def score_archive_response(raw: str, transcript_text: str, window_start: float, window_end: float, response_format: str) -> dict:
    result = {
        "format": response_format,
        "valid_format": False,
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
        chapters = _extract_archive_chapters(raw, response_format)
    except Exception as exc:
        result["error"] = str(exc)
        return result

    words = source_words(transcript_text)
    result["valid_format"] = True
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
        "valid_format",
        "keys_ok",
        "timestamps_ok",
        "count_ok",
        "no_markdown",
        "no_fluff_titles",
        "content_grounded",
    ]
    result["quality"] = sum(1 for gate in gates if result[gate])
    return result


def transcript_chunks(transcript: list[dict], chunk_duration: int = CHUNK_DURATION) -> list[dict]:
    chunks = _transcript_prompt_chunks(transcript, chunk_duration=chunk_duration)
    for index, chunk in enumerate(chunks, start=1):
        chunk["index"] = index
    return chunks


def benchmark_text(
    transcript: list[dict],
    runs: int,
    timeout: int,
    full: bool = True,
    formats: list[str] | None = None,
    max_tokens: int = 2048,
) -> list[dict]:
    chunks = transcript_chunks(transcript)
    if not chunks:
        chunks = [{"index": 1, "start": 0.0, "end": 300.0, "items": transcript[:60]}]
    if not full:
        chunks = chunks[:1]

    results = []
    formats = formats or ["xml", "json"]
    signal.signal(signal.SIGALRM, _timeout_handler)
    for run in range(1, runs + 1):
        for chunk in chunks:
            for response_format in formats:
                chunk_text = chunk["text"]
                user_prompt = f"Transcript segment {chunk['start']:.1f}-{chunk['end']:.1f}s:\n{chunk_text}"
                start = time.time()
                signal.alarm(timeout)
                try:
                    raw = mlx_chat(
                        model=MODEL,
                        messages=[
                            {"role": "system", "content": _archive_system_prompt(response_format)},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.1,
                        max_tokens=max_tokens,
                    )
                    signal.alarm(0)
                    results.append({
                        "run": run,
                        "chunk": chunk["index"],
                        "window": [round(chunk["start"], 1), round(chunk["end"], 1)],
                        "input_items": len(chunk["items"]),
                        "input_chars": len(chunk_text),
                        "seconds": round(time.time() - start, 1),
                        "raw_chars": len(raw),
                        **score_archive_response(raw, chunk_text, chunk["start"], chunk["end"], response_format),
                    })
                except Exception as exc:
                    signal.alarm(0)
                    results.append({
                        "run": run,
                        "chunk": chunk["index"],
                        "format": response_format,
                        "window": [round(chunk["start"], 1), round(chunk["end"], 1)],
                        "seconds": round(time.time() - start, 1),
                        "error": str(exc),
                        "quality": 0,
                    })
    return results


def summarize_text_results(results: list[dict]) -> dict:
    if not results:
        return {"chunks": 0, "passed": 0, "pass_rate": 0.0}
    passed = [result for result in results if result.get("quality") == 7]
    qualities = [int(result.get("quality", 0)) for result in results]
    return {
        "chunks": len(results),
        "passed": len(passed),
        "pass_rate": round(len(passed) / len(results), 3),
        "min_quality": min(qualities),
        "avg_quality": round(statistics.mean(qualities), 2),
        "total_seconds": round(sum(float(result.get("seconds", 0)) for result in results), 1),
    }


def summarize_by_format(results: list[dict]) -> dict:
    summary = {}
    for response_format in sorted({str(result.get("format", "unknown")) for result in results}):
        rows = [result for result in results if result.get("format") == response_format]
        summary[response_format] = summarize_text_results(rows)
    return summary


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
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["xml", "json"],
        default=["xml", "json"],
        help="Response formats to benchmark. Default compares XML and JSON.",
    )
    parser.add_argument(
        "--first-chunk-only",
        action="store_true",
        help="Benchmark only the first transcript chunk. By default, every transcript chunk is tested.",
    )
    args = parser.parse_args()

    transcript, job_dir = load_transcript(args.job)
    print(f"Model: {MODEL}")
    print(f"Transcript items: {len(transcript)}")
    if job_dir:
        print(f"Project: {job_dir}")

    print("\nText archive benchmark")
    text_results = benchmark_text(
        transcript,
        args.runs,
        args.timeout,
        full=not args.first_chunk_only,
        formats=args.formats,
        max_tokens=args.max_tokens,
    )
    for result in text_results:
        print(json.dumps(result, indent=2))
    print("Text benchmark summary")
    print(json.dumps(summarize_text_results(text_results), indent=2))
    print("Text benchmark summary by format")
    print(json.dumps(summarize_by_format(text_results), indent=2))

    image_results = benchmark_images(job_dir)
    if image_results:
        print("\nImage selection benchmark")
        for result in image_results:
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
