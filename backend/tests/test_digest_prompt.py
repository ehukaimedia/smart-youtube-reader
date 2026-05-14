import unittest

from app.digest import build_digest_user_prompt


SOURCE = [
    {
        "concept": "Concept A",
        "summary": "Summary A",
        "content": "Content A",
        "timestamp_start": 0,
        "timestamp_end": 30,
        "images": [],
    },
    {
        "concept": "Concept B",
        "summary": "Summary B",
        "content": "Content B",
        "timestamp_start": 30,
        "timestamp_end": 60,
        "images": ["frames/0001.png"],
    },
]


class DigestPromptTests(unittest.TestCase):
    def test_prompt_states_preservation_rule(self):
        prompt = build_digest_user_prompt(SOURCE)
        self.assertIn("Preserve every numeric claim", prompt)
        self.assertIn("proper noun", prompt)
        self.assertIn("concrete example", prompt)

    def test_prompt_states_compression_target(self):
        prompt = build_digest_user_prompt(SOURCE)
        self.assertIn("60-80 percent", prompt)
        self.assertIn("Merge tightly related", prompt)

    def test_prompt_with_images_keeps_image_instruction_and_preservation(self):
        prompt = build_digest_user_prompt(SOURCE, include_generated_images=True)
        self.assertIn("Preserve every numeric claim", prompt)
        self.assertIn("generated/chapter-01-concept.png", prompt)
        self.assertIn("operator_image_note", prompt)

    def test_prompt_without_images_keeps_source_indices_instruction(self):
        prompt = build_digest_user_prompt(SOURCE)
        self.assertIn("Use source_indices to preserve the original images", prompt)
        self.assertNotIn("generated/chapter-01-concept.png", prompt)


if __name__ == "__main__":
    unittest.main()
