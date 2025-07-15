"""
CSV importer for conference talk database content.
Imports data from CSV files exported by CSVExporter.
"""
import csv
import json
import os
from typing import Dict, Any, List, Optional
from .base_importer import BaseImporter


class CSVImporter(BaseImporter):
    """Imports database content from CSV format."""
    
    def __init__(self, database):
        """Initialize the CSV importer."""
        super().__init__(database)
        self.import_stats = {
            'talks_imported': 0,
            'paragraphs_imported': 0,
            'tags_imported': 0,
            'paragraph_tags_imported': 0,
            'keywords_imported': 0,
            'paragraph_keywords_imported': 0,
            'errors': []
        }
    
    def validate_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Validate that the provided files are compatible with this importer.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'found_files': {
                'talks': None,
                'paragraphs': None,
                'tags': None,
                'paragraph_tags': None,
                'keywords': None,
                'paragraph_keywords': None,
                'metadata': None
            }
        }
        
        # Check if files exist
        for file_path in file_paths:
            if not os.path.exists(file_path):
                validation_result['errors'].append(f"File not found: {file_path}")
                validation_result['is_valid'] = False
                continue
            
            # Identify file type by name pattern (check more specific patterns first)
            filename = os.path.basename(file_path)
            if filename.endswith('_paragraph_tags.csv') or filename == 'paragraph_tags.csv':
                validation_result['found_files']['paragraph_tags'] = file_path
            elif filename.endswith('_paragraph_keywords.csv') or filename == 'paragraph_keywords.csv':
                validation_result['found_files']['paragraph_keywords'] = file_path
            elif filename.endswith('_talks.csv') or filename == 'talks.csv':
                validation_result['found_files']['talks'] = file_path
            elif filename.endswith('_paragraphs.csv') or filename == 'paragraphs.csv':
                validation_result['found_files']['paragraphs'] = file_path
            elif filename.endswith('_tags.csv') or filename == 'tags.csv':
                validation_result['found_files']['tags'] = file_path
            elif filename.endswith('_keywords.csv') or filename == 'keywords.csv':
                validation_result['found_files']['keywords'] = file_path
            elif filename.endswith('_metadata.csv') or filename == 'metadata.csv':
                validation_result['found_files']['metadata'] = file_path
        
        # Check for required files
        required_files = ['talks', 'paragraphs', 'tags']
        for required in required_files:
            if validation_result['found_files'][required] is None:
                validation_result['errors'].append(f"Required file missing: {required}.csv")
                validation_result['is_valid'] = False
        
        # Validate file structure
        if validation_result['is_valid']:
            try:
                self._validate_file_structure(validation_result['found_files'])
            except Exception as e:
                validation_result['errors'].append(f"File structure validation failed: {str(e)}")
                validation_result['is_valid'] = False
        
        return validation_result
    
    def _validate_file_structure(self, found_files: Dict[str, Optional[str]]):
        """Validate the structure of CSV files."""
        expected_columns = {
            'talks': ['id', 'title', 'speaker', 'conference_date', 'hyperlink'],
            'paragraphs': ['id', 'talk_id', 'paragraph_number', 'content', 'matched_keywords', 
                          'notes', 'reviewed', 'review_date'],
            'tags': ['id', 'name', 'description', 'parent_tag_id'],
            'paragraph_tags': ['paragraph_id', 'tag_id'],
            'keywords': ['keyword'],
            'paragraph_keywords': ['paragraph_id', 'keyword']
        }
        
        for file_type, file_path in found_files.items():
            if file_path and file_type in expected_columns:
                with open(file_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    actual_columns = set(reader.fieldnames or [])
                    expected_columns_set = set(expected_columns[file_type])
                    
                    # For backward compatibility, allow session field in talks but don't require it
                    if file_type == 'talks' and 'session' in actual_columns:
                        actual_columns.discard('session')
                    
                    if not expected_columns_set.issubset(actual_columns):
                        missing = expected_columns_set - actual_columns
                        raise ValueError(f"Missing columns in {file_type}.csv: {missing}")
    
    def import_data(self, file_paths: List[str], merge_mode: bool = False) -> Dict[str, Any]:
        """
        Import data from CSV files into the database.
        
        Args:
            file_paths: List of file paths to import from
            merge_mode: If True, merge with existing data. If False, clear database first.
            
        Returns:
            Dictionary containing import results and statistics
        """
        # Reset import stats
        self.import_stats = {
            'talks_imported': 0,
            'paragraphs_imported': 0,
            'tags_imported': 0,
            'paragraph_tags_imported': 0,
            'keywords_imported': 0,
            'paragraph_keywords_imported': 0,
            'errors': []
        }
        
        # Validate files first
        validation_result = self.validate_files(file_paths)
        if not validation_result['is_valid']:
            return {
                'success': False,
                'errors': validation_result['errors'],
                'stats': self.import_stats
            }
        
        found_files = validation_result['found_files']
        
        try:
            # Clear database if not in merge mode
            if not merge_mode:
                self._clear_database()
            
            # Import in dependency order
            # 1. Import talks first (no dependencies)
            if found_files['talks']:
                self._import_talks(found_files['talks'], merge_mode)
            
            # 2. Import paragraphs (depends on talks)
            if found_files['paragraphs']:
                self._import_paragraphs(found_files['paragraphs'], merge_mode)
            
            # 3. Import tags (may have parent dependencies)
            if found_files['tags']:
                self._import_tags(found_files['tags'], merge_mode)
            
            # 4. Import paragraph-tag associations (depends on paragraphs and tags)
            if found_files['paragraph_tags']:
                self._import_paragraph_tags(found_files['paragraph_tags'])
            
            # 5. Import keywords (no dependencies)
            if found_files['keywords']:
                self._import_keywords(found_files['keywords'])
            
            # 6. Import paragraph-keyword associations (depends on paragraphs and keywords)
            if found_files['paragraph_keywords']:
                self._import_paragraph_keywords(found_files['paragraph_keywords'])
            
            return {
                'success': True,
                'stats': self.import_stats,
                'message': 'Import completed successfully'
            }
            
        except Exception as e:
            self.import_stats['errors'].append(f"Import failed: {str(e)}")
            return {
                'success': False,
                'errors': self.import_stats['errors'],
                'stats': self.import_stats
            }
    
    def _clear_database(self):
        """Clear all data from the database."""
        # Note: This is a destructive operation
        # In a real implementation, you might want to create a backup first
        try:
            # Get all tables and clear them in reverse dependency order
            import sqlite3
            
            # Use the database connection to clear tables
            if hasattr(self.database, 'db_path'):
                conn = sqlite3.connect(self.database.db_path)
                cursor = conn.cursor()
                
                # Disable foreign key constraints temporarily
                cursor.execute("PRAGMA foreign_keys = OFF")
                
                # Clear tables in reverse dependency order
                tables_to_clear = [
                    'paragraph_keywords',
                    'paragraph_tags', 
                    'keywords',
                    'tags',
                    'paragraphs',
                    'talks'
                ]
                
                for table in tables_to_clear:
                    cursor.execute(f"DELETE FROM {table}")
                
                # Reset auto-increment counters
                cursor.execute("DELETE FROM sqlite_sequence")
                
                # Re-enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys = ON")
                
                conn.commit()
                conn.close()
        except Exception as e:
            self.import_stats['errors'].append(f"Database clearing failed: {str(e)}")
            raise
    
    def _import_talks(self, file_path: str, merge_mode: bool):
        """Import talks from CSV file."""
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    if merge_mode:
                        # Use add_or_update_talk for merge mode
                        talk_data = {
                            'title': row['title'],
                            'speaker': row['speaker'],
                            'conference_date': row['conference_date'],
                            'url': row['hyperlink'] or None
                        }
                        self.database.add_or_update_talk(talk_data)
                    else:
                        # Direct insert for new database
                        self.database.add_talk(
                            title=row['title'],
                            speaker=row['speaker'],
                            conference_date=row['conference_date'],
                            hyperlink=row['hyperlink'] or None
                        )

                    self.import_stats['talks_imported'] += 1
                    
                except Exception as e:
                    print(f"Error importing talk: {row.get('title', 'Unknown')} - {e}")
                    continue
    
    def _import_paragraphs(self, file_path: str, merge_mode: bool):
        """Import paragraphs from CSV file."""
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    matched_keywords = json.loads(row['matched_keywords']) if row['matched_keywords'] else []
                    
                    if merge_mode:
                        # Use add_or_update_paragraph for merge mode
                        paragraph_id = self.database.add_or_update_paragraph(
                            talk_id=int(row['talk_id']),
                            paragraph_number=int(row['paragraph_number']),
                            content=row['content'],
                            matched_keywords=matched_keywords
                        )
                    else:
                        # Direct insert for new database
                        paragraph_id = self.database.add_paragraph(
                            talk_id=int(row['talk_id']),
                            paragraph_number=int(row['paragraph_number']),
                            content=row['content'],
                            matched_keywords=matched_keywords
                        )
                    
                    # Update notes and review status
                    if row['notes']:
                        self.database.update_paragraph_notes(paragraph_id, row['notes'])
                    
                    if row['reviewed'] and row['reviewed'].lower() in ['true', '1']:
                        self.database.mark_paragraph_reviewed(paragraph_id, True)
                    
                    self.import_stats['paragraphs_imported'] += 1
                    
                except Exception as e:
                    self.import_stats['errors'].append(f"Error importing paragraph {row.get('id', 'Unknown')}: {str(e)}")
    
    def _import_tags(self, file_path: str, merge_mode: bool):
        """Import tags from CSV file."""
        # Read all tags first to handle parent-child relationships
        tags_data = []
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tags_data.append(row)
        
        # Sort tags to import parents before children
        # Tags without parents first, then by parent_tag_id
        tags_data.sort(key=lambda x: (x['parent_tag_id'] != '', x['parent_tag_id']))
        
        # Keep track of imported tag IDs for ID mapping
        tag_id_mapping = {}
        
        for row in tags_data:
            try:
                parent_tag_id = None
                if row['parent_tag_id'] and row['parent_tag_id'] != '':
                    # Map old parent ID to new parent ID
                    old_parent_id = int(row['parent_tag_id'])
                    parent_tag_id = tag_id_mapping.get(old_parent_id)
                
                if merge_mode:
                    # Check if tag already exists
                    existing_tags = self.database.search_tags(row['name'])
                    if existing_tags:
                        # Tag exists, update it
                        tag_id = existing_tags[0]['id']
                        self.database.update_tag(
                            tag_id=tag_id,
                            name=row['name'],
                            description=row['description'] or None,
                            parent_tag_id=parent_tag_id
                        )
                    else:
                        # Tag doesn't exist, create it
                        tag_id = self.database.add_tag(
                            name=row['name'],
                            description=row['description'] or None,
                            parent_tag_id=parent_tag_id
                        )
                else:
                    # Direct insert for new database
                    tag_id = self.database.add_tag(
                        name=row['name'],
                        description=row['description'] or None,
                        parent_tag_id=parent_tag_id
                    )
                
                # Store ID mapping for child tags
                old_tag_id = int(row['id'])
                tag_id_mapping[old_tag_id] = tag_id
                
                self.import_stats['tags_imported'] += 1
                
            except Exception as e:
                self.import_stats['errors'].append(f"Error importing tag '{row.get('name', 'Unknown')}': {str(e)}")
    
    def _import_paragraph_tags(self, file_path: str):
        """Import paragraph-tag associations from CSV file."""
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    self.database.tag_paragraph(
                        paragraph_id=int(row['paragraph_id']),
                        tag_id=int(row['tag_id'])
                    )
                    self.import_stats['paragraph_tags_imported'] += 1
                    
                except Exception as e:
                    self.import_stats['errors'].append(f"Error importing paragraph-tag association: {str(e)}")
    
    def _import_keywords(self, file_path: str):
        """Import keywords from CSV file."""
        keywords = []
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                keywords.append(row['keyword'])
        
        try:
            self.database.add_keywords(keywords)
            self.import_stats['keywords_imported'] = len(keywords)
        except Exception as e:
            self.import_stats['errors'].append(f"Error importing keywords: {str(e)}")
    
    def _import_paragraph_keywords(self, file_path: str):
        """Import paragraph-keyword associations from CSV file."""
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Group by paragraph_id for batch processing
            paragraph_keywords = {}
            
            for row in reader:
                paragraph_id = int(row['paragraph_id'])
                keyword = row['keyword']
                
                if paragraph_id not in paragraph_keywords:
                    paragraph_keywords[paragraph_id] = []
                paragraph_keywords[paragraph_id].append(keyword)
            
            # Import associations
            for paragraph_id, keywords in paragraph_keywords.items():
                try:
                    self.database.add_paragraph_keyword_associations(paragraph_id, keywords)
                    self.import_stats['paragraph_keywords_imported'] += len(keywords)
                except Exception as e:
                    self.import_stats['errors'].append(f"Error importing paragraph-keyword associations for paragraph {paragraph_id}: {str(e)}")
    
    def get_import_summary(self) -> str:
        """Get a summary of the import operation."""
        summary_lines = [
            "CSV Import Summary",
            "=" * 20,
            f"Talks imported: {self.import_stats['talks_imported']}",
            f"Paragraphs imported: {self.import_stats['paragraphs_imported']}",
            f"Tags imported: {self.import_stats['tags_imported']}",
            f"Paragraph-tag associations: {self.import_stats['paragraph_tags_imported']}",
            f"Keywords imported: {self.import_stats['keywords_imported']}",
            f"Paragraph-keyword associations: {self.import_stats['paragraph_keywords_imported']}",
            f"Errors: {len(self.import_stats['errors'])}"
        ]
        
        if self.import_stats['errors']:
            summary_lines.append("\nErrors:")
            for error in self.import_stats['errors']:
                summary_lines.append(f"  - {error}")
        
        return "\n".join(summary_lines)