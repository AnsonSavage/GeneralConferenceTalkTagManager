"""
Markdown exporter for conference talk database content.
"""
import re
from typing import Dict, Any, List
from .base_exporter import BaseExporter
from .helpers import create_paragraph_link


class MarkdownExporter(BaseExporter):
    """Exports database content to markdown format."""
    
    def __init__(self, bold_keywords: bool = True):
        """
        Initialize the markdown exporter.
        
        Args:
            bold_keywords: Whether to bold matched keywords in paragraph content (default: True)
        """
        self.bold_keywords = bold_keywords
    
    def export(self, export_data: Dict[str, Any], output_file: str = None) -> str:
        """
        Export the provided data to markdown format.
        
        Args:
            export_data: Dictionary containing all necessary data for export
            output_file: Optional file path to write the markdown content
            
        Returns:
            The generated markdown content as a string
        """
        tags_dict = export_data['tags_dict']
        root_tags = export_data['root_tags']
        export_timestamp = export_data['export_timestamp']
        
        # Generate markdown content
        markdown_content = []
        markdown_content.append("# Conference Talks Database Export\n")
        markdown_content.append(f"*Generated on {export_timestamp}*")
        
        if self.bold_keywords:
            markdown_content.append("*Keywords are bolded in paragraph content*")
        
        markdown_content.append("")
        
        # Process each root tag
        for root_tag in sorted(root_tags, key=lambda x: x['name']):
            self._export_tag_hierarchy(root_tag, markdown_content, tags_dict, level=1)
        
        # Join all content
        full_content = '\n'.join(markdown_content)
        
        # Write to file if specified
        if output_file:
            self.write_to_file(full_content, output_file)
        
        return full_content
    
    def _bold_keywords_in_content(self, content: str, keywords: List[str]) -> str:
        """
        Bold keywords in paragraph content for markdown output.
        
        Args:
            content: The paragraph content
            keywords: List of keywords to bold
            
        Returns:
            Content with keywords wrapped in **bold** markdown syntax
        """
        if not keywords or not self.bold_keywords:
            return content
        
        # Create a copy of content to modify
        bolded_content = content
        
        # Sort keywords by length (longest first) to avoid partial replacements
        sorted_keywords = sorted(keywords, key=len, reverse=True)
        
        for keyword in sorted_keywords:
            # Use word boundaries to match whole words only
            # Case-insensitive matching with word boundaries
            pattern = r'\b' + re.escape(keyword) + r'\b'
            
            def replace_func(match):
                # Preserve the original case of the matched text
                return f"**{match.group()}**"
            
            bolded_content = re.sub(pattern, replace_func, bolded_content, flags=re.IGNORECASE)
        
        return bolded_content
    
    def _export_tag_hierarchy(self, tag_info: Dict, markdown_content: List[str], tags_dict: Dict, level: int = 1):
        """Recursively export tag hierarchy to markdown"""
        # Create heading based on level
        heading_prefix = '#' * (level + 1)  # Start at h2 since h1 is the main title
        markdown_content.append(f"{heading_prefix} {tag_info['name']}")
        
        if tag_info['description']:
            markdown_content.append(f"*{tag_info['description']}*")
        
        markdown_content.append("")
        
        # Process paragraphs for this tag
        for paragraph in tag_info['paragraphs']:
            # Get paragraph content and optionally bold keywords
            content = paragraph['content']
            if paragraph.get('matched_keywords'):
                content = self._bold_keywords_in_content(content, paragraph['matched_keywords'])
            
            # Add paragraph content as bullet point
            markdown_content.append(f"• {content}")
            
            # Add keywords if any
            if paragraph['matched_keywords']:
                keywords_str = ", ".join(paragraph['matched_keywords'])
                markdown_content.append(f"  - **Keywords:** {keywords_str}")
            
            # Add notes if any
            if paragraph['notes'] and paragraph['notes'].strip():
                markdown_content.append(f"  - **Note:** {paragraph['notes'].strip()}")
            
            # Check if paragraph is assigned to other most specific tags (siblings)
            most_specific_tags = paragraph['most_specific_tags']
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
            
            # Add source information with text fragment link
            if paragraph['hyperlink'] and paragraph['hyperlink'].strip():
                # Create text fragment link that jumps to the specific paragraph
                fragment_link = create_paragraph_link(paragraph)
                markdown_content.append(f"  - **Source:** [{paragraph['speaker']} - {paragraph['talk_title']} ({paragraph['conference_date']})]({fragment_link})")
            else:
                markdown_content.append(f"  - **Source:** {paragraph['speaker']} - {paragraph['talk_title']} ({paragraph['conference_date']})")
            markdown_content.append("")
        
        # Process children recursively
        for child_tag in sorted(tag_info['children'], key=lambda x: x['name']):
            self._export_tag_hierarchy(child_tag, markdown_content, tags_dict, level + 1)