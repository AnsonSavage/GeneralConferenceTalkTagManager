"""
Base exporter class for conference talk database content.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseExporter(ABC):
    """Base class for all exporters."""
    
    def __init__(self):
        """Initialize the base exporter."""
        pass
    
    @abstractmethod
    def export(self, export_data: Dict[str, Any], output_file: str = None) -> str:
        """
        Export the provided data to the specific format.
        
        Args:
            export_data: Dictionary containing all necessary data for export
            output_file: Optional file path to write the content
            
        Returns:
            The generated content as a string
        """
        pass
    
    def write_to_file(self, content: str, output_file: str, encoding: str = 'utf-8') -> None:
        """
        Write content to a file.
        
        Args:
            content: The content to write
            output_file: The file path to write to
            encoding: The file encoding to use
        """
        with open(output_file, 'w', encoding=encoding) as f:
            f.write(content)