# General Conference Talk Tag Manager

A Streamlit application for tagging General Conference talks.

## Known issues:
* The delete backup button doesn't work
* When a new database is selected, the page router rerouts to the home page
* if you delete a search term, it won't remove paragraphs that only had that search term
* It's not very clear ot the user that paragraphs are added to the database via search keywords. This is a bit unintuitive and is kind of specific to our usecase.
* It's also not certain whether the database will add additional paragraphs if an existing keyword is used in the search


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

## 🧪 Testing

The project includes a comprehensive test suite with both unit and integration tests that verify the application's core functionality.

### Running Tests

```bash
# Run all tests (recommended)
python run_tests.py --all

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration
```

### Test Structure

```
tests/
├── unit/                           # Unit tests for individual components
│   ├── test_csv_basic.py              # CSV functionality tests
│   └── test_csv_import_export.py      # Database operations tests
├── integration/                    # Integration tests for complete workflows
│   ├── test_standalone_workflow.py    # End-to-end application workflow test
│   └── test_database_merge.py         # Database merging functionality test
└── dummy_data/                     # Test data for integration tests
    └── General_Conference_Talks/      # Sample conference talks from 2001, 2024-2025
```

### Integration Test Details

#### Simple Workflow Integration Test
Tests the core application workflow that users follow:

1. **🔍 Keyword Search**: Searches dummy conference talks for specific keywords (`faith`, `Christ`, `testimony`)
2. **📥 Selective Import**: Only imports talks and paragraphs containing the search keywords (mirrors real user behavior)
3. **🏷️ Tagging**: Creates meaningful tags and applies them to relevant paragraphs based on content
4. **📤 Export Testing**: Validates markdown export functionality
5. **✅ Verification**: Confirms all data is properly stored and accessible

**Expected Results**: ~237 talks, ~2,265 paragraphs containing keywords

#### Database Merge Integration Test
Tests the scenario where two separate databases need to be merged:

1. **📊 Data Splitting**: Divides dummy data into two subsets by year (2001 vs 2024-2025)
2. **🔍 Keyword Filtering**: Each database searches for keywords (`faith`, `Christ`) in its subset
3. **📤 CSV Export**: Exports both databases to CSV format
4. **📥 Merge Import**: Imports both CSV sets into a new merged database
5. **✅ Verification**: Confirms all data from both sources is preserved with proper deduplication

**Expected Results**: Successfully merged database with all talks, paragraphs, and tags from both sources

### Test Results

When tests pass, you'll see output like:
```
🎉 ALL TESTS PASSED!
✅ Unit Tests: 9 tests passed
✅ Integration Tests: 2 tests passed
```

### Development Testing

For development and debugging, you can run individual test files:

```bash
# Run specific unit test
python -m pytest tests/unit/test_csv_basic.py -v

# Run integration test directly
python tests/integration/test_standalone_workflow.py
python tests/integration/test_database_merge.py
```

### Test Data

The integration tests use a subset of dummy conference talk data located in `tests/dummy_data/General_Conference_Talks/`. This data includes:
- Sample talks from 2001, 2024, and 2025
- Realistic talk structure with titles, speakers, and content
- Content containing the test keywords used in integration tests

---
