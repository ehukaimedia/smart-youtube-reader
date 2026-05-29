import unittest

from app.digest import (
    _append_unique_specific,
    _extract_digest_preservation_items,
    _transcript_text_for_chapter,
    build_digest_user_prompt,
)


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
        self.assertIn("generated/chapter-01-concept.webp", prompt)
        self.assertIn("operator_image_note", prompt)
        self.assertIn("simple-infographic", prompt)
        self.assertIn("premium-infographic", prompt)
        self.assertIn("GPT Image 2", prompt)

    def test_prompt_without_images_keeps_source_indices_instruction(self):
        prompt = build_digest_user_prompt(SOURCE)
        self.assertIn("Use source_indices to preserve the original images", prompt)
        self.assertNotIn("generated/chapter-01-concept.webp", prompt)

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

    def test_preservation_items_rank_generic_named_entities_and_numbers(self):
        items = _extract_digest_preservation_items(
            "Mayo Clinic's DERM-AX trial reached 76.4% response on Phase 3 patients. "
            "Northstar Labs removed 80% of the screening steps and improved throughput. "
            "Guides, MD reached 60,000 repositories. "
            "The rest of this paragraph is connective prose without a concrete claim."
        )
        joined = " ".join(items)
        self.assertIn("DERM-AX", joined)
        self.assertIn("76.4%", joined)
        self.assertIn("Northstar Labs", joined)
        self.assertIn("80%", joined)
        self.assertIn("GUIDES.md", joined)

    def test_specific_dedup_keeps_numeric_variant(self):
        selected = []
        seen = set()
        _append_unique_specific(selected, seen, "Vercel removed tools")
        _append_unique_specific(selected, seen, "Vercel removed tools by 80%")
        _append_unique_specific(selected, seen, "Vercel removed tools by 80%")
        self.assertEqual(selected, ["Vercel removed tools", "Vercel removed tools by 80%"])

    def test_transcript_text_handles_reversed_ranges_and_music(self):
        text = _transcript_text_for_chapter(
            [
                {"text": "Keep this Phase 2 finding.", "start": 12, "duration": 3},
                {"text": "Drop [music] only.", "start": 14, "duration": 2},
                {"text": "Outside range.", "start": 30, "duration": 2},
            ],
            20,
            10,
        )
        self.assertEqual(text, "Keep this Phase 2 finding.")


if __name__ == "__main__":
    unittest.main()
