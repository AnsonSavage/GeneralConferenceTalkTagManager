# Conference Talks Analysis - Modular Architecture

A Streamlit application for analyzing and tagging General Conference talks with a clean, modular codebase.

## 📁 Project Structure

```
GeneralConferenceTalkTagManager/
├── app.py                   # Main Streamlit application
├── conference_talks.db      # SQLite database
├── data/                    # Conference talks text files
│   └── General_Conference_Talks/
├── src/                     # Modular source code
│   ├── config/              # Configuration settings
│   │   ├── __init__.py
│   │   └── settings.py      # App settings and constants
│   ├── database/            # Database layer
│   │   ├── __init__.py
│   │   └── conference_talks_db.py  # Database operations
│   ├── components/          # Reusable UI components
│   │   ├── __init__.py
│   │   └── ui_components.py # Flashcard navigator, tag selector, etc.
│   ├── pages/               # Individual page modules
│   │   ├── search_and_tag.py       # Search & Tag page
│   │   ├── manage_paragraphs.py    # Flashcard interface
│   │   ├── manage_talks.py         # Talks overview
│   │   ├── manage_tags.py          # Tag management
│   │   ├── manage_keywords.py      # Keyword management
│   │   ├── add_tags_to_paragraphs.py # Tagging utility
│   │   ├── export.py               # Export functionality
│   │   └── summary.py              # Project summary
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── helpers.py       # Common helper functions
└── utilities/               # External utilities
    └── general_conference_talk_scraper.py
```

## 🚀 Quick Start

Run the main application:
```bash
streamlit run app.py
```

## 🏗️ Architecture Benefits

### **Separation of Concerns**
- **Pages**: Each page is self-contained with its own module
- **Components**: Reusable UI components (flashcard navigation, tag selectors)
- **Database**: Isolated database operations
- **Utils**: Common helper functions
- **Config**: Centralized configuration management

### **Maintainability**
- **Single Responsibility**: Each file has a clear, focused purpose
- **Easy Testing**: Individual modules can be tested in isolation
- **Code Reuse**: Components and utilities are shared across pages
- **Configuration Management**: All settings in one place

### **Scalability**
- **Easy to Add Features**: New pages are simple to add
- **Component Library**: Build up reusable UI components
- **Plugin Architecture**: Easy to extend functionality

## 📄 Page Modules

### `search_and_tag.py`
- Keyword search interface
- Search result display with tagging
- Keyword highlighting

### `manage_paragraphs.py`
- Flashcard-style navigation through paragraphs
- Advanced filtering (tags, keywords, review status)
- Quick tagging interface with hierarchy support
- Tag creation on-the-fly

### `manage_talks.py`
- Overview of all talks in database
- Keyword usage metrics
- Talk statistics

### `manage_tags.py`
- Hierarchical tag creation and editing
- Tag relationship management
- Safe deletion with dependency checking

### `manage_keywords.py`
- View all keywords and their usage
- Click to see paragraphs matching each keyword
- Keyword deletion

### `add_tags_to_paragraphs.py`
- Interface to add tags to selected paragraphs
- Supports hierarchical tag selection
- Batch processing of paragraphs

### `export.py`
- Export tagged paragraphs to CSV
- Customizable export fields
- Preview before export

### `summary.py`
- Project overview and statistics
- Progress tracking
- Recent talks display

## 🧩 Reusable Components

### `FlashcardNavigator`
- Navigation through any list of items
- Previous/Next/Random/Jump functionality
- Session state management

### `TagSelector`
- Tag search and selection interface
- Hierarchical tag creation
- Popup management for tag operations

### `FilterControls`
- Paragraph filtering interface
- Tag and keyword filter options

## 🛠️ Utility Functions

### Content Processing
- `highlight_keywords()`: Highlight search terms in text
- `parse_keywords()`: Parse comma-separated keyword input

### UI Helpers
- `display_hierarchical_tags()`: Show explicit vs implicit tags
- `display_talk_info()`: Consistent talk information display
- Session state management functions

## ⚙️ Configuration

All application settings are centralized in `src/config/settings.py`:
- Application metadata (title, icon, layout)
- Database and file paths
- UI settings (pagination, column counts)
- Navigation structure
- Default values

## 🔄 Migration Guide

The modular version (`app_modular.py`) provides the same functionality as the original `app.py` with improved organization:

1. **All existing features preserved**
2. **Same user interface and workflow**
3. **Enhanced performance through better code organization**
4. **Easier maintenance and future development**

## 🧪 Development

### Adding a New Page
1. Create a new file in `src/pages/`
2. Implement a `render_[page_name]_page(db)` function
3. Add the page to `NAVIGATION_PAGES` in `src/config/settings.py`
4. Add the route in `app_modular.py`

### Creating Reusable Components
1. Add component class to `src/components/ui_components.py`
2. Update `src/components/__init__.py` exports
3. Import and use in page modules

### Adding Utility Functions
1. Add functions to `src/utils/helpers.py`
2. Update `src/utils/__init__.py` exports
3. Import where needed

## 📊 Features

- **Flashcard Interface**: Navigate through paragraphs efficiently
- **Hierarchical Tagging**: Automatic parent tag inheritance
- **Smart Filtering**: Filter by tags, keywords, review status
- **Keyword Highlighting**: Visual emphasis on search terms
- **Progress Tracking**: Monitor review completion
- **Tag Management**: Full CRUD operations with relationship management

## 🎯 Best Practices Implemented

- **DRY Principle**: No code duplication
- **Single Responsibility**: Each module has one clear purpose
- **Consistent Interfaces**: Standardized function signatures
- **Error Handling**: Graceful error management
- **Documentation**: Comprehensive docstrings
- **Type Hints**: Better code clarity and IDE support