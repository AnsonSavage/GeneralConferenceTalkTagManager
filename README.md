# Conference Talks Analysis - Service-Oriented Architecture

A Streamlit application for analyzing and tagging General Conference talks with a clean, service-oriented architecture following single responsibility principles.

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
│   ├── database/            # Database layer (Pure CRUD operations)
│   │   ├── __init__.py
│   │   ├── base_database.py        # Database interface definition
│   │   ├── conference_talks_db.py  # SQLite implementation
│   │   └── database_factory.py     # Database factory pattern
│   ├── services/            # Service layer (Business logic orchestration)
│   │   ├── __init__.py
│   │   └── conference_talks_service.py # Main service coordinator
│   ├── utils/               # Helper classes (Specialized responsibilities)
│   │   ├── __init__.py
│   │   ├── file_parser.py           # File parsing operations
│   │   ├── text_processor.py        # Text processing operations
│   │   ├── search_manager.py        # Search and population workflows
│   │   ├── export_manager.py        # Export functionality
│   │   └── helpers.py               # Common utility functions
│   ├── components/          # Reusable UI components
│   │   ├── __init__.py
│   │   └── ui_components.py # Flashcard navigator, tag selector, etc.
│   └── pages/               # Individual page modules
│       ├── search_and_tag.py       # Search & Tag page
│       ├── manage_paragraphs.py    # Flashcard interface
│       ├── manage_talks.py         # Talks overview
│       ├── manage_tags.py          # Tag management
│       ├── manage_keywords.py      # Keyword management
│       ├── add_tags_to_paragraphs.py # Tagging utility
│       ├── export.py               # Export functionality
│       └── summary.py              # Project summary
└── utilities/               # External utilities
    └── general_conference_talk_scraper.py
```

## 🚀 Quick Start

Run the main application:
```bash
streamlit run app.py
```

## 🏗️ Service-Oriented Architecture

### **Single Responsibility Principle**
Each component has one clear, focused responsibility:

#### **Database Layer** (`src/database/`)
- **Pure CRUD operations only**
- **`base_database.py`**: Clean interface definition
- **`conference_talks_db.py`**: SQLite implementation (database operations only)
- **`database_factory.py`**: Factory pattern for database creation

#### **Helper Classes** (`src/utils/`)
- **`file_parser.py`**: Handles parsing conference talk text files
- **`text_processor.py`**: Manages text processing (paragraph splitting, keyword matching)
- **`search_manager.py`**: Coordinates file scanning and database population
- **`export_manager.py`**: Handles markdown export with tag hierarchy

#### **Service Layer** (`src/services/`)
- **`conference_talks_service.py`**: Orchestrates all components
- **Provides unified API** to the UI layer
- **Delegates specialized tasks** to appropriate helper classes

#### **UI Layer** (`src/pages/`, `src/components/`)
- **Uses service layer only** - no direct database access
- **Focused on user interaction** and presentation

### **Architecture Benefits**

#### **Maintainability**
- Changes to file parsing don't affect database code
- Database changes don't affect text processing
- Each class can be tested independently

#### **Flexibility** 
- Easy to swap database implementations (PostgreSQL, MongoDB, etc.)
- Text processing algorithms can be changed without affecting other components
- Export formats can be added without touching core logic

#### **Testability**
- Each component can be unit tested in isolation
- Mock implementations can be easily created
- Clear interfaces make testing straightforward

## 🔧 Component Responsibilities

### Database Layer (Pure CRUD)
```python
# Only handles database operations
service.add_talk(title, speaker, date, url)
service.get_talks_summary()
service.add_paragraph(talk_id, content, keywords)
service.tag_paragraph(paragraph_id, tag_id)
```

### File Processing
```python
# Handles file parsing
service.parse_talk_file(file_path)
service.get_all_talk_files()
```

### Text Processing
```python
# Handles text analysis
service.split_into_paragraphs(content)
service.find_keyword_matches(text, keywords)
```

### Search Coordination
```python
# Coordinates search workflows
service.scan_for_keywords(keywords)
service.search_and_populate_database(keywords)
```

### Export Operations
```python
# Handles export functionality
service.export_to_markdown(output_file)
```

## 📄 Page Modules

All page modules now use the **service layer** instead of direct database access:

### `search_and_tag.py`
- Uses `service.search_and_populate_database()` for file scanning
- Uses `service.get_keywords()` for keyword suggestions
- Delegates all database operations to service layer

### `manage_paragraphs.py`
- Uses `service.get_all_paragraphs_with_filters()` for filtering
- Uses `service.tag_paragraph()` for tagging operations
- Clean separation between UI logic and data operations

### `manage_tags.py`
- Uses `service.add_tag()`, `service.update_tag()`, `service.delete_tag()`
- Hierarchical tag operations through service layer
- No direct database queries in UI code

### `export.py`
- Uses `service.export_to_markdown()` for export functionality
- Uses `service.get_export_statistics()` for preview data
- Export logic completely separated from UI presentation

## 🧩 Service Layer API

The `ConferenceTalksService` provides a unified interface:

```python
# Initialize service (coordinates all components)
service = ConferenceTalksService(db_path="talks.db", data_path="data/")

