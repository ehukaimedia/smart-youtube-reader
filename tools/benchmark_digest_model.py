#!/usr/bin/env python3
"""Benchmark the local Ollama AI digest model against Smart YouTube Reader archives."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.digest import (
    DIGEST_SYSTEM_PROMPT,
    build_digest_user_prompt,
    _normalize_agent_chapter,
    _validate_digest_quality,
)

DATA_ROOT = ROOT / "data" / "jobs"
MODELFILE = ROOT / "backend" / "modelfiles" / "smart-youtube-digest.Modelfile"
DEFAULT_MODEL = "smart-youtube-digest"
DEFAULT_ARCHIVES = [
    "how-to-master-volume-profile-trading-in-less-than-15-minutes-and-never-guess-market-direction-again_e68163e9",
    "introduction-to-volume-profiles-on-tradingview-tutorial_cb887f63",
]

def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the local Ollama AI digest Modelfile.")
    parser.add_argument("archives", nargs="*", help="Job folder names or paths to archive.json files")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--runs", type=int, default=1, help="Runs per archive (default: 1)")
    parser.add_argument("--build", action="store_true", help="Run ollama create before benchmarking")
    parser.add_argument("--ollama-host", default="http://127.0.0.1:11434", help="Ollama host URL")
    args = parser.parse_args()

    if args.build:
        build_model(args.model)

    archives = resolve_archives(args.archives or DEFAULT_ARCHIVES)
    if not archives:
        print("No benchmark archives found.", file=sys.stderr)
        return 2

    failures = 0
    for archive_path in archives:
        source = json.loads(archive_path.read_text(encoding="utf-8"))
        source_chapters = source.get("archive", [])
        if not source_chapters:
            print(f"\n{archive_path}: no source chapters")
            failures += 1
            continue

        print(f"\n{archive_path.relative_to(ROOT)}")
        print(f"source chapters: {len(source_chapters)}  source images: {count_source_images(source_chapters)}")

        for run_index in range(args.runs):
            started = time.time()
            raw = call_ollama(args.ollama_host, args.model, build_digest_user_prompt(source_chapters))
            elapsed = time.time() - started
            result = score_digest(raw, source_chapters, archive_path.parent)
            status = "PASS" if result["passed"] else "FAIL"
            print(
                f"  run {run_index + 1}: {status} "
                f"chapters={result['chapter_count']} "
                f"compression={result['compression']:.2f} "
                f"images={result['preserved_images']}/{result['expected_images']} "
                f"time={elapsed:.1f}s"
            )
            if result["errors"]:
                for error in result["errors"]:
                    print(f"    - {error}")
                failures += 1

    if failures:
        print(f"\nFAILED quality gates: {failures}")
        return 1

    print("\nAll local digest quality gates passed.")
    return 0


def build_model(model: str) -> None:
    subprocess.run(
        ["ollama", "create", model, "-f", str(MODELFILE)],
        cwd=ROOT,
        check=True,
    )


def resolve_archives(values: list[str]) -> list[Path]:
    archives = []
    for value in values:
        path = Path(value)
        if path.is_file():
            archives.append(path.resolve())
            continue

        folder = DATA_ROOT / value
        archive = folder / "archive.json"
        if archive.exists():
            archives.append(archive.resolve())
            continue

        matches = list(DATA_ROOT.glob(f"*{value}*/archive.json"))
        archives.extend(match.resolve() for match in matches)

    seen = set()
    unique = []
    for archive in archives:
        if archive not in seen:
            unique.append(archive)
            seen.add(archive)
    return unique


def call_ollama(host: str, model: str, prompt: str) -> str:
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.05,
            "num_ctx": 16384,
        },
    }).encode("utf-8")
    request = urllib.request.Request(
        host.rstrip("/") + "/api/chat",
        data=body,
        method="POST",
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return str(payload.get("message", {}).get("content") or "")


def score_digest(raw: str, source_chapters: list[dict[str, Any]], source_dir: Path) -> dict[str, Any]:
    errors = []
    parsed = extract_json(raw)
    if not isinstance(parsed, dict):
        return failed("output is not a JSON object")

    title = str(parsed.get("title") or "").strip()
    chapters = parsed.get("chapters")
    changes = parsed.get("changes_summary")

    if not title:
        errors.append("missing title")
    if has_hype(title):
        errors.append(f"title has hype wording: {title}")
    if title.lower() in {str(chapter.get("concept", "")).lower() for chapter in source_chapters[:1]}:
        errors.append("title appears to reuse the source headline or first chapter title")
    if not isinstance(chapters, list) or not chapters:
        errors.append("chapters must be a non-empty list")
        chapters = []
    if not isinstance(changes, list) or not changes:
        errors.append("changes_summary must be a non-empty list")

    source_count = len(source_chapters)
    chapter_count = len(chapters)
    compression = chapter_count / source_count if source_count else 1
    if source_count > 3 and chapter_count >= source_count:
        errors.append("digest did not reduce chapter count")

    valid_indices = set(range(source_count))
    used_indices = []
    content_lengths = []
    normalized_chapters = []
    for index, chapter in enumerate(chapters):
        indices = chapter.get("source_indices")
        if not isinstance(indices, list) or not indices:
            errors.append(f"chapter {index} missing source_indices")
            indices = []
        bad_indices = [item for item in indices if not isinstance(item, int) or item not in valid_indices]
        if bad_indices:
            errors.append(f"chapter {index} has invalid source_indices: {bad_indices}")
        used_indices.extend(item for item in indices if isinstance(item, int) and item in valid_indices)

        start = chapter.get("timestamp_start")
        end = chapter.get("timestamp_end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            errors.append(f"chapter {index} timestamps must be numeric")
        elif end < start:
            errors.append(f"chapter {index} timestamp_end precedes timestamp_start")

        content = str(chapter.get("content") or "")
        content_lengths.append(len(content))
        if len(content) < 120:
            errors.append(f"chapter {index} content too short for teaching context")

        if isinstance(chapter, dict):
            try:
                normalized = _normalize_agent_chapter(source_dir, source_chapters, chapter, strict=True)
                if normalized:
                    normalized_chapters.append(normalized)
            except RuntimeError as exc:
                errors.append(f"chapter {index} production normalization failed: {exc}")

    avg_content_len = sum(content_lengths) / len(content_lengths) if content_lengths else 0
    if avg_content_len < 240:
        errors.append("average chapter content is too thin")

    if normalized_chapters:
        try:
            _validate_digest_quality(normalized_chapters, source_chapters)
        except RuntimeError as exc:
            errors.append(f"production quality validation failed: {exc}")

    expected_images = count_source_images([source_chapters[index] for index in sorted(set(used_indices))])
    preserved_images = count_source_images(normalized_chapters)
    if preserved_images != expected_images:
        errors.append(f"preserved image count mismatch: expected {expected_images}, got {preserved_images}")

    return {
        "passed": not errors,
        "errors": errors,
        "chapter_count": chapter_count,
        "compression": compression,
        "expected_images": expected_images,
        "preserved_images": preserved_images,
    }


def extract_json(raw: str) -> Any:
    cleaned = raw.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(cleaned[start:end])
    except json.JSONDecodeError:
        return None


def failed(message: str) -> dict[str, Any]:
    return {
        "passed": False,
        "errors": [message],
        "chapter_count": 0,
        "compression": 1,
        "expected_images": 0,
        "preserved_images": 0,
    }


def count_source_images(chapters: list[dict[str, Any]]) -> int:
    images = set()
    for chapter in chapters:
        for image in chapter.get("images", []) or []:
            images.add(image)
    return len(images)


def has_hype(title: str) -> bool:
    return bool(re.search(r"\b(ultimate|insane|secret|shocking|must watch|you won't believe|complete guide|actually works)\b", title, re.I))


if __name__ == "__main__":
    raise SystemExit(main())
