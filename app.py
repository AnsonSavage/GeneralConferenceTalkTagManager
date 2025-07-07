"""
Main application file for the Conference Talks Analysis application.
Modular structure with separate pages and components.
"""
import streamlit as st
import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.config.settings import APP_TITLE, APP_ICON, DEFAULT_LAYOUT, NAVIGATION_PAGES, SIDEBAR_TIPS
from src.database import ConferenceTalksDB
from src.pages.search_and_tag import render_search_and_tag_page
from src.pages.add_tags_to_paragraphs import render_add_tags_page
from src.pages.manage_paragraphs import render_manage_paragraphs_page
from src.pages.manage_talks import render_manage_talks_page
from src.pages.manage_tags import render_manage_tags_page
from src.pages.manage_keywords import render_manage_keywords_page
from src.pages.export import render_export_page
from src.pages.summary import render_summary_page


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
            # Clear the cached database when switching
            if 'database_instance' in st.session_state:
                del st.session_state['database_instance']
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
                        # Create new database
                        new_db = ConferenceTalksDB(db_path=new_db_name)
                        st.session_state.selected_database = new_db_name
                        # Clear cached database
                        if 'database_instance' in st.session_state:
                            del st.session_state['database_instance']
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


# Initialize database with selected file
@st.cache_resource
def get_database_instance(db_path: str):
    """Get database instance for the selected database file."""
    return ConferenceTalksDB(db_path=db_path)


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
    
    # Get database instance for selected file
    selected_db = st.session_state.selected_database
    db = get_database_instance(selected_db)
    
    # Sidebar navigation
    st.sidebar.markdown("---")
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", NAVIGATION_PAGES)
    
    # Route to appropriate page
    if page == "🔍 Search & Tag":
        render_search_and_tag_page(db)
    elif page == "📝 Add Tags to Paragraphs":
        render_add_tags_page(db)
    elif page == "📄 Manage Paragraphs":
        render_manage_paragraphs_page(db)
    elif page == "📚 Manage Talks":
        render_manage_talks_page(db)
    elif page == "🏷️ Manage Tags":
        render_manage_tags_page(db)
    elif page == "🔤 Manage Keywords":
        render_manage_keywords_page(db)
    elif page == "📤 Export":
        render_export_page(db)
    elif page == "📊 Summary":
        render_summary_page(db)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Tips:**")
    for tip in SIDEBAR_TIPS:
        st.sidebar.markdown(tip)


if __name__ == "__main__":
    main()