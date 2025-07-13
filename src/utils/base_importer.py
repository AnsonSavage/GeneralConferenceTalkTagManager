"""
Base importer class for conference talk database content.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..database.base_database import BaseDatabaseInterface


class BaseImporter(ABC):
    """Base class for all importers."""
    
    def __init__(self, database: BaseDatabaseInterface):
        """Initialize the base importer with a database instance."""
        self.database = database
    
    @abstractmethod
    def import_data(self, file_paths: List[str], merge_mode: bool = False) -> Dict[str, Any]:
        """
        Import data from files into the database.
        
        Args:
            file_paths: List of file paths to import from
            merge_mode: If True, merge with existing data. If False, create new database.
            
        Returns:
            Dictionary containing import results and statistics
        """
        pass
    
    @abstractmethod
    def validate_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Validate that the provided files are compatible with this importer.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Dictionary containing validation results
        """
        pass
    
    def clear_database(self) -> None:
        """Clear all data from the database (for non-merge imports)."""
        # This is a destructive operation - implement with caution
        # For now, we'll implement this in the specific database implementations
        pass