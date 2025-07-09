"""
Abstract base class for database operations.
This defines the interface that all database implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any


class BaseDatabaseInterface(ABC):
    """Abstract base class defining the interface for conference talks database operations."""
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the database connection.
        
        Args:
            connection_params: Database-specific connection parameters
        """
        self.connection_params = connection_params
    
    @abstractmethod
    def init_database(self) -> None:
        """Initialize the database with required tables and schema."""
        pass
    
    # Talk operations
    @abstractmethod
    def add_talk(self, title: str, speaker: str, conference_date: str, 
                 hyperlink: str, session: str = None) -> int:
        """Add a new talk and return its ID."""
        pass
    
    @abstractmethod
    def add_or_update_talk(self, talk_data: Dict) -> int:
        """Add a talk to the database or return existing ID."""
        pass
    
    @abstractmethod
    def get_talks_summary(self) -> List[Dict]:
        """Get summary of all talks."""
        pass
    
    @abstractmethod
    def get_talks_with_paragraph_counts(self) -> List[Dict]:
        """Get all talks with their paragraph counts."""
        pass
    
    # Paragraph operations
    @abstractmethod
    def add_paragraph(self, talk_id: int, paragraph_number: int, 
                     content: str, matched_keywords: List[str] = None) -> int:
        """Add a paragraph to a talk."""
        pass
    
    @abstractmethod
    def add_or_update_paragraph(self, talk_id: int, paragraph_number: int, 
                               content: str, matched_keywords: List[str]) -> int:
        """Add a paragraph or update its keywords if it already exists."""
        pass
    
    @abstractmethod
    def search_paragraphs(self, keywords: List[str]) -> List[Dict]:
        """Search for paragraphs containing any of the keywords."""
        pass
    
    @abstractmethod
    def get_all_paragraphs_with_filters(self, tag_filter: str = None, keyword_filter: str = None, 
                                       untagged_only: bool = False, reviewed_only: bool = False) -> List[Dict]:
        """Get paragraphs with optional filtering."""
        pass
    
    @abstractmethod
    def get_paragraphs_by_tag(self, tag_id: int) -> List[Dict]:
        """Get all paragraphs that have a specific tag."""
        pass
    
    @abstractmethod
    def mark_paragraph_reviewed(self, paragraph_id: int, reviewed: bool = True) -> None:
        """Mark a paragraph as reviewed."""
        pass
    
    @abstractmethod
    def update_paragraph_notes(self, paragraph_id: int, notes: str) -> None:
        """Update notes for a paragraph."""
        pass
    
    @abstractmethod
    def get_paragraph_with_notes(self, paragraph_id: int) -> Optional[Dict]:
        """Get a paragraph with its notes."""
        pass
    
    @abstractmethod
    def mark_all_paragraphs_not_reviewed(self) -> None:
        """Mark all paragraphs as not reviewed."""
        pass
    
    @abstractmethod
    def get_paragraph_count_for_tag(self, tag_id: int) -> int:
        """Get the number of paragraphs assigned to a specific tag."""
        pass
    
    @abstractmethod
    def get_untagged_paragraphs_summary(self) -> Dict[str, Any]:
        """Get summary statistics for untagged paragraphs."""
        pass
    
    # Tag operations
    @abstractmethod
    def add_tag(self, name: str, description: str = None, parent_tag_id: int = None) -> int:
        """Add a new tag."""
        pass
    
    @abstractmethod
    def get_all_tags(self) -> List[Dict]:
        """Get all tags with their hierarchy."""
        pass
    
    @abstractmethod
    def get_paragraph_tags(self, paragraph_id: int) -> List[Dict]:
        """Get all tags for a paragraph."""
        pass
    
    @abstractmethod
    def get_paragraph_tags_with_hierarchy(self, paragraph_id: int) -> Dict:
        """Get all tags for a paragraph, separating explicit and implicit tags."""
        pass
    
    @abstractmethod
    def tag_paragraph(self, paragraph_id: int, tag_id: int) -> None:
        """Tag a paragraph with a specific tag."""
        pass
    
    @abstractmethod
    def tag_paragraph_with_hierarchy(self, paragraph_id: int, tag_id: int) -> None:
        """Tag a paragraph and all its parent tags."""
        pass
    
    @abstractmethod
    def remove_tag_from_paragraph(self, paragraph_id: int, tag_id: int) -> None:
        """Remove a tag from a paragraph."""
        pass
    
    @abstractmethod
    def remove_tag_from_all_paragraphs(self, tag_id: int) -> int:
        """Remove a tag from all paragraphs and return the number of paragraphs affected."""
        pass
    
    @abstractmethod
    def update_tag(self, tag_id: int, name: str = None, description: str = None, 
                   parent_tag_id: int = None) -> None:
        """Update a tag's properties."""
        pass
    
    @abstractmethod
    def delete_tag(self, tag_id: int) -> None:
        """Delete a tag and update its children to have no parent."""
        pass
    
    @abstractmethod
    def search_tags(self, query: str) -> List[Dict]:
        """Search for tags by name."""
        pass
    
    @abstractmethod
    def get_tag_hierarchy(self, tag_id: int) -> List[int]:
        """Get all parent tags for a given tag (including the tag itself)."""
        pass
    
    @abstractmethod
    def get_tag_usage_statistics(self) -> List[Dict]:
        """Get usage statistics for all tags."""
        pass
    
    @abstractmethod
    def get_top_tags_by_usage(self, limit: int = 10) -> List[Dict]:
        """Get top tags by paragraph count."""
        pass
    
    # Keyword operations
    @abstractmethod
    def add_keywords(self, keywords: List[str]) -> None:
        """Add keywords to the keywords table."""
        pass
    
    @abstractmethod
    def get_keywords(self) -> List[str]:
        """Get all keywords."""
        pass
    
    @abstractmethod
    def delete_keyword(self, keyword: str) -> None:
        """Delete a keyword and all its associations."""
        pass
    
    @abstractmethod
    def get_paragraphs_by_keyword(self, keyword: str) -> List[Dict]:
        """Get all paragraphs that match a specific keyword."""
        pass
    
    @abstractmethod
    def add_paragraph_keyword_associations(self, paragraph_id: int, keywords: List[str]) -> None:
        """Add keyword associations for a paragraph."""
        pass
    
    @abstractmethod
    def get_keyword_usage_statistics(self) -> List[Dict]:
        """Get usage statistics for all keywords."""
        pass
    
    # Statistics and metadata operations
    @abstractmethod
    def get_export_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for export preview."""
        pass
    
    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """Get database metadata and table information."""
        pass