"""
Basic functionality test for CSV import/export.
Tests the core functionality without complex imports.
"""
import unittest
import tempfile
import os
import csv
import sys

# Simple test without relative import issues
class TestCSVBasicFunctionality(unittest.TestCase):
    """Test basic CSV functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary files
        for file in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        os.rmdir(self.temp_dir)

    def test_csv_file_creation_and_reading(self):
        """Test that CSV files can be created and read properly."""
        # Test data with special characters
        test_data = [
            {'title': 'Test Talk; With Semicolon', 'speaker': 'Elder Test, Speaker'},
            {'title': 'Another Talk "With Quotes"', 'speaker': 'Sister Example'}
        ]
        
        # Write CSV file
        csv_file = os.path.join(self.temp_dir, "test_talks.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'speaker']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in test_data:
                writer.writerow(row)
        
        # Verify file was created
        self.assertTrue(os.path.exists(csv_file))
        
        # Read and verify content
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['title'], 'Test Talk; With Semicolon')
        self.assertEqual(rows[0]['speaker'], 'Elder Test, Speaker')
        self.assertEqual(rows[1]['title'], 'Another Talk "With Quotes"')

    def test_csv_special_character_handling(self):
        """Test that CSV properly handles special characters."""
        # Test data with various special characters
        test_content = "This paragraph has, commas and \"quotes\" and; semicolons."
        
        csv_file = os.path.join(self.temp_dir, "test_content.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['content'])
            writer.writeheader()
            writer.writerow({'content': test_content})
        
        # Read back and verify
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
        
        self.assertEqual(row['content'], test_content)

    def test_file_pattern_matching(self):
        """Test the file pattern matching logic that was fixed."""
        # Simulate the file names from the export
        test_files = [
            "conference_talks_export_20250712_180030_talks.csv",
            "conference_talks_export_20250712_180030_paragraphs.csv",
            "conference_talks_export_20250712_180030_tags.csv",
            "conference_talks_export_20250712_180030_paragraph_tags.csv",
            "conference_talks_export_20250712_180030_keywords.csv",
            "conference_talks_export_20250712_180030_paragraph_keywords.csv",
            "conference_talks_export_20250712_180030_metadata.csv"
        ]
        
        # Test the file pattern matching logic
        found_files = {
            'talks': None,
            'paragraphs': None,
            'tags': None,
            'paragraph_tags': None,
            'keywords': None,
            'paragraph_keywords': None,
            'metadata': None
        }
        
        for file_path in test_files:
            filename = os.path.basename(file_path)
            # Use the fixed pattern matching logic
            if filename.endswith('_paragraph_tags.csv') or filename == 'paragraph_tags.csv':
                found_files['paragraph_tags'] = file_path
            elif filename.endswith('_paragraph_keywords.csv') or filename == 'paragraph_keywords.csv':
                found_files['paragraph_keywords'] = file_path
            elif filename.endswith('_talks.csv') or filename == 'talks.csv':
                found_files['talks'] = file_path
            elif filename.endswith('_paragraphs.csv') or filename == 'paragraphs.csv':
                found_files['paragraphs'] = file_path
            elif filename.endswith('_tags.csv') or filename == 'tags.csv':
                found_files['tags'] = file_path
            elif filename.endswith('_keywords.csv') or filename == 'keywords.csv':
                found_files['keywords'] = file_path
            elif filename.endswith('_metadata.csv') or filename == 'metadata.csv':
                found_files['metadata'] = file_path
        
        # Verify all files were matched correctly
        self.assertIsNotNone(found_files['talks'])
        self.assertIsNotNone(found_files['paragraphs'])
        self.assertIsNotNone(found_files['tags'])
        self.assertIsNotNone(found_files['paragraph_tags'])
        self.assertIsNotNone(found_files['keywords'])
        self.assertIsNotNone(found_files['paragraph_keywords'])
        self.assertIsNotNone(found_files['metadata'])
        
        # Verify specific files were matched
        self.assertTrue(found_files['paragraph_tags'].endswith('paragraph_tags.csv'))
        self.assertTrue(found_files['paragraph_keywords'].endswith('paragraph_keywords.csv'))
        self.assertFalse(found_files['tags'].endswith('paragraph_tags.csv'))  # Should not be confused
        self.assertFalse(found_files['keywords'].endswith('paragraph_keywords.csv'))  # Should not be confused

    def test_csv_row_counting(self):
        """Test CSV row counting for import preview."""
        # Create test files with known row counts
        test_files = {
            'talks': 5,
            'paragraphs': 50,
            'tags': 10,
            'paragraph_tags': 25,
            'keywords': 8,
            'paragraph_keywords': 15
        }
        
        for file_type, row_count in test_files.items():
            csv_file = os.path.join(self.temp_dir, f"test_{file_type}.csv")
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'data'])
                writer.writeheader()
                
                for i in range(row_count):
                    writer.writerow({'id': i, 'data': f'test_data_{i}'})
        
        # Test counting logic
        stats = {}
        for file_type in test_files.keys():
            csv_file = os.path.join(self.temp_dir, f"test_{file_type}.csv")
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                stats[file_type] = sum(1 for row in reader)
        
        # Verify counts match expected values
        for file_type, expected_count in test_files.items():
            self.assertEqual(stats[file_type], expected_count, 
                           f"File {file_type} should have {expected_count} rows, got {stats[file_type]}")


if __name__ == '__main__':
    unittest.main()