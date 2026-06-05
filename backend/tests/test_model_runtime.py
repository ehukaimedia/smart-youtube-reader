import unittest
from unittest.mock import patch

from app import model_runtime


class ModelRuntimeTests(unittest.TestCase):
    def test_normalize_message_preserves_images_for_ollama_vision(self):
        message = model_runtime._normalize_message({
            "role": "user",
            "content": "What is visible?",
            "images": ["abc123"],
        })

        self.assertEqual(message["role"], "user")
        self.assertEqual(message["content"], "What is visible?")
        self.assertEqual(message["images"], ["abc123"])

    def test_check_model_raises_useful_pull_error_when_missing(self):
        with patch.object(model_runtime, "list_local_models", return_value=[]):
            with self.assertRaisesRegex(RuntimeError, "ollama pull gemma4:12b"):
                model_runtime.check_model("gemma4:12b")

    def test_chat_posts_non_streaming_ollama_payload(self):
        captured = {}

        def fake_request(path, payload=None, timeout=30):
            captured["path"] = path
            captured["payload"] = payload
            captured["timeout"] = timeout
            return {"message": {"content": "done"}}

        with (
            patch.object(model_runtime, "check_model", return_value=True),
            patch.object(model_runtime, "_request_json", side_effect=fake_request),
        ):
            output = model_runtime.chat(
                "gemma4:12b",
                [{"role": "user", "content": "Pick", "images": ["abc123"]}],
                temperature=0.1,
                max_tokens=128,
            )

        self.assertEqual(output, "done")
        self.assertEqual(captured["path"], "/api/chat")
        self.assertFalse(captured["payload"]["stream"])
        self.assertFalse(captured["payload"]["think"])
        self.assertEqual(captured["payload"]["options"]["num_predict"], 128)
        self.assertEqual(captured["payload"]["messages"][0]["images"], ["abc123"])


if __name__ == "__main__":
    unittest.main()
