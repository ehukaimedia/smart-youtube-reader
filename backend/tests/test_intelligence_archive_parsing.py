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

    def test_normalize_generated_chapters_shifts_tight_overlap_start(self):
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
                "start_time": 12,
                "end_time": 45,
            },
        ]

        normalized, repairs = intelligence._normalize_generated_chapters(chapters, 0, 90)

        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized[1]["start_time"], 40)
        self.assertEqual(normalized[1]["end_time"], 45)
        self.assertTrue(any(repair["action"] == "shifted_start_after_previous" for repair in repairs))

    def test_normalize_generated_chapters_drops_after_overlap_repair(self):
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
                "start_time": 12,
                "end_time": 20,
            },
        ]

        normalized, repairs = intelligence._normalize_generated_chapters(chapters, 0, 90)

        self.assertEqual(len(normalized), 1)
        self.assertTrue(any(repair["action"] == "dropped_after_overlap_repair" for repair in repairs))

    def test_expand_chapters_to_transcript_evidence_extends_quoted_rows(self):
        chapters = [
            {
                "title": "Harness finding",
                "summary": "Harness changed the benchmark outcome.",
                "content": "LangChain confirmed that modifying harness infrastructure ranked five.",
                "start_time": 0,
                "end_time": 10,
            }
        ]
        transcript = [
            {"text": "Intro sentence", "start": 0, "duration": 4},
            {
                "text": "LangChain confirmed it by modifying only harness infrastructure to rank five",
                "start": 42,
                "duration": 6,
            },
        ]

        expanded, repairs = intelligence._expand_chapters_to_transcript_evidence(chapters, transcript, 0, 60)

        self.assertEqual(expanded[0]["start_time"], 0)
        self.assertEqual(expanded[0]["end_time"], 48)
        self.assertTrue(any(repair["action"] == "expanded_to_cover_transcript_evidence" for repair in repairs))

    def test_add_transcript_gap_chapters_covers_contentful_gap(self):
        chapters = [
            {
                "title": "Before gap",
                "summary": "Before",
                "content": "Before content",
                "start_time": 0,
                "end_time": 20,
            },
            {
                "title": "After gap",
                "summary": "After",
                "content": "After content",
                "start_time": 80,
                "end_time": 100,
            },
        ]
        transcript = [
            {
                "text": (
                    "Rank two with Opus rank one with Haiku smaller model outranking larger models "
                    "through harness optimization alone meta harness scores terminal bench optimized "
                    "system field hand engineered entries transfer improved five other models reusable "
                    "asset harness accuracy points state art fewer tokens finding changes calculus "
                    "portable structure improves other models representation orchestration memory "
                    "retrieval topology reusable engineering result"
                ),
                "start": 30,
                "duration": 40,
            }
        ]

        expanded, repairs = intelligence._add_transcript_gap_chapters(chapters, transcript, 0, 100)

        self.assertEqual(len(expanded), 3)
        self.assertEqual(expanded[1]["start_time"], 20)
        self.assertEqual(expanded[1]["end_time"], 80)
        self.assertEqual(expanded[1]["_fallback"], "transcript_gap")
        self.assertTrue(any(repair["action"] == "added_transcript_gap_chapter" for repair in repairs))

    def test_clean_transcript_text_strips_caption_noise_markers(self):
        cleaned = intelligence._clean_transcript_text(
            "intro >> [music] >> body of the talk [Applause] outro [inaudible: 12:34]"
        )
        self.assertEqual(cleaned, "intro body of the talk outro")

    def test_trim_to_sentence_boundary_trims_when_terminator_present(self):
        trimmed = intelligence._trim_to_sentence_boundary(
            "First complete sentence. Second complete sentence! Trailing partial that should drop"
        )
        self.assertEqual(trimmed, "First complete sentence. Second complete sentence!")

    def test_trim_to_sentence_boundary_keeps_text_when_no_terminator(self):
        text = "no terminator here at all so keep it whole"
        self.assertEqual(intelligence._trim_to_sentence_boundary(text), text)

    def test_trim_to_sentence_boundary_keeps_text_when_cut_too_aggressive(self):
        text = "Short. " + "x" * 200
        self.assertEqual(intelligence._trim_to_sentence_boundary(text), text)

    def test_gap_chapter_content_strips_music_marker_and_completes_sentence(self):
        chapters = [
            {
                "title": "Before",
                "summary": "Before",
                "content": "Before",
                "start_time": 0,
                "end_time": 20,
            },
            {
                "title": "After",
                "summary": "After",
                "content": "After",
                "start_time": 80,
                "end_time": 100,
            },
        ]
        transcript = [
            {
                "text": (
                    ">> [music] >> Harness engineering absorbs the prior two and adds what the "
                    "model can't do on its own. Orchestration memory verification safety determine "
                    "production behavior more than weights. The discipline takes on an odd shape in practice "
                    "with reusable components emerging from optimization runs across multiple model families. "
                    "Researchers continue refining how agents write an agent's"
                ),
                "start": 30,
                "duration": 40,
            }
        ]

        expanded, _ = intelligence._add_transcript_gap_chapters(chapters, transcript, 0, 100)
        gap = expanded[1]
        self.assertEqual(gap["_fallback"], "transcript_gap")
        self.assertNotIn("[music]", gap["content"])
        self.assertNotIn(">>", gap["content"])
        self.assertTrue(gap["content"].rstrip()[-1] in ".!?", gap["content"])
        self.assertNotIn("write an agent's", gap["content"])

    def test_gap_chapter_fires_for_13_second_gap_with_substantive_content(self):
        chapters = [
            {
                "title": "Before",
                "summary": "Before",
                "content": "Before",
                "start_time": 0,
                "end_time": 20,
            },
            {
                "title": "After",
                "summary": "After",
                "content": "After",
                "start_time": 33.3,
                "end_time": 60,
            },
        ]
        transcript = [
            {
                "text": (
                    "Three eras in four years prompt engineering context engineering harness "
                    "engineering. Harness engineering absorbs prior eras orchestration memory "
                    "retrieval verification safety production behavior reusable components "
                    "portable structure improves representation across multiple models reusable "
                    "assets harness accuracy points state fewer tokens finding changes calculus."
                ),
                "start": 20.0,
                "duration": 13.3,
            }
        ]

        expanded, repairs = intelligence._add_transcript_gap_chapters(chapters, transcript, 0, 60)

        self.assertEqual(len(expanded), 3)
        self.assertEqual(expanded[1]["_fallback"], "transcript_gap")
        self.assertTrue(any(repair["action"] == "added_transcript_gap_chapter" for repair in repairs))


if __name__ == "__main__":
    unittest.main()
