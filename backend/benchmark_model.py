#!/usr/bin/env python3
"""
Benchmark smart-reader:latest vs gemma4:latest on archive generation quality.

Usage:
    python benchmark_model.py                          # uses bundled sample transcript
    python benchmark_model.py <job_data_folder_name>   # uses a real job's transcript
    python benchmark_model.py --runs 3                 # number of runs per model (default 1)

Scores each run on:
  - valid_json:       output parses as JSON list
  - chapter_count:    number of chapters produced
  - timestamp_type:   all timestamps are numbers (not strings)
  - verbatim_content: content fields are long (>100 chars), suggesting verbatim not paraphrased
  - no_markdown:      no ``` code fences in output
"""

import json
import time
import sys
import os
import argparse
from pathlib import Path

import ollama

SYSTEM_PROMPT = (
    "You are an expert AI Data Archivist. Your goal is to convert the following video transcript segment "
    "into a structured dataset for machine learning.\n"
    "Action: Break the content into logical 'Concepts' or 'Chapters'.\n"
    "Output Format: JSON list of objects, each with:\n"
    " - 'title': Short concept title\n"
    " - 'summary': One sentence summary\n"
    " - 'content': The full text content for this section\n"
    " - 'start_time': approximate start time in seconds (relative to video start)\n"
    " - 'end_time': approximate end time in seconds\n"
    "IMPORTANT: Focus ONLY on the provided text. Do not hallucinate content outside this segment.\n"
    "CRITICAL: Output ONLY raw JSON. Do not wrap the JSON in markdown formatting or code blocks."
)

SAMPLE_TRANSCRIPT = """
The YouTube algorithm isn't what you think. Most creators chase the wrong numbers.
The system they're trying to beat stopped working that way years ago.
Here's what's actually happening under the surface, and why your best video might fail
while your weirdest one explodes. Everyone is still optimizing for a machine that doesn't exist.
Ask any creator what makes a video succeed and you'll hear the same two answers:
click-through rate and watch time. Get people to click, keep them watching, and repeat.
This idea is everywhere. It sounds right. A decade ago it mostly did.
But the system running YouTube in 2026 is not a spreadsheet of CTR and retention.
It's a recommendation engine closer in spirit to ChatGPT than a ranking formula.
The old mental model said high CTR means pushed to more people.
Long watch time means boosted. More views means more reach. The algorithm promotes videos.
What's actually happening is very different. A viewer gets matched to the content they'll value.
Satisfaction is predicted, not measured. After views are an output, never an input.
The algorithm matches, it never pushes.
Every single video has a semantic ID. Google's research teams have published extensively
on semantic IDs, which are compact numeric fingerprints that represent what a piece of
content is about at multiple levels of detail. Your video gets reduced to a list of numbers.
That list doesn't describe keywords. It describes meaning. The topic, the tone, the pacing,
the emotional arc, the kind of viewer who tends to finish it.
Two videos with completely different titles can have nearly identical semantic fingerprints.
This is why the algorithm can recommend a video to someone who has never watched your channel.
It doesn't need your channel. It needs a fingerprint that matches what the viewer is hungry for.
A video doesn't blow up because it's great. A video blows up because at a specific moment,
the platform has a shortage of exactly what it offers and your fingerprint is the cleanest match.
There are four triggers: demand spikes, timing windows, external traffic, and session resonance.
Session resonance is my favourite: if your video keeps viewers on YouTube longer than
the video they would have watched instead, the system quietly promotes it further.
"""


def load_transcript_from_job(folder_name: str) -> str:
    candidates = [
        Path(f"data/jobs/{folder_name}/transcript.json"),
        Path(f"../data/jobs/{folder_name}/transcript.json"),
    ]
    for p in candidates:
        if p.exists():
            items = json.loads(p.read_text())
            # Take first 5 minutes
            chunk = [t for t in items if t.get("start", 0) < 300]
            return " ".join(t["text"] for t in chunk if "text" in t)
    raise FileNotFoundError(f"transcript.json not found for job {folder_name}")


