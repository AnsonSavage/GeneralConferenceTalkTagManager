"""
CSV exporter for conference talk database content.
Exports all data necessary for complete database reconstruction.
"""
import csv
import json
from typing import Dict, Any
from datetime import datetime
from .base_exporter import BaseExporter


class CSVExporter(BaseExporter):
    """Exports database content to CSV format for complete data reconstruction."""
    
    def __init__(self):
        """Initialize the CSV exporter."""
        super().__init__()
        self.exported_files = []
    
    def export(self, export_data: Dict[str, Any], output_file: str = None) -> str:
        """
        Export the provided data to CSV format.
        
        Args:
            export_data: Dictionary containing all necessary data for export
            output_file: Optional file path prefix for CSV files
            
        Returns:
            Summary of exported files as a string
        """
        # Get the database instance from export_data to query raw data
        database = export_data.get('database')
        if not database:
            raise ValueError("Database instance required for CSV export")
        
        # Determine output file prefix
        if output_file:
            if output_file.endswith('.csv'):
                file_prefix = output_file[:-4]
            else:
                file_prefix = output_file
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_prefix = f"conference_talks_export_{timestamp}"
        
        # Export all tables
        self.exported_files = []
        
        # Export talks
        self._export_talks(database, f"{file_prefix}_talks.csv")
        
        # Export paragraphs
        self._export_paragraphs(database, f"{file_prefix}_paragraphs.csv")
        
        # Export tags
        self._export_tags(database, f"{file_prefix}_tags.csv")
        
        # Export paragraph_tags associations
        self._export_paragraph_tags(database, f"{file_prefix}_paragraph_tags.csv")
        
        # Export keywords
        self._export_keywords(database, f"{file_prefix}_keywords.csv")
        
        # Export paragraph_keywords associations
        self._export_paragraph_keywords(database, f"{file_prefix}_paragraph_keywords.csv")
        
        # Export metadata
        self._export_metadata(export_data, f"{file_prefix}_metadata.csv")
        
        # Create summary
        summary = self._create_export_summary()
        
        # Write summary to file
        summary_file = f"{file_prefix}_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        self.exported_files.append(summary_file)
        
        return summary
    
    def _export_talks(self, database, filename: str):
        """Export talks table to CSV."""
        talks = database.get_talks_summary()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if talks:
                fieldnames = ['id', 'title', 'speaker', 'conference_date', 'hyperlink']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for talk in talks:
                    writer.writerow({
                        'id': talk['id'],
                        'title': talk['title'],
                        'speaker': talk['speaker'],
                        'conference_date': talk['conference_date'],
                        'hyperlink': talk.get('hyperlink', '')
                    })
        
        self.exported_files.append(filename)
    
    def _export_paragraphs(self, database, filename: str):
        """Export paragraphs table to CSV."""
        paragraphs = database.get_all_paragraphs_with_filters()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if paragraphs:
                fieldnames = ['id', 'talk_id', 'paragraph_number', 'content', 'matched_keywords', 
                             'notes', 'reviewed', 'review_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for paragraph in paragraphs:
                    writer.writerow({
                        'id': paragraph['id'],
                        'talk_id': paragraph['talk_id'],
                        'paragraph_number': paragraph['paragraph_number'],
                        'content': paragraph['content'],
                        'matched_keywords': json.dumps(paragraph.get('matched_keywords', [])),
                        'notes': paragraph.get('notes', ''),
                        'reviewed': paragraph.get('reviewed', False),
                        'review_date': paragraph.get('review_date', '')
                    })
        
        self.exported_files.append(filename)
    
    def _export_tags(self, database, filename: str):
        """Export tags table to CSV."""
        tags = database.get_all_tags()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if tags:
                fieldnames = ['id', 'name', 'description', 'parent_tag_id']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for tag in tags:
                    writer.writerow({
                        'id': tag['id'],
                        'name': tag['name'],
                        'description': tag.get('description', ''),
                        'parent_tag_id': tag.get('parent_tag_id', '')
                    })
        
        self.exported_files.append(filename)
    
    def _export_paragraph_tags(self, database, filename: str):
        """Export paragraph_tags associations to CSV."""
        # Get all paragraph-tag associations
        paragraphs = database.get_all_paragraphs_with_filters()
        associations = []
        
        for paragraph in paragraphs:
            tags = database.get_paragraph_tags(paragraph['id'])
            for tag in tags:
                associations.append({
                    'paragraph_id': paragraph['id'],
                    'tag_id': tag['id']
                })
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['paragraph_id', 'tag_id']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for association in associations:
                writer.writerow(association)
        
        self.exported_files.append(filename)
    
    def _export_keywords(self, database, filename: str):
        """Export keywords table to CSV."""
        keywords = database.get_keywords()
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['keyword']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for keyword in keywords:
                writer.writerow({'keyword': keyword})
        
        self.exported_files.append(filename)
    
    def _export_paragraph_keywords(self, database, filename: str):
        """Export paragraph_keywords associations to CSV."""
        # Get all paragraph-keyword associations
        paragraphs = database.get_all_paragraphs_with_filters()
        associations = []
        
        for paragraph in paragraphs:
            keywords = database.get_paragraphs_by_keyword(paragraph['id'])
            for keyword_data in keywords:
                if keyword_data['id'] == paragraph['id']:  # Match the paragraph
                    for keyword in keyword_data.get('matched_keywords', []):
                        associations.append({
                            'paragraph_id': paragraph['id'],
                            'keyword': keyword
                        })
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['paragraph_id', 'keyword']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for association in associations:
                writer.writerow(association)
        
        self.exported_files.append(filename)
    
    def _export_metadata(self, export_data: Dict[str, Any], filename: str):
        """Export metadata about the export."""
        metadata = {
            'export_timestamp': export_data.get('export_timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'export_version': '1.0',
            'database_type': 'sqlite',
            'exporter': 'CSVExporter'
        }
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['key', 'value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for key, value in metadata.items():
                writer.writerow({'key': key, 'value': value})
        
        self.exported_files.append(filename)
    
    def _create_export_summary(self) -> str:
        """Create a summary of the export."""
        summary_lines = [
            "Conference Talks Database - CSV Export Summary",
            "=" * 50,
            f"Export completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total files exported: {len(self.exported_files)}",
            "",
            "Exported files:"
        ]
        
        for filename in self.exported_files:
            summary_lines.append(f"  - {filename}")
        
        summary_lines.extend([
            "",
            "Import Instructions:",
            "1. Use the CSV Import function in the application",
            "2. Select all CSV files from this export",
            "3. Choose 'Create New Database' or 'Merge with Current'",
            "4. The data will be reconstructed maintaining all relationships",
            "",
            "File Descriptions:",
            "- talks.csv: Conference talks metadata",
            "- paragraphs.csv: Paragraph content with notes and review status",
            "- tags.csv: Tag hierarchy and descriptions",
            "- paragraph_tags.csv: Paragraph-tag associations",
            "- keywords.csv: Keyword list",
            "- paragraph_keywords.csv: Paragraph-keyword associations",
            "- metadata.csv: Export metadata and version info"
        ])
        
        return "\n".join(summary_lines)