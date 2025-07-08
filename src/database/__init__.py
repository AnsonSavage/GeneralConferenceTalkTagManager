"""
Database module initialization.
"""
from .base_database import BaseDatabaseInterface
from .conference_talks_db import SQLiteConferenceTalksDB
from .database_factory import DatabaseFactory, get_database

# For backward compatibility
ConferenceTalksDB = SQLiteConferenceTalksDB

__all__ = ['BaseDatabaseInterface', 'SQLiteConferenceTalksDB', 'ConferenceTalksDB', 'DatabaseFactory', 'get_database']