# Conference Talks Analysis Tool

A Streamlit application for analyzing General Conference talks, finding paragraphs with specific keywords, and organizing them with tags.

## Features

- **Search Functionality**: Search paragraphs across multiple talks using keywords
- **Tagging System**: Create hierarchical tags and apply them to paragraphs
- **Talk Management**: Add and manage conference talks with metadata
- **Review Tracking**: Mark paragraphs as reviewed to track progress
- **SQLite Database**: All data stored locally in a SQLite database

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database with Sample Data

```bash
python sample_data.py
```

This will create a SQLite database (`conference_talks.db`) with sample talks, keywords, and tags.

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage Guide

### 1. Search & Tag (Main Feature)
- Enter keywords separated by commas
- Click "Search" to find matching paragraphs
- Review each paragraph and add tags
- Mark paragraphs as reviewed when done

### 2. Manage Talks
- Add new talks with title, speaker, date, and hyperlink
- View summary of all talks and their paragraph counts

### 3. Manage Tags
- Create hierarchical tags (parent/child relationships)
- Add descriptions to tags for better organization

### 4. Manage Keywords
- Add new keywords to expand your search vocabulary
- View all existing keywords

### 5. Summary
- View project statistics
- Track review progress
- See recent talks

## Database Schema

The application uses SQLite with the following tables:

- **talks**: Conference talk metadata (title, speaker, date, hyperlink)
- **paragraphs**: Individual paragraphs with content and matched keywords
- **tags**: Hierarchical tagging system
- **paragraph_tags**: Many-to-many relationship between paragraphs and tags
- **keywords**: Searchable keywords
- **search_sessions**: Track search history

## Adding Your Own Data

### Method 1: Through the Interface
1. Go to "Manage Talks" tab
2. Use "Add New Talk" form
3. Then manually add paragraphs (you'll need to modify the code to add a paragraph management interface)

### Method 2: Programmatically
```python
from database import ConferenceTalksDB

db = ConferenceTalksDB()

# Add a talk
talk_id = db.add_talk(
    title="Your Talk Title",
    speaker="Speaker Name",
    conference_date="April 2024",
    hyperlink="https://example.com/talk",
    session="General Conference"
)

# Add paragraphs
db.add_paragraph(
    talk_id=talk_id,
    paragraph_number=1,
    content="Your paragraph content here...",
    matched_keywords=["keyword1", "keyword2"]
)
```

## Customization

### Adding New Features
- **Bulk Import**: Add CSV/Excel import functionality
- **Export**: Add export to different formats
- **Advanced Search**: Add boolean operators, phrase matching
- **Analytics**: Add charts and statistics
- **Collaboration**: Add user management and sharing

### Database Extensions
- **Paragraph Linking**: Connect related paragraphs
- **Confidence Scoring**: Rate keyword matches
- **Notes**: Add personal notes to paragraphs
- **Categories**: Group talks by topics

## File Structure

```
conference_talks_analysis/
├── app.py              # Main Streamlit application
├── database.py         # Database operations and schema
├── sample_data.py      # Sample data population script
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── conference_talks.db # SQLite database (created when you run the app)
```

## Tips for Effective Use

1. **Start with Keywords**: Build a comprehensive keyword list before searching
2. **Create Tag Hierarchy**: Use parent/child tags for better organization
3. **Regular Reviews**: Mark paragraphs as reviewed to track progress
4. **Consistent Tagging**: Develop consistent tagging conventions
5. **Backup Database**: Regular backup of your SQLite file

## Troubleshooting

### Database Issues
- If database gets corrupted, delete `conference_talks.db` and run `python sample_data.py` again
- Check file permissions if you get write errors

### Performance
- For large datasets (1000+ talks), consider adding more database indexes
- Use specific keywords rather than very broad terms

### Interface Issues
- Refresh the page if the interface becomes unresponsive
- Check browser console for JavaScript errors

## Future Enhancements

- [ ] Bulk import from CSV/Excel
- [ ] Advanced search with boolean operators
- [ ] Export functionality (PDF, Word, CSV)
- [ ] Analytics dashboard
- [ ] Mobile-responsive design
- [ ] Multi-user support
- [ ] Cloud synchronization
- [ ] API endpoints for external integrations

## Support

If you encounter issues:
1. Check the console output for error messages
2. Verify your Python and package versions
3. Ensure SQLite is properly installed
4. Check file permissions in the working directory