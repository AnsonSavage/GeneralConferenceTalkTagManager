"""
Configuration settings for the Conference Talks Analysis application.
"""
import os
from pathlib import Path

# Application settings
APP_TITLE = "Conference Talks Analysis"
APP_ICON = "📖"
DEFAULT_LAYOUT = "wide"

# Database settings
DEFAULT_DB_PATH = "conference_talks.db"
DEFAULT_DATA_PATH = "data/General_Conference_Talks"

# File paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = PROJECT_ROOT

# Search settings
DEFAULT_MATCH_WHOLE_WORDS = True
MIN_PARAGRAPH_LENGTH = 50

# UI settings
ITEMS_PER_PAGE = 10
MAX_COLUMNS_FOR_DISPLAY = 4
DEFAULT_FILTER_EXPANDED = True

# Navigation pages
NAVIGATION_PAGES = [
    "🔍 Search & Tag",
    "📄 Manage Paragraphs", 
    "📚 Manage Talks",
    "🏷️ Manage Tags",
    "🔤 Manage Keywords",
    "📤 Export",
    "📊 Summary"
]

# Tips for sidebar
SIDEBAR_TIPS = [
    "• Enter keywords to scan conference talks",
    "• Only matching paragraphs are stored in database",
    "• Use specific keywords for better results",
    "• Create hierarchical tags for better organization",
    "• Review paragraphs to track progress"
]