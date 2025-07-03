"""
Utility functions for the Conference Talks Analysis application.
"""
import streamlit as st
import random
from typing import List, Dict, Any


def highlight_keywords(content: str, keywords: List[str]) -> str:
    """
    Highlight keywords in content with red text.
    
    Args:
        content: The text content to highlight
        keywords: List of keywords to highlight
        
    Returns:
        Content with highlighted keywords
    """
    highlighted_content = content
    for keyword in keywords:
        highlighted_content = highlighted_content.replace(
            keyword, 
            f"**:red[{keyword}]**"
        )
        highlighted_content = highlighted_content.replace(
            keyword.capitalize(), 
            f"**:red[{keyword.capitalize()}]**"
        )
    return highlighted_content


def parse_keywords(keywords_input: str) -> List[str]:
    """
    Parse keywords from user input.
    
    Args:
        keywords_input: Comma-separated string of keywords
        
    Returns:
        List of cleaned keywords
    """
    return [k.strip() for k in keywords_input.split(",") if k.strip()]


def get_random_index(max_index: int) -> int:
    """
    Get a random index within the given range.
    
    Args:
        max_index: Maximum index value (exclusive)
        
    Returns:
        Random index
    """
    return random.randint(0, max_index - 1)


def display_paragraph_tags(paragraph_id: int, db, removable: bool = True) -> None:
    """
    Display tags for a paragraph with optional remove buttons.
    
    Args:
        paragraph_id: ID of the paragraph
        db: Database instance
        removable: Whether to show remove buttons
    """
    current_tags = db.get_paragraph_tags(paragraph_id)
    if current_tags:
        st.markdown("**Current Tags:**")
        tag_cols = st.columns(len(current_tags))
        for j, tag in enumerate(current_tags):
            with tag_cols[j]:
                if removable and st.button(f"❌ {tag['name']}", key=f"remove_tag_{paragraph_id}_{tag['id']}"):
                    db.remove_tag_from_paragraph(paragraph_id, tag['id'])
                    st.rerun()
                elif not removable:
                    st.write(f"🏷️ {tag['name']}")


def display_hierarchical_tags(paragraph_id: int, db) -> None:
    """
    Display tags with hierarchy (explicit vs implicit).
    
    Args:
        paragraph_id: ID of the paragraph
        db: Database instance
    """
    tag_data = db.get_paragraph_tags_with_hierarchy(paragraph_id)
    
    if tag_data['explicit'] or tag_data['implicit']:
        st.markdown("**Current Tags:**")
        
        # Display explicit tags (removable)
        if tag_data['explicit']:
            st.markdown("*Explicit tags:*")
            cols = st.columns(len(tag_data['explicit']))
            for i, tag in enumerate(tag_data['explicit']):
                with cols[i]:
                    if st.button(f"❌ {tag['name']}", key=f"remove_explicit_{paragraph_id}_{tag['id']}"):
                        db.remove_tag_from_paragraph(paragraph_id, tag['id'])
                        db.update_paragraph_reviewed_status()
                        st.rerun()
        
        # Display implicit tags (grayed out)
        if tag_data['implicit']:
            st.markdown("*Implicit tags (from parent hierarchy):*")
            cols = st.columns(len(tag_data['implicit']))
            for i, tag in enumerate(tag_data['implicit']):
                with cols[i]:
                    st.markdown(f"🔗 :gray[{tag['name']}]")
    else:
        st.info("No tags assigned to this paragraph yet.")


def display_talk_info(paragraph_data: Dict[str, Any]) -> None:
    """
    Display talk information in a consistent format.
    
    Args:
        paragraph_data: Dictionary containing talk information
    """
    st.markdown(f"**Talk:** [{paragraph_data['talk_title']}]({paragraph_data['hyperlink']})")
    st.markdown(f"**Speaker:** {paragraph_data['speaker']}")
    st.markdown(f"**Date:** {paragraph_data['conference_date']}")
    if paragraph_data.get('session'):
        st.markdown(f"**Session:** {paragraph_data['session']}")


def get_navigation_state(key: str, default: int = 0) -> int:
    """
    Get navigation state from session state.
    
    Args:
        key: Session state key
        default: Default value if key doesn't exist
        
    Returns:
        Navigation state value
    """
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def update_navigation_state(key: str, value: int) -> None:
    """
    Update navigation state in session state.
    
    Args:
        key: Session state key
        value: New value to set
    """
    st.session_state[key] = value


def clear_session_state_key(key: str) -> None:
    """
    Clear a specific key from session state.
    
    Args:
        key: Session state key to clear
    """
    if key in st.session_state:
        del st.session_state[key]


def show_success_message(message: str) -> None:
    """
    Show a success message and rerun the app.
    
    Args:
        message: Success message to display
    """
    st.success(message)
    st.rerun()


def show_error_message(message: str) -> None:
    """
    Show an error message.
    
    Args:
        message: Error message to display
    """
    st.error(message)