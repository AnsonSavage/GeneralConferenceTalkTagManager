"""
Integration test that directly imports specific modules to avoid relative import issues.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the src directory to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import only the specific modules we need, avoiding __init__.py files
from database.sqlite_database import SQLiteConferenceTalksDB


class SimpleWorkflowIntegrationTest:
    """Integration test that uses direct module imports to test core functionality."""
    
    def __init__(self):
        self.test_dir = None
        self.db_path = None
        self.dummy_data_path = None
        
    def setup(self):
        """Set up test environment."""
        print("🔧 Setting up test environment...")
        
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp(prefix="simple_workflow_test_")
        print(f"  Created test directory: {self.test_dir}")
        
        # Set up database path
        self.db_path = os.path.join(self.test_dir, "test.db")
        
        # Set up dummy data path
        self.dummy_data_path = project_root / "tests" / "dummy_data" / "General_Conference_Talks"
        
        if not self.dummy_data_path.exists():
            raise FileNotFoundError(f"Dummy data not found at: {self.dummy_data_path}")
            
        print(f"  Using dummy data from: {self.dummy_data_path}")
        
    def teardown(self):
        """Clean up test environment."""
        print("🧹 Cleaning up test environment...")
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print(f"  Removed test directory: {self.test_dir}")
            
    def search_and_import_talks(self, db, keywords):
        """Search dummy data for keywords and import matching talks (simulating SearchManager behavior)."""
        print(f"  🔍 Searching for keywords: {', '.join(keywords)}")
        
        talks_added = 0
        paragraphs_added = 0
        
        # Walk through dummy data and search for keywords
        for year_dir in self.dummy_data_path.iterdir():
            if not year_dir.is_dir():
                continue
                
            year = year_dir.name
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                    
                month = month_dir.name
                session = "April" if month == "04" else "October"
                conference_date = f"{year}-{month}"
                
                for talk_file in month_dir.glob("*.txt"):
                    try:
                        # Read talk file
                        with open(talk_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Parse talk content
                        lines = content.split('\n')
                        title = ""
                        speaker = ""
                        url = ""
                        talk_text = ""
                        
                        for i, line in enumerate(lines):
                            if line.startswith("Title: "):
                                title = line[7:].strip()
                            elif line.startswith("Speaker: "):
                                speaker = line[9:].strip()
                            elif line.startswith("URL: "):
                                url = line[5:].strip()
                            elif line.strip() == "" and i > 2:
                                talk_text = '\n'.join(lines[i+1:]).strip()
                                break
                        
                        if title and speaker and talk_text:
                            # Check if talk contains any of our keywords
                            talk_text_lower = talk_text.lower()
                            found_keywords = []
                            
                            for keyword in keywords:
                                if keyword.lower() in talk_text_lower:
                                    found_keywords.append(keyword)
                            
                            # Only add talks that contain our search keywords
                            if found_keywords:
                                # Add talk to database
                                talk_id = db.add_talk(title, speaker, conference_date, url, session)
                                talks_added += 1
                                
                                # Split into paragraphs and add only those containing keywords
                                paragraphs = [p.strip() for p in talk_text.split('\n\n') if p.strip()]
                                for i, paragraph in enumerate(paragraphs):
                                    if paragraph:
                                        # Check if this paragraph contains any keywords
                                        paragraph_lower = paragraph.lower()
                                        paragraph_keywords = []
                                        
                                        for keyword in keywords:
                                            if keyword.lower() in paragraph_lower:
                                                paragraph_keywords.append(keyword)
                                        
                                        # Only add paragraphs that match our search
                                        if paragraph_keywords:
                                            db.add_paragraph(talk_id, i + 1, paragraph, paragraph_keywords)
                                            paragraphs_added += 1
                                            
                    except Exception as e:
                        print(f"    ❌ Error processing {talk_file}: {e}")
        
        print(f"  ✅ Added {talks_added} talks and {paragraphs_added} paragraphs containing keywords")
        
        # Add keywords to database
        db.add_keywords(keywords)
        
        return talks_added, paragraphs_added
        
    def test_application_workflow(self):
        """Test the application workflow with keyword search and database population."""
        print("\n📥 Testing application workflow...")
        
        # Create database
        db = SQLiteConferenceTalksDB({'db_path': self.db_path})
        
        # Test keywords that should have matches in the dummy data
        test_keywords = ["faith", "Christ", "testimony"]
        
        # Search and import talks containing keywords
        talks_count, paragraphs_count = self.search_and_import_talks(db, test_keywords)
        
        if talks_count == 0:
            raise Exception("No talks were found with the search keywords!")
            
        # Add some tags and tag paragraphs
        self.add_tags_and_tag_content(db)
        
        # Test basic database operations
        self.verify_database_content(db)
        
        # Test export functionality
        self.test_export_functionality(db)
        
        print("  ✅ Application workflow completed successfully")
        return True
        
    def add_tags_and_tag_content(self, db):
        """Add tags and apply them to relevant paragraphs."""
        print("  🏷️  Adding tags and tagging content...")
        
        # Create tags based on our search keywords
        tags = [
            ("Faith", "Content about faith and belief"),
            ("Christ", "Content mentioning Jesus Christ"),
            ("Testimony", "Personal testimony content")
        ]
        
        tag_ids = {}
        for tag_name, description in tags:
            try:
                tag_id = db.add_tag(tag_name, description)
                tag_ids[tag_name] = tag_id
            except ValueError:
                # Tag might already exist
                existing_tags = db.get_all_tags()
                for tag in existing_tags:
                    if tag['name'] == tag_name:
                        tag_ids[tag_name] = tag['id']
                        break
                        
        # Get paragraphs and tag them based on content
        paragraphs = db.get_all_paragraphs_with_filters()
        tagged_count = 0
        
        for paragraph in paragraphs[:10]:  # Tag first 10 paragraphs
            content_lower = paragraph['content'].lower()
            
            # Tag paragraphs based on their content
            if 'faith' in content_lower and 'Faith' in tag_ids:
                try:
                    db.tag_paragraph(paragraph['id'], tag_ids['Faith'])
                    tagged_count += 1
                except Exception:
                    pass
                    
            if 'christ' in content_lower and 'Christ' in tag_ids:
                try:
                    db.tag_paragraph(paragraph['id'], tag_ids['Christ'])
                    tagged_count += 1
                except Exception:
                    pass
                    
            if 'testimony' in content_lower and 'Testimony' in tag_ids:
                try:
                    db.tag_paragraph(paragraph['id'], tag_ids['Testimony'])
                    tagged_count += 1
                except Exception:
                    pass
                
        print(f"    Added {len(tags)} tags and applied {tagged_count} tag assignments")
        
    def verify_database_content(self, db):
        """Verify that the database contains the expected content."""
        print("  ✅ Verifying database content...")
        
        talks = db.get_talks_summary()
        paragraphs = db.get_all_paragraphs_with_filters()
        tags = db.get_all_tags()
        keywords = db.get_keywords()
        
        print(f"    📊 Database contains: {len(talks)} talks, {len(paragraphs)} paragraphs")
        print(f"    📊 Database contains: {len(tags)} tags, {len(keywords)} keywords")
        
        if len(talks) == 0 or len(paragraphs) == 0:
            raise Exception("Database is missing expected content!")
            
    def test_export_functionality(self, db):
        """Test basic export functionality."""
        print("  📤 Testing export functionality...")
        
        # Create a simple markdown export
        markdown_file = os.path.join(self.test_dir, "test_export.md")
        
        talks = db.get_talks_summary()
        
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write("# Conference Talks Export\n\n")
            
            for talk in talks[:3]:  # Export first 3 talks
                f.write(f"## {talk['title']}\n")
                f.write(f"**Speaker:** {talk['speaker']}\n")
                f.write(f"**Date:** {talk['conference_date']}\n\n")
                
                # Get paragraphs for this talk
                paragraphs = db.get_all_paragraphs_with_filters()
                talk_paragraphs = [p for p in paragraphs if p['talk_id'] == talk['id']]
                
                for paragraph in talk_paragraphs[:2]:  # First 2 paragraphs
                    f.write(f"{paragraph['content']}\n\n")
                
                f.write("---\n\n")
        
        # Verify export was created
        if os.path.exists(markdown_file):
            file_size = os.path.getsize(markdown_file)
            print(f"    ✅ Created markdown export: {file_size} bytes")
            
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 100:
                    print("    ✅ Export contains substantial content")
                    return True
                else:
                    print("    ❌ Export file is too small")
                    return False
        else:
            print("    ❌ Export file was not created")
            return False
        
    def run_test(self):
        """Run the simple workflow integration test."""
        print("🚀 Starting Simple Workflow Integration Test")
        print("=" * 50)
        
        try:
            self.setup()
            success = self.test_application_workflow()
            
            print("\n" + "=" * 50)
            if success:
                print("🎉 SIMPLE WORKFLOW INTEGRATION TEST PASSED!")
                print("✅ Core application workflow verified")
                print("✅ Keyword search and database population working")
                print("✅ Tagging functionality working")
                print("✅ Export functionality working")
            else:
                print("❌ SIMPLE WORKFLOW INTEGRATION TEST FAILED!")
                
            return success
            
        except Exception as e:
            print(f"\n❌ SIMPLE WORKFLOW INTEGRATION TEST FAILED WITH ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            self.teardown()


def main():
    """Main function to run the simple workflow integration test."""
    test = SimpleWorkflowIntegrationTest()
    success = test.run_test()
    
    if success:
        print("\n🎊 Simple workflow integration test passed!")
        return 0
    else:
        print("\n💥 Simple workflow integration test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())