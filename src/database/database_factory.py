"""
Database factory for creating database instances.
"""
from typing import Dict, Any
from .base_database import BaseDatabaseInterface
from .sqlite_database import SQLiteConferenceTalksDB


class DatabaseFactory:
    """Factory class for creating database instances based on configuration."""
    
    @staticmethod
    def create_database(db_type: str = "sqlite", connection_params: Dict[str, Any] = None) -> BaseDatabaseInterface:
        """
        Create a database instance based on the specified type.
        
        Args:
            db_type: Type of database to create ("sqlite", etc.)
            connection_params: Database-specific connection parameters
            
        Returns:
            Database instance implementing BaseDatabaseInterface
            
        Raises:
            ValueError: If unsupported database type is specified
        """
        if connection_params is None:
            connection_params = {}
            
        if db_type.lower() == "sqlite":
            return SQLiteConferenceTalksDB(connection_params)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @staticmethod
    def create_sqlite_database(db_path: str = "conference_talks.db") -> BaseDatabaseInterface:
        """
        Convenience method to create an SQLite database instance.
        
        Args:
            db_path: Path to the SQLite database file
            
        Returns:
            SQLite database instance
        """
        return SQLiteConferenceTalksDB({
            'db_path': db_path
        })


# Create a default instance
def get_database(db_path: str = "conference_talks.db") -> BaseDatabaseInterface:
    """
    Get a default database instance.
    
    Args:
        db_path: Path to the database file
        
    Returns:
        Database instance
    """
    return DatabaseFactory.create_sqlite_database(db_path)