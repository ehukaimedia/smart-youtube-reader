import unittest
from unittest.mock import patch

from app import intelligence


class ArchiveParsingTests(unittest.TestCase):
    def test_xml_parser_keeps_valid_chapters_when_sibling_is_malformed(self):
        raw = """
        <archive>
          <chapter>
            <title>Valid Chapter</title>
            <summary>Summary</summary>
            <content>Grounded content</content>
            <start_time>0</start_time>
            <end_time>10</end_time>
          </chapter>
          <chapter>
            <title>Broken Chapter</title>
          </chapter>
        </archive>
        """

        chapters = intelligence._extract_xml_chapters(raw)

        self.assertEqual(len(chapters), 1)
        self.assertEqual(chapters[0]["title"], "Valid Chapter")
        self.assertEqual(chapters[0]["start_time"], 0.0)
        self.assertEqual(chapters[0]["end_time"], 10.0)

    def test_generate_archive_chunk_retries_xml_then_uses_json_fallback(self):
        chunk = {"start": 0.0, "end": 12.0, "text": "[0.0-12.0] transcript evidence"}
        malformed_xml = "<archive><chapter><title>Missing fields</title></chapter></archive>"
        valid_json = """
        [
          {
            "title": "JSON Fallback",
            "summary": "Fallback summary",
            "content": "transcript evidence",
            "start_time": 0,
            "end_time": 12
          }
        ]
        """

        with patch.object(intelligence, "_chat", side_effect=[malformed_xml, malformed_xml, valid_json]) as chat:
            chapters, meta = intelligence._generate_archive_chunk("test-model", chunk)

        self.assertEqual(chat.call_count, 3)
        self.assertEqual(len(chapters), 1)
        self.assertEqual(chapters[0]["title"], "JSON Fallback")
        self.assertEqual(meta["format"], "json")
        self.assertTrue(meta["fallback"])
        self.assertEqual(meta["attempts"], 3)

    def test_normalize_generated_chapters_repairs_overlapping_ranges(self):
        chapters = [
            {
                "title": "First",
                "summary": "Summary one",
                "content": "Evidence one",
                "start_time": 10,
                "end_time": 40,
            },
            {
                "title": "Second",
                "summary": "Summary two",
                "content": "Evidence two",
                "start_time": 34,
                "end_time": 60,
            },
        ]

        normalized, repairs = intelligence._normalize_generated_chapters(chapters, 0, 90)

        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized[0]["start_time"], 10)
        self.assertEqual(normalized[0]["end_time"], 34)
        self.assertEqual(normalized[1]["start_time"], 34)
        self.assertEqual(normalized[1]["end_time"], 60)
        self.assertTrue(any(repair["action"] == "trimmed_previous_overlap" for repair in repairs))

    def test_normalize_generated_chapters_clamps_and_drops_invalid_chapters(self):
        chapters = [
            {
                "title": "Outside",
                "summary": "Summary",
                "content": "Evidence",
                "start_time": -5,
                "end_time": 130,
            },
            {
                "title": "",
                "summary": "Missing title",
                "content": "Evidence",
                "start_time": 10,
                "end_time": 20,
            },
        ]

        normalized, repairs = intelligence._normalize_generated_chapters(chapters, 0, 120)

        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["start_time"], 0)
        self.assertEqual(normalized[0]["end_time"], 120)
        self.assertTrue(any(repair["action"] == "clamped_to_transcript_bounds" for repair in repairs))
        self.assertTrue(any(repair["action"] == "dropped_empty_required_field" for repair in repairs))


if __name__ == "__main__":
    unittest.main()
