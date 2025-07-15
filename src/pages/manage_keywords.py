"""
Manage Keywords page module.
"""
import streamlit as st
from typing import List, Dict, Any
from ..utils.helpers import highlight_keywords, display_talk_info
from ..database.base_database import BaseDatabaseInterface


def render_manage_keywords_page(database: BaseDatabaseInterface) -> None:
    """Render the Manage Keywords page."""
    st.header("Manage Keywords")
    
    st.info("💡 Keywords are automatically added when you search for them. Click on a keyword to see all matching paragraphs.")
    
    # Display existing keywords
    st.subheader("Existing Keywords")
    keywords = database.get_keywords()
    
    if keywords:
        # Check if we're viewing paragraphs for a specific keyword
        if 'viewing_keyword' in st.session_state:
            _render_keyword_paragraphs_view(database)
        else:
            _render_keywords_list(database, keywords)
    else:
        st.info("No keywords added yet. Start by searching for keywords in the '🔍 Search & Tag' section.")


def _render_keyword_paragraphs_view(database: BaseDatabaseInterface) -> None:
    """Render the view showing paragraphs for a specific keyword."""
    keyword = st.session_state.viewing_keyword
    st.subheader(f"Paragraphs matching '{keyword}'")
    
    # Back button
    if st.button("← Back to Keywords List"):
        del st.session_state.viewing_keyword
        st.rerun()
    
    # Get paragraphs for this keyword
    paragraphs = database.get_paragraphs_by_keyword(keyword)
    
    if paragraphs:
        st.write(f"Found {len(paragraphs)} paragraphs")
        
        # Display each paragraph
        for para in paragraphs:
            with st.expander(f"**{para['talk_title']}** - {para['speaker']} ({para['conference_date']}) - Para {para['paragraph_number']}", expanded=False):
                display_talk_info(para)
                
                # Highlight the keyword in the content
                content = highlight_keywords(para['content'], [keyword])
                
                st.markdown("**Paragraph Content:**")
                st.markdown(content)
                
                # Show review status
                if para['reviewed']:
                    st.success(f"✅ Reviewed on {para['review_date']}")
                else:
                    st.warning("⏳ Not reviewed yet")
    else:
        st.info("No paragraphs found for this keyword.")


def _render_keywords_list(database: BaseDatabaseInterface, keywords: List[str]) -> None:
    """Render the list of keywords with view and delete options."""
    st.write("Click on a keyword to see all matching paragraphs:")
    
    # Create columns for keyword display
    cols = st.columns(3)
    for i, keyword in enumerate(keywords):
        with cols[i % 3]:
            # Keyword button and delete button in same row
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button(f"🔍 {keyword}", key=f"view_keyword_{keyword}"):
                    st.session_state.viewing_keyword = keyword
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_keyword_{keyword}", help=f"Delete '{keyword}'"):
                    database.delete_keyword(keyword)
                    st.success(f"Keyword '{keyword}' deleted!")
                    st.rerun()