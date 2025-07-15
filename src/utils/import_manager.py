"""
Import utilities for conference talk database content.
"""
from typing import List, Dict, Any
from ..database.base_database import BaseDatabaseInterface
from .base_importer import BaseImporter
from .csv_importer import CSVImporter


class ImportManager:
    """Handles importing database content using various importers."""
    
    def __init__(self, database: BaseDatabaseInterface):
        """
        Initialize the import manager.
        
        Args:
            database: The database instance to import into
        """
        self.database = database
    
    def import_with_importer(self, importer: BaseImporter, file_paths: List[str], 
                           merge_mode: bool = False) -> Dict[str, Any]:
        """
        Import database content using the specified importer.
        
        Args:
            importer: The importer instance to use
            file_paths: List of file paths to import from
            merge_mode: If True, merge with existing data. If False, create new database.
            
        Returns:
            Dictionary containing import results and statistics
        """
        return importer.import_data(file_paths, merge_mode)
    
    def import_from_csv(self, file_paths: List[str], merge_mode: bool = False) -> Dict[str, Any]:
        """
        Import database content from CSV files.
        
        Args:
            file_paths: List of CSV file paths to import from
            merge_mode: If True, merge with existing data. If False, create new database.
            
        Returns:
            Dictionary containing import results and statistics
        """
        csv_importer = CSVImporter(self.database)
        return self.import_with_importer(csv_importer, file_paths, merge_mode)
    
    def validate_csv_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Validate CSV files before import.
        
        Args:
            file_paths: List of CSV file paths to validate
            
        Returns:
            Dictionary containing validation results
        """
        csv_importer = CSVImporter(self.database)
        return csv_importer.validate_files(file_paths)
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported import formats.
        
        Returns:
            List of supported format names
        """
        return ['csv']