"""
File parsing utilities for conference talk files.
"""
import os
from typing import Dict


class FileParser:
    """Handles parsing of conference talk text files."""
    
    def __init__(self, data_path: str):
        """
        Initialize the file parser.
        
        Args:
            data_path: Path to the directory containing talk files
        """
        self.data_path = data_path
    
    def parse_talk_file(self, file_path: str) -> Dict:
        """
        Parse a single talk file and return its metadata and content.
        
        Args:
            file_path: Path to the talk file
            
        Returns:
            Dictionary containing talk metadata and content
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        lines = content.split('\n')
        
        # Extract metadata from first 3 lines
        title = lines[0].replace('Title: ', '') if lines[0].startswith('Title: ') else ''
        speaker = lines[1].replace('Speaker: ', '') if lines[1].startswith('Speaker: ') else ''
        url = lines[2].replace('URL: ', '') if lines[2].startswith('URL: ') else ''
        
        # Extract talk body (skip metadata + blank line)
        talk_body = '\n'.join(lines[4:]) if len(lines) > 4 else ''
        
        # Extract year and month from file path
        path_parts = file_path.split(os.sep)
        year = path_parts[-3] if len(path_parts) >= 3 else ''
        month = path_parts[-2] if len(path_parts) >= 2 else ''
        
        # Convert month to conference date
        conference_date = f"{'April' if month == '04' else 'October'} {year}" if year and month else ''
        
        return {
            'title': title,
            'speaker': speaker,
            'url': url,
            'conference_date': conference_date,
            'content': talk_body,
            'file_path': file_path
        }
    
    def get_all_talk_files(self) -> list:
        """
        Get all talk files in the data directory.
        
        Returns:
            List of file paths to talk files
        """
        talk_files = []
        
        if not os.path.exists(self.data_path):
            return talk_files
        
        # Walk through the directory structure
        for root, dirs, files in os.walk(self.data_path):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    talk_files.append(file_path)
        
        return talk_files