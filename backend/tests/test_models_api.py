import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main as app_main


class ModelsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app_main.app)

    def test_models_endpoint_only_marks_installed_models_as_selectable(self):
        with (
            patch.object(app_main, "list_local_models", return_value=["gemma4:12b"]),
            patch.object(app_main, "list_loaded_models", return_value=[]),
        ):
            body = self.client.get("/models").json()

        self.assertEqual(body["models"], ["gemma4:12b"])
        self.assertEqual(body["default_model"], "gemma4:12b")
        detail_by_name = {model["name"]: model for model in body["model_details"]}
        self.assertTrue(detail_by_name["gemma4:12b"]["installed"])
        self.assertFalse(detail_by_name["gemma4:26b"]["installed"])

    def test_create_job_rejects_missing_model_before_background_job(self):
        with (
            patch.object(app_main.job_store, "find_reusable_job", return_value=None),
            patch.object(app_main.job_store, "create_job") as create_job,
            patch.object(app_main, "check_model", side_effect=RuntimeError("ollama pull gemma4:26b")),
        ):
            response = self.client.post(
                "/jobs",
                json={
                    "video_url": "https://www.youtube.com/watch?v=abc12345678",
                    "model": "gemma4:26b",
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("ollama pull gemma4:26b", response.json()["detail"])
        create_job.assert_not_called()


if __name__ == "__main__":
    unittest.main()
