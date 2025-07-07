"""
Main application file for the Conference Talks Analysis application.
Modular structure with separate pages and components.
"""
import streamlit as st
import sys
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


# Initialize database
@st.cache_resource
def init_database():
    return ConferenceTalksDB()


def main():
    """Main application function."""
    # Page configuration
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout=DEFAULT_LAYOUT
    )
    
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    # Initialize database
    db = init_database()
    
    # Sidebar navigation
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