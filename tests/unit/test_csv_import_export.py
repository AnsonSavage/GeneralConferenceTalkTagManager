"""
Unit tests for CSV import/export functionality.
"""
import unittest
import tempfile
import os
import sqlite3
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the src directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.csv_exporter import CSVExporter
from utils.csv_importer import CSVImporter
from utils.export_manager import ExportManager
from utils.import_manager import ImportManager
from database.sqlite_database import SQLiteDatabase


class TestCSVExportImport(unittest.TestCase):
    """Test CSV export and import functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize database
        self.database = SQLiteDatabase(self.db_path)
        
        # Create temporary directory for CSV files
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample test data
        self.sample_talk_data = {
            'title': 'Test Talk; With Semicolon',
            'speaker': 'Elder Test, Speaker',
            'conference_date': 'October 2023',
            'session': 'General Session',
            'url': 'https://example.com/test-talk'
        }
        
        # Add sample data to database
        self.talk_id = self.database.add_talk(
            title=self.sample_talk_data['title'],
            speaker=self.sample_talk_data['speaker'],
            conference_date=self.sample_talk_data['conference_date'],
            hyperlink=self.sample_talk_data['url'],
            session=self.sample_talk_data['session']
        )
        
        self.paragraph_id = self.database.add_paragraph(
            talk_id=self.talk_id,
            paragraph_number=1,
            content="This is a test paragraph with, commas and \"quotes\".",
            matched_keywords=["test", "example"]
        )
        
        self.tag_id = self.database.add_tag(
            name="Test Tag",
            description="A test tag for unit testing"
        )
        
        self.database.tag_paragraph(self.paragraph_id, self.tag_id)
        self.database.add_keywords(["test", "example", "unit-testing"])

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary database
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
        
        # Clean up temporary CSV files
        for file in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        os.rmdir(self.temp_dir)

    def test_csv_export_creates_all_files(self):
        """Test that CSV export creates all required files."""
        export_manager = ExportManager(self.database)
        output_prefix = os.path.join(self.temp_dir, "test_export")
        
        summary = export_manager.export_to_csv(output_prefix)
        
        # Check that all expected files are created
        expected_files = [
            "test_export_talks.csv",
            "test_export_paragraphs.csv", 
            "test_export_tags.csv",
            "test_export_paragraph_tags.csv",
            "test_export_keywords.csv",
            "test_export_paragraph_keywords.csv",
            "test_export_metadata.csv",
            "test_export_summary.txt"
        ]
        
        for filename in expected_files:
            file_path = os.path.join(self.temp_dir, filename)
            self.assertTrue(os.path.exists(file_path), f"File {filename} was not created")

    def test_csv_export_content_properly_escaped(self):
        """Test that CSV export properly escapes special characters."""
        export_manager = ExportManager(self.database)
        output_prefix = os.path.join(self.temp_dir, "test_export")
        
        export_manager.export_to_csv(output_prefix)
        
        # Read the talks CSV and verify content
        talks_file = os.path.join(self.temp_dir, "test_export_talks.csv")
        with open(talks_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Verify that semicolons and commas are properly handled
        self.assertIn('"Test Talk; With Semicolon"', content)
        self.assertIn('"Elder Test, Speaker"', content)

    def test_csv_import_validates_files(self):
        """Test that CSV import properly validates files."""
        # First export data
        export_manager = ExportManager(self.database)
        output_prefix = os.path.join(self.temp_dir, "test_export")
        export_manager.export_to_csv(output_prefix)
        
        # Create importer and validate
        importer = CSVImporter(self.database)
        
        # Test with all files
        csv_files = [
            os.path.join(self.temp_dir, "test_export_talks.csv"),
            os.path.join(self.temp_dir, "test_export_paragraphs.csv"),
            os.path.join(self.temp_dir, "test_export_tags.csv"),
            os.path.join(self.temp_dir, "test_export_paragraph_tags.csv"),
            os.path.join(self.temp_dir, "test_export_keywords.csv"),
            os.path.join(self.temp_dir, "test_export_paragraph_keywords.csv"),
            os.path.join(self.temp_dir, "test_export_metadata.csv")
        ]
        
        validation_result = importer.validate_files(csv_files)
        
        self.assertTrue(validation_result['is_valid'])
        self.assertEqual(len(validation_result['errors']), 0)
        
        # Verify all files are found
        found_files = validation_result['found_files']
        self.assertIsNotNone(found_files['talks'])
        self.assertIsNotNone(found_files['paragraphs'])
        self.assertIsNotNone(found_files['tags'])
        self.assertIsNotNone(found_files['paragraph_tags'])
        self.assertIsNotNone(found_files['keywords'])
        self.assertIsNotNone(found_files['paragraph_keywords'])
        self.assertIsNotNone(found_files['metadata'])

    def test_csv_import_missing_required_files(self):
        """Test that CSV import fails when required files are missing."""
        importer = CSVImporter(self.database)
        
        # Test with missing required files
        csv_files = [
            os.path.join(self.temp_dir, "test_export_talks.csv"),
            # Missing paragraphs.csv and tags.csv
        ]
        
        # Create the talks file
        with open(csv_files[0], 'w', encoding='utf-8') as f:
            f.write("id,title,speaker,conference_date,session,hyperlink\n")
            f.write("1,Test,Speaker,2023,,\n")
        
        validation_result = importer.validate_files(csv_files)
        
        self.assertFalse(validation_result['is_valid'])
        self.assertGreater(len(validation_result['errors']), 0)

    def test_csv_roundtrip_export_import(self):
        """Test that data exported and then imported remains the same."""
        # Export data
        export_manager = ExportManager(self.database)
        output_prefix = os.path.join(self.temp_dir, "test_export")
        export_manager.export_to_csv(output_prefix)
        
        # Create a new database for import
        temp_db2 = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db2.close()
        import_db_path = temp_db2.name
        
        try:
            import_database = SQLiteDatabase(import_db_path)
            
            # Import data
            import_manager = ImportManager(import_database)
            csv_files = [
                os.path.join(self.temp_dir, "test_export_talks.csv"),
                os.path.join(self.temp_dir, "test_export_paragraphs.csv"),
                os.path.join(self.temp_dir, "test_export_tags.csv"),
                os.path.join(self.temp_dir, "test_export_paragraph_tags.csv"),
                os.path.join(self.temp_dir, "test_export_keywords.csv"),
                os.path.join(self.temp_dir, "test_export_paragraph_keywords.csv"),
                os.path.join(self.temp_dir, "test_export_metadata.csv")
            ]
            
            import_result = import_manager.import_from_csv(csv_files, merge_mode=False)
            
            # Verify import succeeded
            self.assertTrue(import_result['success'])
            
            # Verify data integrity
            talks = import_database.get_talks_summary()
            self.assertEqual(len(talks), 1)
            self.assertEqual(talks[0]['title'], self.sample_talk_data['title'])
            self.assertEqual(talks[0]['speaker'], self.sample_talk_data['speaker'])
            
            paragraphs = import_database.get_all_paragraphs_with_filters()
            self.assertEqual(len(paragraphs), 1)
            self.assertEqual(paragraphs[0]['content'], "This is a test paragraph with, commas and \"quotes\".")
            
            tags = import_database.get_all_tags()
            self.assertEqual(len(tags), 1)
            self.assertEqual(tags[0]['name'], "Test Tag")
            
            # Verify paragraph-tag associations
            paragraph_tags = import_database.get_paragraph_tags(paragraphs[0]['id'])
            self.assertEqual(len(paragraph_tags), 1)
            self.assertEqual(paragraph_tags[0]['name'], "Test Tag")
            
        finally:
            # Clean up import database
            if os.path.exists(import_db_path):
                os.unlink(import_db_path)

    def test_csv_import_merge_mode(self):
        """Test that CSV import merge mode works correctly."""
        # Export original data
        export_manager = ExportManager(self.database)
        output_prefix = os.path.join(self.temp_dir, "test_export")
        export_manager.export_to_csv(output_prefix)
        
        # Add additional data to original database
        additional_talk_id = self.database.add_talk(
            title="Additional Talk",
            speaker="Another Speaker",
            conference_date="April 2024"
        )
        
        # Import into same database using merge mode
        import_manager = ImportManager(self.database)
        csv_files = [
            os.path.join(self.temp_dir, "test_export_talks.csv"),
            os.path.join(self.temp_dir, "test_export_paragraphs.csv"),
            os.path.join(self.temp_dir, "test_export_tags.csv"),
            os.path.join(self.temp_dir, "test_export_paragraph_tags.csv"),
            os.path.join(self.temp_dir, "test_export_keywords.csv"),
            os.path.join(self.temp_dir, "test_export_paragraph_keywords.csv"),
            os.path.join(self.temp_dir, "test_export_metadata.csv")
        ]
        
        import_result = import_manager.import_from_csv(csv_files, merge_mode=True)
        
        # Verify import succeeded
        self.assertTrue(import_result['success'])
        
        # Verify both original and additional data exist
        talks = self.database.get_talks_summary()
        self.assertEqual(len(talks), 2)  # Original + additional
        
        talk_titles = [talk['title'] for talk in talks]
        self.assertIn("Additional Talk", talk_titles)
        self.assertIn(self.sample_talk_data['title'], talk_titles)

    def test_csv_import_replace_mode(self):
        """Test that CSV import replace mode clears existing data."""
        # Add additional data to database
        additional_talk_id = self.database.add_talk(
            title="Additional Talk",
            speaker="Another Speaker",
            conference_date="April 2024"
        )
        
        # Export only original data
        export_manager = ExportManager(self.database)
        output_prefix = os.path.join(self.temp_dir, "test_export")
        export_manager.export_to_csv(output_prefix)
        
        # Import using replace mode
        import_manager = ImportManager(self.database)
        csv_files = [
            os.path.join(self.temp_dir, "test_export_talks.csv"),
            os.path.join(self.temp_dir, "test_export_paragraphs.csv"),
            os.path.join(self.temp_dir, "test_export_tags.csv"),
            os.path.join(self.temp_dir, "test_export_paragraph_tags.csv"),
            os.path.join(self.temp_dir, "test_export_keywords.csv"),
            os.path.join(self.temp_dir, "test_export_paragraph_keywords.csv"),
            os.path.join(self.temp_dir, "test_export_metadata.csv")
        ]
        
        import_result = import_manager.import_from_csv(csv_files, merge_mode=False)
        
        # Verify import succeeded
        self.assertTrue(import_result['success'])
        
        # Verify only imported data exists (additional talk should be gone)
        talks = self.database.get_talks_summary()
        self.assertEqual(len(talks), 1)
        self.assertEqual(talks[0]['title'], self.sample_talk_data['title'])

    def test_csv_import_error_handling(self):
        """Test CSV import error handling with malformed data."""
        # Create malformed CSV file
        malformed_talks_file = os.path.join(self.temp_dir, "malformed_talks.csv")
        with open(malformed_talks_file, 'w', encoding='utf-8') as f:
            f.write("id,title,speaker,conference_date,session,hyperlink\n")
            f.write("invalid_id,Test,Speaker,2023,,\n")  # Invalid ID
        
        # Create minimal valid files
        paragraphs_file = os.path.join(self.temp_dir, "test_paragraphs.csv")
        with open(paragraphs_file, 'w', encoding='utf-8') as f:
            f.write("id,talk_id,paragraph_number,content,matched_keywords,notes,reviewed,review_date\n")
        
        tags_file = os.path.join(self.temp_dir, "test_tags.csv")
        with open(tags_file, 'w', encoding='utf-8') as f:
            f.write("id,name,description,parent_tag_id\n")
        
        # Try to import
        import_manager = ImportManager(self.database)
        csv_files = [malformed_talks_file, paragraphs_file, tags_file]
        
        import_result = import_manager.import_from_csv(csv_files, merge_mode=False)
        
        # Import should succeed overall but have errors
        self.assertTrue(import_result['success'])
        self.assertGreater(len(import_result['stats']['errors']), 0)


if __name__ == '__main__':
    unittest.main()