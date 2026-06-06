from __future__ import annotations

import os
import subprocess
from pathlib import Path


APP_NAME = "smart-youtube-reader"


def app_commit() -> str | None:
    for key in ("SMART_READER_APP_COMMIT", "GITHUB_SHA"):
        value = os.environ.get(key)
        if value:
            return value

    repo_root = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    commit = result.stdout.strip()
    return commit or None


def app_metadata() -> dict:
    return {
        "name": APP_NAME,
        "commit": app_commit(),
    }

