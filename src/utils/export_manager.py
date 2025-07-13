"""
Export utilities for conference talk database content.
"""
from datetime import datetime
from typing import List, Dict, Any
from ..database.base_database import BaseDatabaseInterface
from .base_exporter import BaseExporter
from .markdown_exporter import MarkdownExporter


class ExportManager:
    """Handles exporting database content using various exporters."""
    
    def __init__(self, database: BaseDatabaseInterface):
        """
        Initialize the export manager.
        
        Args:
            database: The database instance to export from
        """
        self.database = database
    
    def prepare_export_data(self) -> Dict[str, Any]:
        """
        Prepare all necessary data for export.
        
        Returns:
            Dictionary containing all export data
        """
        # Get all tags with their hierarchy
        tags_data = self.database.get_all_tags()
        
        # Build tag hierarchy
        tags_dict = {}
        root_tags = []
        
        for tag in tags_data:
            tag_info = {
                'id': tag['id'],
                'name': tag['name'],
                'description': tag['description'],
                'parent_id': tag['parent_tag_id'],
                'children': []
            }
            tags_dict[tag['id']] = tag_info
            
            if tag['parent_tag_id'] is None:
                root_tags.append(tag_info)
        
        # Build parent-child relationships
        for tag_info in tags_dict.values():
            if tag_info['parent_id'] is not None:
                parent = tags_dict.get(tag_info['parent_id'])
                if parent:
                    parent['children'].append(tag_info)
        
        # Prepare paragraphs data for each tag
        for tag_info in tags_dict.values():
            tag_id = tag_info['id']
            all_paragraphs = self.database.get_paragraphs_by_tag(tag_id)
            
            # Filter to only include paragraphs where this tag is the most specific
            paragraphs_to_show = []
            for paragraph in all_paragraphs:
                para_id = paragraph['id']
                most_specific_tags = self._get_most_specific_tags_for_paragraph(para_id, tags_dict)
                
                # Only include this paragraph if the current tag is one of the most specific
                if tag_id in most_specific_tags:
                    # Add additional metadata to paragraph
                    paragraph['most_specific_tags'] = most_specific_tags
                    paragraphs_to_show.append(paragraph)
            
            tag_info['paragraphs'] = paragraphs_to_show
        
        return {
            'tags_dict': tags_dict,
            'root_tags': root_tags,
            'export_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def export_with_exporter(self, exporter: BaseExporter, output_file: str = None) -> str:
        """
        Export database content using the specified exporter.
        
        Args:
            exporter: The exporter instance to use
            output_file: Optional file path to write the content
            
        Returns:
            The generated content as a string
        """
        export_data = self.prepare_export_data()
        return exporter.export(export_data, output_file)
    
    def export_to_markdown(self, output_file: str = None) -> str:
        """
        Export database content to markdown format (backward compatibility).
        
        Args:
            output_file: Optional file path to write the markdown content
            
        Returns:
            The generated markdown content as a string
        """
        markdown_exporter = MarkdownExporter()
        return self.export_with_exporter(markdown_exporter, output_file)
    
    def _get_most_specific_tags_for_paragraph(self, paragraph_id: int, tags_dict: Dict) -> List[int]:
        """Get the most specific (leaf) tags for a paragraph"""
        # Get all tags for this paragraph
        paragraph_tags = self.database.get_paragraph_tags(paragraph_id)
        paragraph_tag_ids = {tag['id'] for tag in paragraph_tags}
        
        # Find leaf tags (tags that don't have any children that are also tagged for this paragraph)
        leaf_tags = []
        
        for tag_id in paragraph_tag_ids:
            # Check if any children of this tag are also tagged for this paragraph
            has_tagged_children = False
            
            # Find all children of this tag
            for other_tag_id, tag_info in tags_dict.items():
                if tag_info['parent_id'] == tag_id and other_tag_id in paragraph_tag_ids:
                    has_tagged_children = True
                    break
            
            # If no children are tagged, this is a leaf tag
            if not has_tagged_children:
                leaf_tags.append(tag_id)
        
        return leaf_tags