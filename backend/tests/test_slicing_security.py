"""Security regression tests for the video slicer's selected_files handling.

A malicious or buggy client could pass slicer `selected_files` entries containing
path-traversal sequences (e.g. "../../../etc/passwd"). Before the guard in
slicing._resolve_preview_file, finalize_sequence and save_slice_to_project read
those paths relative to the preview dir, enabling an arbitrary-file read. These
tests lock in the rejection.
"""

import json
import unittest
import tempfile
import zipfile
from pathlib import Path

from app import slicing


class _FakeJob:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir


class _FakeStore:
    def __init__(self, job: _FakeJob):
        self._job = job

    def get(self, job_id: str) -> _FakeJob:
        return self._job


class SlicingTraversalTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.data_dir = self.root / "job"
        self.preview_id = "prev1234"
        self.preview_dir = self.data_dir / "previews" / self.preview_id
        self.preview_dir.mkdir(parents=True)
        # A legitimate preview frame (bare basename).
        (self.preview_dir / "0001.jpg").write_bytes(b"benign-frame-bytes")
        # Preview metadata required by save_slice_to_project.
        (self.preview_dir / "preview_meta.json").write_text(
            json.dumps({"start": 0.0, "end": 1.0, "fps": 1})
        )
        # A secret OUTSIDE the preview dir that traversal would target.
        self.secret = self.root / "secret.txt"
        self.secret.write_text("TOP-SECRET-DO-NOT-LEAK")
        # preview_dir -> previews -> job -> root, so "../../../secret.txt" reaches it.
        self.traversal = "../../../secret.txt"
        self.store = _FakeStore(_FakeJob(self.data_dir))

    def tearDown(self):
        self._tmp.cleanup()

    def test_finalize_sequence_rejects_traversal(self):
        with self.assertRaises(ValueError):
            slicing.finalize_sequence(
                "job", self.preview_id, [self.traversal], self.store
            )
        # The secret must not have leaked into any produced zip.
        for zip_path in self.data_dir.glob("slices/*/sequence.zip"):
            with zipfile.ZipFile(zip_path) as zf:
                for name in zf.namelist():
                    self.assertNotIn(b"TOP-SECRET", zf.read(name))

    def test_save_slice_to_project_rejects_traversal(self):
        with self.assertRaises(ValueError):
            slicing.save_slice_to_project(
                "job", self.preview_id, [self.traversal], self.store
            )
        # The secret must not have been copied into any slice frames dir.
        for copied in self.data_dir.glob("slices/*/frames/*"):
            self.assertNotIn("secret", copied.name)

    def test_absolute_path_rejected(self):
        with self.assertRaises(ValueError):
            slicing.finalize_sequence(
                "job", self.preview_id, [str(self.secret)], self.store
            )

    def test_legitimate_basename_still_works(self):
        result = slicing.finalize_sequence(
            "job", self.preview_id, ["0001.jpg"], self.store
        )
        zip_path = self.data_dir / result["path"]
        self.assertTrue(zip_path.exists())
        with zipfile.ZipFile(zip_path) as zf:
            self.assertIn("0001.jpg", zf.namelist())
            self.assertEqual(zf.read("0001.jpg"), b"benign-frame-bytes")


if __name__ == "__main__":
    unittest.main()
