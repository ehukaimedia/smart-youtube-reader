#!/usr/bin/env python3
"""Benchmark the local Ollama model on the text-only AI digest task.

Sends the explicit text-only CLI digest prompt to Ollama and reports latency,
whether the output is valid JSON in
the expected shape, and a per-chapter summary. The default production digest
workflow uses an external agent with generated WebP images.

Usage:
    backend/.venv/bin/python backend/benchmarks/digest_prompt.py \
        data/jobs/<source-project-folder>

The project path can be relative to the repo root or absolute.
The benchmark result is written to <project>/generated/gemma4-digest-benchmark.json.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.model_runtime import chat as model_chat, DEFAULT_MODEL


def get_prompt(project_folder: str) -> str:
    result = subprocess.run(
        ["python3", str(REPO / "tools" / "create_ai_digest_version.py"), project_folder, "--text-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def strip_fences(text: str) -> str:
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    return fence.group(1).strip() if fence else text.strip()


def validate_shape(obj: dict) -> list[str]:
    issues = []
    if not isinstance(obj, dict):
        return ["root is not an object"]
    for key in ("title", "chapters", "changes_summary"):
        if key not in obj:
            issues.append(f"missing top-level key: {key}")
    chapters = obj.get("chapters") or []
    if not isinstance(chapters, list) or not chapters:
        issues.append("chapters is empty or not a list")
        return issues
    required = {"source_indices", "concept", "summary", "content", "timestamp_start", "timestamp_end"}
    for i, ch in enumerate(chapters):
        if not isinstance(ch, dict):
            issues.append(f"chapter[{i}] not an object")
            continue
        missing = required - set(ch.keys())
        if missing:
            issues.append(f"chapter[{i}] missing fields: {sorted(missing)}")
        si = ch.get("source_indices")
        if not isinstance(si, list) or not all(isinstance(x, int) for x in si):
            issues.append(f"chapter[{i}].source_indices not int list: {si!r}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=8000)
    args = parser.parse_args()

    prompt = get_prompt(args.project)
    user_msg = (
        "You are the digest agent. Return JSON only, no commentary, no markdown fences.\n\n"
        + prompt
    )

    t0 = time.time()
    output = model_chat(
        model=args.model,
        messages=[{"role": "user", "content": user_msg}],
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    elapsed = time.time() - t0

    raw = strip_fences(output)
    try:
        parsed = json.loads(raw)
        parse_ok = True
        parse_err = None
    except Exception as e:
        parsed = None
        parse_ok = False
        parse_err = str(e)

    issues = validate_shape(parsed) if parse_ok else ["could not parse JSON"]

    print(f"model        : {args.model}")
    print(f"elapsed      : {elapsed:.1f}s")
    print(f"output_chars : {len(output)}")
    print(f"parse_ok     : {parse_ok}")
    if parse_err:
        print(f"parse_err    : {parse_err[:200]}")
    print(f"shape_issues : {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")
    if parse_ok and parsed:
        chapters = parsed.get("chapters") or []
        print(f"title        : {parsed.get('title', '')!r}")
        print(f"chapters     : {len(chapters)}")
        for i, ch in enumerate(chapters):
            si = ch.get("source_indices", [])
            concept = ch.get("concept", "")
            print(f"  [{i}] src={si} concept={concept!r}")

    project_path = Path(args.project)
    if not project_path.is_absolute():
        project_path = REPO / project_path
    out_path = project_path / "generated" / "gemma4-digest-benchmark.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "model": args.model,
        "elapsed_seconds": elapsed,
        "output_chars": len(output),
        "parse_ok": parse_ok,
        "parse_error": parse_err,
        "shape_issues": issues,
        "raw_output": output,
        "parsed": parsed,
    }, indent=2))
    print(f"\nbenchmark saved: {out_path}")
    return 0 if parse_ok and not issues else 1


if __name__ == "__main__":
    sys.exit(main())