# Database operations (delegated to database layer)
service.add_talk(title, speaker, date, url)
service.get_talks_summary()
service.search_paragraphs(keywords)

# File operations (delegated to file parser)
service.parse_talk_file(file_path)
service.get_all_talk_files()

# Text processing (delegated to text processor)
service.split_into_paragraphs(content)
service.find_keyword_matches(text, keywords)

# Search workflows (delegated to search manager)
service.scan_for_keywords(keywords)
service.search_and_populate_database(keywords)

# Export operations (delegated to export manager)
service.export_to_markdown(output_file)
```

## 🔄 Migration from Monolithic Architecture

### Before (Monolithic Database Class)
- Single large class handling database, file parsing, text processing, and export
- Difficult to test individual components
- Changes to one feature could break others
- Hard to extend with new functionality

### After (Service-Oriented Architecture)
- **Database classes**: Pure CRUD operations only
- **Helper classes**: Specialized single responsibilities
- **Service layer**: Orchestrates all components
- **Easy to test**: Each component is independent
- **Easy to extend**: Add new helper classes or swap implementations

## ⚙️ Configuration

All application settings are centralized in `src/config/settings.py`:
- Application metadata (title, icon, layout)
- Navigation structure and page organization
- Default database and file paths
- UI settings and constants

## 🧪 Development

### Adding New Functionality
1. **Database operations**: Add methods to database interface and implementation
2. **File processing**: Extend `FileParser` class
3. **Text processing**: Extend `TextProcessor` class
4. **Search workflows**: Extend `SearchManager` class
5. **Export formats**: Extend `ExportManager` class
6. **UI features**: Add page modules or UI components

### Testing Strategy
- **Unit tests**: Test each helper class independently
- **Integration tests**: Test service layer coordination
- **UI tests**: Test page modules with mock service layer

### Best Practices Implemented
- **Single Responsibility Principle**: Each class has one clear purpose
- **Dependency Injection**: Service layer coordinates dependencies
- **Interface Segregation**: Clean interfaces between layers
- **Open/Closed Principle**: Easy to extend without modifying existing code

## 📊 Features

- **Flashcard Interface**: Navigate through paragraphs efficiently
- **Hierarchical Tagging**: Automatic parent tag inheritance
- **Smart Filtering**: Filter by tags, keywords, review status
- **Keyword Highlighting**: Visual emphasis on search terms
- **Progress Tracking**: Monitor review completion
- **Markdown Export**: Export with tag hierarchy organization
- **Database Abstraction**: Support for multiple database backends

## 🎯 Architecture Principles

✅ **Single Responsibility**: Each class has one reason to change  
✅ **Separation of Concerns**: Database, business logic, and UI are separate  
✅ **Dependency Inversion**: UI depends on abstractions, not concrete implementations  
✅ **Open/Closed**: Easy to extend without modifying existing code  
✅ **Interface Segregation**: Clean, focused interfaces between components