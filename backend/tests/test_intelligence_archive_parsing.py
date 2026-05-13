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


if __name__ == "__main__":
    unittest.main()
