"""Tests for statistics histogram utilities and database time series aggregation."""
import os
import sys
import tempfile
import unittest
from collections import defaultdict

import altair as alt
from altair.vegalite.v5.api import LayerChart

# Ensure src package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from database.sqlite_database import SQLiteConferenceTalksDB
from src.pages.statistics import (
    _build_usage_histogram,
    _create_usage_histogram_chart,
    _prepare_histogram_dataframe,
)


class TestStatisticsHistograms(unittest.TestCase):
    """Validate histogram helpers and database time series queries."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_statistics.db")
        self.database = SQLiteConferenceTalksDB({"db_path": self.db_path})

        # Create sample tags and talks
        self.tag_faith = self.database.add_tag("Faith")
        self.tag_hope = self.database.add_tag("Hope")

        talk_april = self.database.add_talk(
            title="April Talk",
            speaker="Speaker 1",
            conference_date="2024-04",
            hyperlink="https://example.com/april",
        )
        paragraph_april = self.database.add_paragraph(
            talk_id=talk_april,
            paragraph_number=1,
            content="Paragraph about faith",
        )
        self.database.tag_paragraph(paragraph_april, self.tag_faith)

        talk_october = self.database.add_talk(
            title="October Talk",
            speaker="Speaker 2",
            conference_date="2024-10",
            hyperlink="https://example.com/october",
        )
        paragraph_october = self.database.add_paragraph(
            talk_id=talk_october,
            paragraph_number=1,
            content="Paragraph about hope",
        )
        self.database.tag_paragraph(paragraph_october, self.tag_hope)

        # Add a future conference with no tagged paragraphs to ensure zero counts appear
        self.database.add_talk(
            title="Future Talk",
            speaker="Speaker 3",
            conference_date="2025-04",
            hyperlink="https://example.com/future",
        )

    def tearDown(self) -> None:
        self.database = None
        self.temp_dir.cleanup()

    def test_get_tag_usage_time_series_by_tag_includes_zero_counts(self) -> None:
        """The per-tag time series should include conferences with zero usage."""
        tag_ids = {self.tag_faith, self.tag_hope}
        series = self.database.get_tag_usage_time_series(tag_ids, by_tag=True)

        self.assertTrue(series, "Expected non-empty time series for selected tags")

        counts_by_tag = defaultdict(dict)
        for entry in series:
            counts_by_tag[entry["tag_id"]][entry["conference_date"]] = entry["paragraph_count"]

        # Each tag should have entries for all three conferences
        self.assertSetEqual(
            {"2024-04-01", "2024-10-01", "2025-04-01"},
            set(counts_by_tag[self.tag_faith].keys()),
        )
        self.assertSetEqual(
            {"2024-04-01", "2024-10-01", "2025-04-01"},
            set(counts_by_tag[self.tag_hope].keys()),
        )

        # Verify paragraph counts per tag and conference
        self.assertEqual(1, counts_by_tag[self.tag_faith]["2024-04-01"])
        self.assertEqual(0, counts_by_tag[self.tag_faith]["2024-10-01"])
        self.assertEqual(0, counts_by_tag[self.tag_faith]["2025-04-01"])

        self.assertEqual(0, counts_by_tag[self.tag_hope]["2024-04-01"])
        self.assertEqual(1, counts_by_tag[self.tag_hope]["2024-10-01"])
        self.assertEqual(0, counts_by_tag[self.tag_hope]["2025-04-01"])

        # Combined (non per-tag) counts should match the sum of individual tags
        combined = self.database.get_tag_usage_time_series(tag_ids)
        combined_counts = {entry["conference_date"]: entry["paragraph_count"] for entry in combined}
        self.assertEqual({
            "2024-04-01": 1,
            "2024-10-01": 1,
            "2025-04-01": 0,
        }, combined_counts)

    def test_histogram_helpers_generate_regression_metrics(self) -> None:
        """Histogram helper functions should aggregate data and compute regression stats."""
        time_series = [
            {"conference_date": "2024-04-01", "paragraph_count": 1},
            {"conference_date": "2024-10-01", "paragraph_count": 3},
            {"conference_date": "2025-04-01", "paragraph_count": 5},
        ]

        histogram = _build_usage_histogram(time_series, frequency_months=6)
        self.assertEqual(3, len(histogram))

        df, slope, intercept, r_squared = _prepare_histogram_dataframe(histogram)
        self.assertFalse(df.empty)
        self.assertAlmostEqual(2.0, slope, places=3)
        self.assertAlmostEqual(1.0, intercept, places=3)
        self.assertAlmostEqual(1.0, r_squared, places=3)

        chart = _create_usage_histogram_chart(df)
        self.assertTrue(isinstance(chart, (alt.Chart, LayerChart)))


if __name__ == "__main__":
    unittest.main()
