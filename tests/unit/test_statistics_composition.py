"""Tests for category composition utilities on the statistics page."""
import os
import sys
import tempfile
import unittest

# Ensure src package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from database.sqlite_database import SQLiteConferenceTalksDB
from src.pages.statistics import (
    _assign_base_colors_to_tags,
    _calculate_category_composition_segments,
)


class TestCategoryComposition(unittest.TestCase):
    """Validate composition segment calculations for overlapping subcategories."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_composition.db")
        self.database = SQLiteConferenceTalksDB({"db_path": self.db_path})

        # Create tags: parent with three immediate children
        self.tag_main = self.database.add_tag("Main")
        self.tag_a = self.database.add_tag("A", parent_tag_id=self.tag_main)
        self.tag_b = self.database.add_tag("B", parent_tag_id=self.tag_main)
        self.tag_c = self.database.add_tag("C", parent_tag_id=self.tag_main)

        # Create a single talk with five paragraphs
        talk_id = self.database.add_talk(
            title="Sample Talk",
            speaker="Speaker",
            conference_date="2024-04",
            hyperlink="https://example.com/sample",
        )
        paragraphs = [
            self.database.add_paragraph(talk_id, idx + 1, f"Paragraph {idx + 1}")
            for idx in range(5)
        ]

        # Tag paragraphs to create overlaps matching the specification example
        # Paragraph 1 tagged with A and B
        self.database.tag_paragraph(paragraphs[0], self.tag_a)
        self.database.tag_paragraph(paragraphs[0], self.tag_b)
        # Paragraph 2 tagged with A and C
        self.database.tag_paragraph(paragraphs[1], self.tag_a)
        self.database.tag_paragraph(paragraphs[1], self.tag_c)
        # Paragraph 3 tagged with A only
        self.database.tag_paragraph(paragraphs[2], self.tag_a)
        # Paragraph 4 tagged with B and C
        self.database.tag_paragraph(paragraphs[3], self.tag_b)
        self.database.tag_paragraph(paragraphs[3], self.tag_c)
        # Paragraph 5 tagged with C only
        self.database.tag_paragraph(paragraphs[4], self.tag_c)

    def tearDown(self) -> None:
        self.database = None
        self.temp_dir.cleanup()

    def test_calculate_category_composition_segments(self) -> None:
        """Shared paragraphs should produce distinct composition segments."""
        tag_stats = self.database.get_tag_usage_statistics()
        tag_dict = {tag["id"]: tag for tag in tag_stats}
        base_color_map = _assign_base_colors_to_tags(tag_stats)

        paragraph_cache = {}
        segments, total = _calculate_category_composition_segments(
            child_tag_ids=[self.tag_a, self.tag_b, self.tag_c],
            database=self.database,
            paragraph_cache=paragraph_cache,
            tag_dict=tag_dict,
            base_color_map=base_color_map,
        )

        self.assertEqual(5, total)
        self.assertEqual(5, len(segments))

        counts_by_label = {segment["segment_label"]: segment["paragraph_count"] for segment in segments}
        expected_counts = {
            "A": 1,
            "C": 1,
            "A + B": 1,
            "A + C": 1,
            "B + C": 1,
        }
        self.assertDictEqual(expected_counts, counts_by_label)

        for segment in segments:
            self.assertAlmostEqual(20.0, segment["percentage"], places=4)
            self.assertTrue(segment["color"].startswith("rgba("))

        # Verify paragraph cache populated for all children
        self.assertSetEqual({self.tag_a, self.tag_b, self.tag_c}, set(paragraph_cache.keys()))

if __name__ == "__main__":
    unittest.main()
