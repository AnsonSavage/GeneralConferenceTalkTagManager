"""
Reusable UI components for the Conference Talks Analysis application.

This module provides backward compatibility by importing all UI components
from their individual files.
"""

# Import all components from their separate files
from .flashcard_navigator import FlashcardNavigator
from .tag_selector import TagSelector
from .filter_controls import FilterControls

# Re-export for backward compatibility
__all__ = [
    'FlashcardNavigator',
    'TagSelector', 
    'FilterControls'
]