def score(raw: str) -> dict:
    result = {
        "valid_json": False,
        "chapter_count": 0,
        "timestamp_type_ok": False,
        "verbatim_content": False,
        "no_markdown": "```" not in raw,
        "raw_length": len(raw),
    }
    # Strip markdown fences if present
    cleaned = raw
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start == -1 or end == 0:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        json_str = "[" + cleaned[start:end] + "]" if start != -1 else cleaned
    else:
        json_str = cleaned[start:end]

    try:
        chapters = json.loads(json_str)
        result["valid_json"] = isinstance(chapters, list)
        result["chapter_count"] = len(chapters) if isinstance(chapters, list) else 0

        if isinstance(chapters, list) and chapters:
            ts_ok = all(
                isinstance(c.get("start_time"), (int, float)) and
                isinstance(c.get("end_time"), (int, float))
                for c in chapters
            )
            result["timestamp_type_ok"] = ts_ok
            avg_content_len = sum(len(c.get("content", "")) for c in chapters) / len(chapters)
            result["verbatim_content"] = avg_content_len > 150
    except Exception:
        pass

    return result


def run_model(model: str, transcript: str, use_system: bool = True) -> tuple[str, float]:
    messages = []
    if use_system:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": f"Transcript Segment (0-300s): {transcript}"})

    t0 = time.time()
    resp = ollama.chat(model=model, messages=messages)
    elapsed = time.time() - t0
    return resp["message"]["content"], elapsed


def print_scores(label: str, scores_list: list[dict], times: list[float]):
    print(f"\n{'─'*50}")
    print(f"  {label}")
    print(f"{'─'*50}")
    for i, (s, t) in enumerate(zip(scores_list, times)):
        print(f"  Run {i+1}: valid_json={s['valid_json']}  chapters={s['chapter_count']}  "
              f"ts_ok={s['timestamp_type_ok']}  verbatim={s['verbatim_content']}  "
              f"no_md={s['no_markdown']}  time={t:.1f}s")

    if scores_list:
        avg_chapters = sum(s["chapter_count"] for s in scores_list) / len(scores_list)
        valid_rate = sum(s["valid_json"] for s in scores_list) / len(scores_list)
        ts_rate = sum(s["timestamp_type_ok"] for s in scores_list) / len(scores_list)
        avg_time = sum(times) / len(times)
        print(f"\n  Averages: valid={valid_rate:.0%}  chapters={avg_chapters:.1f}  "
              f"ts_ok={ts_rate:.0%}  time={avg_time:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Benchmark smart-reader vs gemma4")
    parser.add_argument("job_folder", nargs="?", help="Job data folder name")
    parser.add_argument("--runs", type=int, default=1, help="Runs per model (default 1)")
    args = parser.parse_args()

    if args.job_folder:
        print(f"Loading transcript from job: {args.job_folder}")
        transcript = load_transcript_from_job(args.job_folder)
    else:
        print("Using built-in sample transcript (15-minute YouTube algorithm video excerpt)")
        transcript = SAMPLE_TRANSCRIPT.strip()

    print(f"Transcript length: {len(transcript)} chars")
    print(f"Runs per model: {args.runs}\n")

    models = [
        ("smart-reader:latest", True),
        ("gemma4:latest",       False),
    ]

    for model, use_system in models:
        scores_list, times = [], []
        for run in range(args.runs):
            print(f"  [{model}] run {run+1}/{args.runs}...", end=" ", flush=True)
            try:
                raw, elapsed = run_model(model, transcript, use_system)
                s = score(raw)
                scores_list.append(s)
                times.append(elapsed)
                print(f"done ({elapsed:.1f}s)")
            except Exception as e:
                print(f"ERROR: {e}")

        print_scores(model, scores_list, times)

    print(f"\n{'═'*50}")
    print("  Legend:")
    print("    valid_json    — output parsed as JSON list")
    print("    chapters      — number of chapters produced (target: 3-5)")
    print("    ts_ok         — all timestamps are numbers, not strings")
    print("    verbatim      — avg content length >150 chars (not paraphrased)")
    print("    no_md         — no ``` fences in raw output")
    print(f"{'═'*50}\n")


if __name__ == "__main__":
    main()
