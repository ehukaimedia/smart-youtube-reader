"""Smoke tests for the repo-root digest CLIs in tools/.

These cover the argparse entry points and the task-printing branches (including the
--text-only flip), which are the README's headline operator workflow but were
previously untested. They run each CLI as a subprocess against the bundled demo
projects in examples/demo-jobs (read-only: the task-print path writes nothing).
"""

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / "tools"
EXAMPLES = REPO / "examples" / "demo-jobs"
CLAUDE_PROJECT = EXAMPLES / "smart-youtube-reader-claude"
GEMINI_PROJECT = EXAMPLES / "smart-youtube-reader-gemini"

IMAGE_TASK_MARKER = "Create one novel WebP teaching image per digest chapter"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


@unittest.skipUnless(CLAUDE_PROJECT.exists(), "demo project fixture missing")
class AiDigestCliTests(unittest.TestCase):
    def test_default_prints_image_rich_task(self):
        result = _run(str(TOOLS / "create_ai_digest_version.py"), str(CLAUDE_PROJECT))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(IMAGE_TASK_MARKER, result.stdout)

    def test_text_only_drops_the_image_task(self):
        result = _run(
            str(TOOLS / "create_ai_digest_version.py"), str(CLAUDE_PROJECT), "--text-only"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        # The --text-only branch must NOT instruct creating new teaching images.
        self.assertNotIn(IMAGE_TASK_MARKER, result.stdout)

    def test_conflicting_flags_rejected(self):
        result = _run(
            str(TOOLS / "create_ai_digest_version.py"),
            str(CLAUDE_PROJECT),
            "--with-images",
            "--text-only",
        )
        self.assertNotEqual(result.returncode, 0)


@unittest.skipUnless(
    CLAUDE_PROJECT.exists() and GEMINI_PROJECT.exists(), "demo project fixtures missing"
)
class GroupDigestCliTests(unittest.TestCase):
    def test_default_prints_group_task(self):
        result = _run(
            str(TOOLS / "create_group_ai_digest_version.py"),
            str(CLAUDE_PROJECT),
            str(GEMINI_PROJECT),
            "--title",
            "Combined Test Digest",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GROUP AI digest", result.stdout)


class SummaryThumbnailCliTests(unittest.TestCase):
    def test_missing_project_exits_nonzero(self):
        result = _run(
            str(TOOLS / "create_summary_thumbnail.py"), "no-such-project-xyz-123"
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("not found", (result.stderr + result.stdout).lower())


if __name__ == "__main__":
    unittest.main()
