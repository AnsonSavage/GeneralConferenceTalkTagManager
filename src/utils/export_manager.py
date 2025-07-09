"""
Export utilities for conference talk database content.
"""
from datetime import datetime
from typing import List, Dict
from ..database.base_database import BaseDatabaseInterface


class ExportManager:
    """Handles exporting database content to various formats."""
    
    def __init__(self, database: BaseDatabaseInterface):
        """
        Initialize the export manager.
        
        Args:
            database: The database instance to export from
        """
        self.database = database
    
    def export_to_markdown(self, output_file: str = None) -> str:
        """
        Export database content to markdown format organized by tag hierarchy.
        
        Args:
            output_file: Optional file path to write the markdown content
            
        Returns:
            The generated markdown content as a string
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
        
        # Generate markdown content
        markdown_content = []
        markdown_content.append("# Conference Talks Database Export\n")
        markdown_content.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # Process each root tag
        for root_tag in sorted(root_tags, key=lambda x: x['name']):
            self._export_tag_hierarchy(root_tag, markdown_content, tags_dict, level=1)
        
        # Join all content
        full_content = '\n'.join(markdown_content)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_content)
        
        return full_content
    
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
    
    def _export_tag_hierarchy(self, tag_info: Dict, markdown_content: List[str], tags_dict: Dict, level: int = 1):
        """Recursively export tag hierarchy to markdown"""
        # Create heading based on level
        heading_prefix = '#' * (level + 1)  # Start at h2 since h1 is the main title
        markdown_content.append(f"{heading_prefix} {tag_info['name']}")
        
        if tag_info['description']:
            markdown_content.append(f"*{tag_info['description']}*")
        
        markdown_content.append("")
        
        # Get paragraphs that should be displayed under this specific tag
        # Only show paragraphs where this tag is one of the most specific tags
        all_paragraphs = self.database.get_paragraphs_by_tag(tag_info['id'])
        
        # Filter to only include paragraphs where this tag is the most specific
        paragraphs_to_show = []
        for paragraph in all_paragraphs:
            para_id = paragraph['id']
            most_specific_tags = self._get_most_specific_tags_for_paragraph(para_id, tags_dict)
            
            # Only include this paragraph if the current tag is one of the most specific
            if tag_info['id'] in most_specific_tags:
                paragraphs_to_show.append(paragraph)
        
        for paragraph in paragraphs_to_show:
            # Add paragraph content as bullet point
            markdown_content.append(f"• {paragraph['content']}")
            
            # Add keywords if any
            if paragraph['matched_keywords']:
                keywords_str = ", ".join(paragraph['matched_keywords'])
                markdown_content.append(f"  - **Keywords:** {keywords_str}")
            
            # Add notes if any
            if paragraph['notes'] and paragraph['notes'].strip():
                markdown_content.append(f"  - **Note:** {paragraph['notes'].strip()}")
            
            # Check if paragraph is assigned to other most specific tags (siblings)
            most_specific_tags = self._get_most_specific_tags_for_paragraph(paragraph['id'], tags_dict)
            other_specific_tags = [tid for tid in most_specific_tags if tid != tag_info['id']]
            
            if other_specific_tags:
                # Get names of other specific tags
                other_tag_names = []
                for tag_id in other_specific_tags:
                    if tag_id in tags_dict:
                        other_tag_names.append(tags_dict[tag_id]['name'])
                
                if other_tag_names:
                    other_tags_str = ", ".join(sorted(other_tag_names))
                    markdown_content.append(f"  - **Also found under:** {other_tags_str}")
            
            # Add source information with hyperlink
            if paragraph['hyperlink'] and paragraph['hyperlink'].strip():
                markdown_content.append(f"  - **Source:** [{paragraph['speaker']} - {paragraph['talk_title']} ({paragraph['conference_date']})]({paragraph['hyperlink']})")
            else:
                markdown_content.append(f"  - **Source:** {paragraph['speaker']} - {paragraph['talk_title']} ({paragraph['conference_date']})")
            markdown_content.append("")
        
        # Process children recursively
        for child_tag in sorted(tag_info['children'], key=lambda x: x['name']):
            self._export_tag_hierarchy(child_tag, markdown_content, tags_dict, level + 1)