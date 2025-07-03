"""
Manage Paragraphs page module.
"""
import streamlit as st
from typing import Dict, Any
from ..components.ui_components import FlashcardNavigator, TagSelector, FilterControls
from ..utils.helpers import highlight_keywords, display_hierarchical_tags


def render_manage_paragraphs_page(db) -> None:
    """Render the Manage Paragraphs page with flashcard interface."""
    st.header("Manage Paragraphs - Flashcard View")
    
    # Filter controls
    filter_controls = FilterControls(db)
    filters = filter_controls.render_paragraph_filters()
    
    # Load filtered paragraphs
    paragraphs = db.get_all_paragraphs_with_filters(
        tag_filter=filters['tag_filter'],
        keyword_filter=filters['keyword_filter'],
        untagged_only=filters['untagged_only']
    )
    
    if paragraphs:
        # Initialize flashcard navigator
        navigator = FlashcardNavigator(paragraphs, "current_paragraph_index")
        
        # Render navigation controls
        navigator.render_navigation()
        
        # Get current paragraph
        current_paragraph = navigator.get_current_item()
        
        if current_paragraph:
            st.divider()
            _render_paragraph_flashcard(current_paragraph, db, filters['keyword_filter'])
    else:
        st.info("No paragraphs found with the current filters. Try adjusting your filter criteria.")


def _render_paragraph_flashcard(paragraph: Dict[str, Any], db, keyword_filter: str = None) -> None:
    """Render a single paragraph as a flashcard."""
    with st.container():
        # Talk information header
        st.markdown(f"### {paragraph['talk_title']}")
        st.markdown(f"**Speaker:** {paragraph['speaker']} | **Date:** {paragraph['conference_date']} | **Paragraph:** {paragraph['paragraph_number']}")
        
        if paragraph['hyperlink']:
            st.markdown(f"[🔗 View Talk]({paragraph['hyperlink']})")
        
        # Paragraph content
        st.markdown("---")
        
        # Highlight keywords if keyword filter is active
        content = paragraph['content']
        if keyword_filter and keyword_filter != "All Keywords":
            content = highlight_keywords(content, [keyword_filter])
        
        st.markdown(content)
        st.markdown("---")
        
        # Display tags with hierarchy
        display_hierarchical_tags(paragraph['id'], db)
        
        # Tag management interface
        st.markdown("**Add Tags:**")
        
        tag_selector = TagSelector(db, paragraph['id'])
        tag_selector.render_tag_search("flashcard")
        
        # Handle popups
        tag_selector.render_tag_creation_popup("flashcard")
        tag_selector.render_all_tags_popup("flashcard")