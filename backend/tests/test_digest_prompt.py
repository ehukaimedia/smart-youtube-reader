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
        self.assertIn("preservation_items", prompt)
        self.assertIn("merge checklist", prompt)

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

    def test_prompt_uses_transcript_slice_for_preservation_items(self):
        prompt = build_digest_user_prompt(
            SOURCE,
            source_transcript=[
                {
                    "text": "Meta harness scores 76.4% on Terminal Bench 2.",
                    "start": 35,
                    "duration": 4,
                },
                {
                    "text": "Outside the chapter window should be ignored.",
                    "start": 400,
                    "duration": 4,
                },
            ],
        )
        self.assertIn("76.4% on Terminal Bench 2", prompt)
        self.assertNotIn("Outside the chapter window", prompt)


if __name__ == "__main__":
    unittest.main()
