#!/usr/bin/env python3
"""Create an AI digest project from an external agent-authored draft."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.digest import (  # noqa: E402
    DIGEST_AGENT_TASK,
    build_digest_user_prompt,
    materialize_digest_project,
    resolve_project,
    _extract_json_object,
    _read_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a Smart YouTube Reader AI digest version from an agent-authored JSON draft."
    )
    parser.add_argument(
        "project",
        help="Source project folder path, data/jobs folder name, or job_id from manifest.json.",
    )
    parser.add_argument(
        "--draft",
        help="Path to the agent-authored digest JSON draft. If omitted, prints the agent task.",
    )
    parser.add_argument(
        "--task-output",
        help="Write the agent task prompt to this path instead of stdout.",
    )
    args = parser.parse_args()

    source_dir = resolve_project(args.project)

    if not args.draft:
        task = build_agent_task(source_dir)
        if args.task_output:
            output_path = Path(args.task_output).expanduser().resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(task, encoding="utf-8")
            print(f"Wrote {output_path}")
        else:
            print(task)
        return 0

    draft = read_draft(Path(args.draft).expanduser().resolve())
    digest_dir, digest_id, manifest = materialize_digest_project(source_dir, draft)
    print(json.dumps({
        "job_id": digest_id,
        "folder": digest_dir.name,
        "path": str(digest_dir),
        "title": manifest["title"],
        "reader": f"http://localhost:3001/reader/{digest_id}",
    }, indent=2))
    return 0


def build_agent_task(source_dir: Path) -> str:
    archive = _read_json(source_dir / "archive.json")
    manifest = _read_json(source_dir / "manifest.json")
    source_chapters = archive.get("archive", [])
    draft_path = source_dir / "generated" / "ai-digest-draft.json"
    command = f'python3 tools/create_ai_digest_version.py "{source_dir}" --draft "{draft_path}"'

    return f"""Create a Smart YouTube Reader AI digest draft for this project.

{DIGEST_AGENT_TASK}

Important workflow:
1. Read the archive text and inspect the actual attached frame images before deciding what to keep.
2. Cut intros, outros, sponsor chatter, repeated sections, hype, and low-value transitions.
3. Keep durable concepts, procedures, definitions, examples, caveats, and visual explanations.
4. Preserve source_indices so the CLI can carry forward the original image references.
5. Write JSON only to:
   {draft_path}
6. Run:
   {command}

Project folder:
{source_dir}

Video title:
{manifest.get("title") or source_dir.name}

YouTube:
{manifest.get("url") or "(not available)"}

Draft JSON shape:
{{
  "title": "Short no-fluff learning title",
  "changes_summary": ["Removed filler.", "Merged repeated concepts."],
  "chapters": [
    {{
      "source_indices": [0, 1],
      "concept": "Concept name",
      "summary": "One-sentence overview.",
      "content": "Dense teaching text for AI agents.",
      "timestamp_start": 0,
      "timestamp_end": 120
    }}
  ]
}}

Source chapter payload:
{build_digest_user_prompt(source_chapters)}
"""


def read_draft(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = _extract_json_object(raw)
    if not isinstance(parsed, dict):
        raise SystemExit("Digest draft must be a JSON object.")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
