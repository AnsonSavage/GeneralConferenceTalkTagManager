"""
Main application file for the Conference Talks Analysis application.
Modular structure with separate pages and components using direct dependency injection.
"""
import streamlit as st
import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.config.settings import APP_TITLE, APP_ICON, DEFAULT_LAYOUT, NAVIGATION_PAGES, SIDEBAR_TIPS
from src.database.database_factory import DatabaseFactory
from src.utils.file_parser import FileParser
from src.utils.text_processor import TextProcessor
from src.utils.search_manager import SearchManager
from src.utils.export_manager import ExportManager
from src.utils.backup_manager import BackupManager
from src.pages.search_and_tag import render_search_and_tag_page
from src.pages.add_tags_to_paragraphs import render_add_tags_page
from src.pages.manage_paragraphs import render_manage_paragraphs_page
from src.pages.manage_talks import render_manage_talks_page
from src.pages.manage_tags import render_manage_tags_page
from src.pages.manage_keywords import render_manage_keywords_page
from src.pages.export import render_export_page
from src.pages.import_data import render_import_page
from src.pages.summary import render_summary_page
from src.pages.backup import render_backup_page


def get_available_databases():
    """Get list of available database files in the current directory."""
    current_dir = Path.cwd()
    db_files = list(current_dir.glob("*.db"))
    return [str(db_file.name) for db_file in db_files]


def render_database_selector():
    """Render database file selector in sidebar."""
    st.sidebar.markdown("### 🗄️ Database Selection")
    
    # Get available databases
    available_dbs = get_available_databases()
    
    # Initialize session state for selected database
    if 'selected_database' not in st.session_state:
        if available_dbs:
            st.session_state.selected_database = available_dbs[0]
        else:
            st.session_state.selected_database = "conference_talks.db"
    
    # Database selection dropdown
    if available_dbs:
        selected_db = st.sidebar.selectbox(
            "Select Database:",
            options=available_dbs,
            index=available_dbs.index(st.session_state.selected_database) if st.session_state.selected_database in available_dbs else 0,
            key="db_selector"
        )
        
        # Update session state if selection changed
        if selected_db != st.session_state.selected_database:
            st.session_state.selected_database = selected_db
            # Clear the cached components when switching
            if 'components' in st.session_state:
                del st.session_state['components']
            st.rerun()
    else:
        st.sidebar.info("No database files found.")
        st.session_state.selected_database = "conference_talks.db"
    
    # Create new database option
    with st.sidebar.expander("➕ Create New Database"):
        new_db_name = st.text_input(
            "Database name:",
            placeholder="my_new_database.db",
            help="Enter a name for the new database file (will add .db extension if not provided)"
        )
        
        if st.button("Create Database", type="primary"):
            if new_db_name:
                # Ensure .db extension
                if not new_db_name.endswith('.db'):
                    new_db_name += '.db'
                
                # Check if file already exists
                if os.path.exists(new_db_name):
                    st.error(f"Database '{new_db_name}' already exists!")
                else:
                    try:
                        # Create new database (this initializes the database file)
                        DatabaseFactory.create_database('sqlite', {'db_path': new_db_name})
                        st.session_state.selected_database = new_db_name
                        # Clear cached components
                        if 'components' in st.session_state:
                            del st.session_state['components']
                        st.success(f"✅ Created database '{new_db_name}'!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating database: {str(e)}")
            else:
                st.warning("Please enter a database name.")
    
    # Show current database info
    current_db = st.session_state.selected_database
    st.sidebar.markdown(f"**Current DB:** `{current_db}`")
    
    # Database file size if it exists
    if os.path.exists(current_db):
        file_size = os.path.getsize(current_db)
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        st.sidebar.caption(f"Size: {size_str}")
    
    # Quick backup button
    if st.sidebar.button("💾 Quick Backup", help="Create a backup of the current database"):
        if os.path.exists(current_db):
            # We need to get the backup manager from components
            components = get_components(current_db)
            backup_manager = components['backup_manager']
            
            with st.spinner("Creating backup..."):
                backup_results = backup_manager.create_backup(current_db)
            
            if backup_results['success']:
                st.sidebar.success("✅ Backup created!")
                st.sidebar.info(f"📁 {backup_results['timestamp']}")
            else:
                st.sidebar.error("❌ Backup failed!")
        else:
            st.sidebar.error("❌ Database not found!")


@st.cache_resource
def get_components(db_path: str, data_path: str = "data/General_Conference_Talks"):
    """Initialize and cache component instances for the selected database file."""
    # Initialize database
    database = DatabaseFactory.create_database('sqlite', {'db_path': db_path})
    
    # Initialize helper classes
    file_parser = FileParser(data_path)
    text_processor = TextProcessor()
    search_manager = SearchManager(database, data_path)
    export_manager = ExportManager(database)
    backup_manager = BackupManager(database)
    
    return {
        'database': database,
        'file_parser': file_parser,
        'text_processor': text_processor,
        'search_manager': search_manager,
        'export_manager': export_manager,
        'backup_manager': backup_manager
    }


def main():
    """Main application function."""
    # Page configuration
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout=DEFAULT_LAYOUT
    )
    
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    # Render database selector
    render_database_selector()
    
    # Get component instances for selected file
    selected_db = st.session_state.selected_database
    components = get_components(selected_db)
    
    # Sidebar navigation
    st.sidebar.markdown("---")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", NAVIGATION_PAGES)
    
    # Route to appropriate page with only needed components
    if page == "🔍 Search & Tag":
        render_search_and_tag_page(components['database'], components['search_manager'])
    elif page == "📝 Add Tags to Paragraphs":
        render_add_tags_page(components['database'])
    elif page == "📄 Manage Paragraphs":
        render_manage_paragraphs_page(components['database'])
    elif page == "📚 Manage Talks":
        render_manage_talks_page(components['database'])
    elif page == "🏷️ Manage Tags":
        render_manage_tags_page(components['database'])
    elif page == "🔤 Manage Keywords":
        render_manage_keywords_page(components['database'])
    elif page == "📤 Export":
        render_export_page(components['database'], components['export_manager'])
    elif page == "📥 Import":
        render_import_page(components['database'])
    elif page == "📊 Summary":
        render_summary_page(components['database'])
    elif page == "💾 Backup":
        render_backup_page(components['database'], components['backup_manager'])
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Tips:**")
    for tip in SIDEBAR_TIPS:
        st.sidebar.markdown(tip)


if __name__ == "__main__":
    main()