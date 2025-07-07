"""
Utility functions for the Conference Talks Analysis application.
"""
import streamlit as st
import random
from typing import List, Dict, Any


def highlight_keywords(content: str, keywords: List[str], paragraph_id: int = None) -> str:
    """
    Highlight keywords in content with red text, considering checkbox states if paragraph_id is provided.
    
    Args:
        content: The text content to highlight
        keywords: List of keywords to highlight
        paragraph_id: Optional paragraph ID to check checkbox states for selective highlighting
        
    Returns:
        Content with highlighted keywords
    """
    highlighted_content = content
    
    for keyword in keywords:
        # Check if this keyword should be highlighted (if paragraph_id is provided)
        should_highlight = True
        if paragraph_id is not None:
            checkbox_key = f"keyword_highlight_{paragraph_id}_{keyword}"
            should_highlight = st.session_state.get(checkbox_key, True)
        
        if should_highlight:
            # Check if we should use caps or title case
            use_caps = True
            if paragraph_id is not None:
                caps_key = f"caps_{paragraph_id}_{keyword}"
                use_caps = st.session_state.get(caps_key, True)
            
            # Apply highlighting with appropriate case
            if use_caps:
                highlighted_keyword = f"**:red[{keyword.upper()}]**"
                highlighted_keyword_cap = f"**:red[{keyword.capitalize().upper()}]**"
            else:
                highlighted_keyword = f"**:red[{keyword}]**"
                highlighted_keyword_cap = f"**:red[{keyword.capitalize()}]**"
            
            # Replace both lowercase and capitalized versions
            highlighted_content = highlighted_content.replace(keyword, highlighted_keyword)
            highlighted_content = highlighted_content.replace(keyword.capitalize(), highlighted_keyword_cap)
    
    return highlighted_content


def highlight_keywords_enhanced(content: str, keywords: List[str], 
                              active_keywords: List[str] = None, 
                              style_preferences: Dict[str, str] = None) -> str:
    """
    Enhanced keyword highlighting with style preferences and selective highlighting.
    
    Args:
        content: The text content to highlight
        keywords: List of all available keywords
        active_keywords: List of keywords that should be highlighted
        style_preferences: Dictionary mapping keywords to style preferences ('caps', 'title', 'bold')
        
    Returns:
        Content with highlighted keywords
    """
    if active_keywords is None:
        active_keywords = keywords
    
    if style_preferences is None:
        style_preferences = {}
    
    highlighted_content = content
    
    for keyword in keywords:
        if keyword in active_keywords:
            style = style_preferences.get(keyword, 'bold')
            
            if style == 'caps':
                highlighted_keyword = f"**:red[{keyword.upper()}]**"
                highlighted_keyword_cap = f"**:red[{keyword.capitalize().upper()}]**"
            elif style == 'title':
                highlighted_keyword = f"**:red[{keyword.title()}]**"
                highlighted_keyword_cap = f"**:red[{keyword.capitalize().title()}]**"
            else:  # bold
                highlighted_keyword = f"**:red[{keyword}]**"
                highlighted_keyword_cap = f"**:red[{keyword.capitalize()}]**"
            
            # Replace both lowercase and capitalized versions
            highlighted_content = highlighted_content.replace(keyword, highlighted_keyword)
            highlighted_content = highlighted_content.replace(keyword.capitalize(), highlighted_keyword_cap)
    
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


def display_enhanced_talk_info(paragraph_data: Dict[str, Any]) -> None:
    """
    Display enhanced talk information with better styling for flashcards.
    
    Args:
        paragraph_data: Dictionary containing talk information
    """
    st.markdown(f"""
    <div style="text-align: center; background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0;">
        <h4 style="color: #1f4e7a; margin-bottom: 8px;">📖 {paragraph_data['talk_title']}</h4>
        <p style="color: #495057; margin: 4px 0;">
            <strong>Speaker:</strong> {paragraph_data['speaker']} | 
            <strong>Date:</strong> {paragraph_data['conference_date']}
        </p>
        {f'<p style="color: #6c757d; margin: 4px 0;"><strong>Session:</strong> {paragraph_data.get("session", "N/A")}</p>' if paragraph_data.get('session') else ''}
        {f'<p style="margin: 8px 0;"><a href="{paragraph_data["hyperlink"]}" target="_blank">🔗 View Original Talk</a></p>' if paragraph_data.get('hyperlink') else ''}
    </div>
    """, unsafe_allow_html=True)


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


def format_flashcard_content(content: str, max_length: int = None) -> str:
    """
    Format content for display in flashcards with optional truncation.
    
    Args:
        content: The content to format
        max_length: Optional maximum length for truncation
        
    Returns:
        Formatted content
    """
    if max_length and len(content) > max_length:
        return content[:max_length] + "..."
    return content


def get_keyword_style_preferences(paragraph_id: int, keywords: List[str]) -> Dict[str, str]:
    """
    Get style preferences for keywords from session state.
    
    Args:
        paragraph_id: ID of the paragraph
        keywords: List of keywords
        
    Returns:
        Dictionary mapping keywords to their style preferences
    """
    preferences = {}
    for keyword in keywords:
        caps_key = f"caps_{paragraph_id}_{keyword}"
        if st.session_state.get(caps_key, True):
            preferences[keyword] = 'caps'
        else:
            preferences[keyword] = 'title'
    return preferences


def get_active_keywords(paragraph_id: int, keywords: List[str]) -> List[str]:
    """
    Get list of keywords that should be highlighted based on checkbox states.
    
    Args:
        paragraph_id: ID of the paragraph
        keywords: List of all keywords
        
    Returns:
        List of keywords that should be highlighted
    """
    active = []
    for keyword in keywords:
        checkbox_key = f"keyword_highlight_{paragraph_id}_{keyword}"
        if st.session_state.get(checkbox_key, True):
            active.append(keyword)
    return active


def create_keyword_summary(keywords: List[str], active_keywords: List[str]) -> str:
    """
    Create a summary of keyword status for display.
    
    Args:
        keywords: List of all keywords
        active_keywords: List of active keywords
        
    Returns:
        Summary string
    """
    if not keywords:
        return "No keywords found"
    
    active_count = len(active_keywords)
    total_count = len(keywords)
    
    if active_count == total_count:
        return f"All {total_count} keywords highlighted"
    elif active_count == 0:
        return f"No keywords highlighted (of {total_count})"
    else:
        return f"{active_count} of {total_count} keywords highlighted"