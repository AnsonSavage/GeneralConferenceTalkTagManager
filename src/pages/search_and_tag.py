"""
Search and Tag page module.
"""
import streamlit as st
from typing import Dict, Any
from ..utils.helpers import highlight_keywords, parse_keywords, display_talk_info, clear_session_state_key
from ..database.base_database import BaseDatabaseInterface


def render_search_and_tag_page(database: BaseDatabaseInterface, search_manager) -> None:
    """Render the Search and Tag page."""
    st.header("Search and Tag Paragraphs")
    
    # Keywords input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get existing keywords for suggestions
        existing_keywords = database.get_keywords()
        
        # Text input for keywords
        keywords_input = st.text_input(
            "Enter keywords (comma-separated):",
            placeholder="light, technology, gospel, faith"
        )
        
        # Display existing keywords as suggestions
        if existing_keywords:
            st.write("**Existing keywords:**")
            keywords_display = ", ".join(existing_keywords)
            st.text(keywords_display)
    
    with col2:
        match_whole_words = st.checkbox("Match whole words only", value=True)
        search_button = st.button("🔍 Search", type="primary")
    
    # Handle search
    if search_button and keywords_input:
        keywords = parse_keywords(keywords_input)
        
        # Search files and populate database with matching content
        with st.spinner("Scanning files for keywords..."):
            results = search_manager.search_and_populate_database(keywords, match_whole_words=match_whole_words)
        
        st.success(f"Found {len(results)} paragraphs matching your keywords")
        
        # Store results in session state
        st.session_state.search_results = results
        st.session_state.search_keywords = keywords
    
    # Display search results
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.header("Search Results")
        
        # Get all tags for tagging interface
        all_tags = database.get_all_tags()
        tag_options = {tag['name']: tag['id'] for tag in all_tags}
        
        # Display each paragraph
        for i, result in enumerate(st.session_state.search_results):
            _render_search_result(result, database, tag_options, i)


def _render_search_result(result: Dict[str, Any], database: BaseDatabaseInterface, tag_options: Dict[str, int], index: int) -> None:
    """Render a single search result."""
    with st.expander(f"**{result['talk_title']}** - {result['speaker']} ({result['conference_date']}) - Para {result['paragraph_number']}", expanded=True):
        
        # Talk information
        col1, col2 = st.columns([2, 1])
        
        with col1:
            display_talk_info(result)
        
        with col2:
            # Reviewed status
            reviewed = st.checkbox(
                "Reviewed", 
                value=result['reviewed'], 
                key=f"reviewed_{result['id']}"
            )
            
            if reviewed != result['reviewed']:
                database.mark_paragraph_reviewed(result['id'], reviewed)
                st.rerun()
        
        # Paragraph content
        st.markdown("**Paragraph Content:**")
        
        # Highlight matched keywords
        content = highlight_keywords(result['content'], result['matched_keywords'])
        st.markdown(content)
        
        # Current tags
        current_tags = database.get_paragraph_tags(result['id'])
        if current_tags:
            st.markdown("**Current Tags:**")
            tag_cols = st.columns(len(current_tags))
            for j, tag in enumerate(current_tags):
                with tag_cols[j]:
                    if st.button(f"❌ {tag['name']}", key=f"remove_tag_{result['id']}_{tag['id']}"):
                        database.remove_tag_from_paragraph(result['id'], tag['id'])
                        st.rerun()
        
        # Add new tags
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if tag_options:
                selected_tag = st.selectbox(
                    "Add Tag:",
                    options=[""] + list(tag_options.keys()),
                    key=f"tag_select_{result['id']}"
                )
            else:
                st.info("No tags available. Create tags in the 'Manage Tags' section.")
                selected_tag = None
        
        with col2:
            if selected_tag and st.button("Add Tag", key=f"add_tag_{result['id']}"):
                database.tag_paragraph(result['id'], tag_options[selected_tag])
                # Clear the selection
                clear_session_state_key(f"tag_select_{result['id']}")
                st.success(f"Tag '{selected_tag}' added!")
                st.rerun()
        
        st.divider()