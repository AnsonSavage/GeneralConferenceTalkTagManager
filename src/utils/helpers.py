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


def display_matched_keywords(paragraph_data: Dict[str, Any]) -> None:
    """
    Display matched keywords in red above the paragraph content.
    
    Args:
        paragraph_data: Dictionary containing paragraph information including matched_keywords
    """
    if paragraph_data.get('matched_keywords'):
        keywords_list = paragraph_data['matched_keywords']
        if keywords_list:
            st.markdown("**🔍 Matched Keywords:**")
            # Display keywords as red badges
            keywords_html = " ".join([f'<span style="background-color: #ffebee; color: #d32f2f; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; margin: 2px;">{keyword}</span>' for keyword in keywords_list])
            st.markdown(f'<div style="margin-bottom: 10px;">{keywords_html}</div>', unsafe_allow_html=True)


def display_hierarchical_tags_with_indentation(paragraph_id: int, db) -> None:
    """
    Display tags with proper visual hierarchy using Unicode characters and styled indentation.
    
    Args:
        paragraph_id: ID of the paragraph
        db: Database instance
    """
    tag_data = db.get_paragraph_tags_with_hierarchy(paragraph_id)
    
    if tag_data['explicit'] or tag_data['implicit']:
        st.markdown("**Current Tags:**")
        
        # Get all tags for this paragraph to build hierarchy
        all_tags = db.get_paragraph_tags(paragraph_id)
        
        # Build a hierarchy tree
        tag_tree = _build_tag_tree(all_tags, db)
        
        if tag_tree:
            _render_tag_tree(tag_tree, paragraph_id, db, level=0)
    else:
        st.info("No tags assigned to this paragraph yet.")


def _build_tag_tree(paragraph_tags: List[Dict], db) -> List[Dict]:
    """
    Build a hierarchical tree structure from paragraph tags.
    
    Args:
        paragraph_tags: List of tag dictionaries for the paragraph
        db: Database instance
        
    Returns:
        List of root tags with children nested
    """
    # Get all tags to understand the full hierarchy
    all_tags = {tag['id']: tag for tag in db.get_all_tags()}
    paragraph_tag_ids = {tag['id'] for tag in paragraph_tags}
    
    # Create tag nodes with children arrays
    tag_nodes = {}
    for tag in paragraph_tags:
        tag_nodes[tag['id']] = {
            'id': tag['id'],
            'name': tag['name'],
            'description': tag['description'],
            'parent_tag_id': tag['parent_tag_id'],
            'children': []
        }
    
    # Determine which tags are explicit (leaf nodes in this paragraph's context)
    # A tag is explicit if no child tags are also assigned to this paragraph
    for tag_id in paragraph_tag_ids:
        is_explicit = True
        # Check if any children of this tag are also in the paragraph's tags
        for other_tag_id in paragraph_tag_ids:
            if other_tag_id != tag_id:
                other_tag = all_tags.get(other_tag_id, {})
                if other_tag.get('parent_tag_id') == tag_id:
                    is_explicit = False
                    break
        
        tag_nodes[tag_id]['is_explicit'] = is_explicit
    
    # Build parent-child relationships
    root_tags = []
    for tag in paragraph_tags:
        tag_id = tag['id']
        parent_id = tag['parent_tag_id']
        
        if parent_id is None or parent_id not in paragraph_tag_ids:
            # This is a root tag (no parent or parent not in paragraph tags)
            root_tags.append(tag_nodes[tag_id])
        elif parent_id in tag_nodes:
            # Add as child to parent
            tag_nodes[parent_id]['children'].append(tag_nodes[tag_id])
    
    return root_tags


def _render_tag_tree(tag_tree: List[Dict], paragraph_id: int, db, level: int = 0):
    """
    Render the tag tree with proper indentation and styling.
    
    Args:
        tag_tree: List of tag nodes with children
        paragraph_id: ID of the paragraph
        db: Database instance
        level: Current nesting level
    """
    for i, tag_node in enumerate(tag_tree):
        is_last = (i == len(tag_tree) - 1)
        
        # Create indentation using Unicode box drawing characters
        if level == 0:
            prefix = ""
        else:
            # Build the prefix based on level and position
            prefix_parts = []
            for l in range(level):
                if l == level - 1:
                    # Last level - use appropriate connector
                    prefix_parts.append("└─ " if is_last else "├─ ")
                else:
                    # Middle levels - use vertical line or space
                    prefix_parts.append("│  ")
            prefix = "".join(prefix_parts)
        
        # Different styling for explicit vs implicit tags
        if tag_node['is_explicit']:
            # Explicit tag - removable
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"{prefix}🏷️ **{tag_node['name']}**")
            with col2:
                if st.button("❌", key=f"remove_tree_{paragraph_id}_{tag_node['id']}", 
                           help=f"Remove {tag_node['name']}"):
                    db.remove_tag_from_paragraph(paragraph_id, tag_node['id'])
                    db.update_paragraph_reviewed_status()
                    st.rerun()
        else:
            # Implicit tag - grayed out
            st.markdown(f"{prefix}🔗 :gray[{tag_node['name']}] *(inherited)*")
        
        # Render children recursively
        if tag_node['children']:
            _render_tag_tree(tag_node['children'], paragraph_id, db, level + 1)


def display_tag_hierarchy_for_selection(db, exclude_tag_ids: List[int] = None) -> Dict:
    """
    Display tag hierarchy for selection with proper indentation.
    
    Args:
        db: Database instance
        exclude_tag_ids: List of tag IDs to exclude from display
        
    Returns:
        Dictionary with selected tag information
    """
    if exclude_tag_ids is None:
        exclude_tag_ids = []
    
    all_tags = db.get_all_tags()
    available_tags = [tag for tag in all_tags if tag['id'] not in exclude_tag_ids]
    
    if not available_tags:
        st.info("No tags available for selection.")
        return None
    
    # Build hierarchy tree
    tag_tree = _build_full_tag_tree(available_tags)
    
    st.markdown("**Select a tag:**")
    
    # Use radio buttons with hierarchical display
    tag_options = []
    tag_display_names = []
    
    def collect_tag_options(nodes: List[Dict], level: int = 0):
        for node in nodes:
            # Create display name with indentation
            if level == 0:
                display_name = f"🏷️ {node['name']}"
            else:
                indent = "　" * level  # Use full-width space for indentation
                display_name = f"{indent}└─ {node['name']}"
            
            tag_options.append(node['id'])
            tag_display_names.append(display_name)
            
            # Add children
            if node['children']:
                collect_tag_options(node['children'], level + 1)
    
    collect_tag_options(tag_tree)
    
    if tag_display_names:
        selected_index = st.radio(
            "Choose tag:",
            range(len(tag_display_names)),
            format_func=lambda x: tag_display_names[x],
            key="tag_selection_radio"
        )
        
        if selected_index is not None:
            selected_tag_id = tag_options[selected_index]
            selected_tag = next(tag for tag in available_tags if tag['id'] == selected_tag_id)
            return selected_tag
    
    return None


def _build_full_tag_tree(tags: List[Dict]) -> List[Dict]:
    """
    Build a complete hierarchical tree from all tags.
    
    Args:
        tags: List of all tag dictionaries
        
    Returns:
        List of root tags with children nested
    """
    tag_dict = {tag['id']: {**tag, 'children': []} for tag in tags}
    root_tags = []
    
    # Build parent-child relationships
    for tag in tags:
        if tag['parent_tag_id'] is None:
            root_tags.append(tag_dict[tag['id']])
        elif tag['parent_tag_id'] in tag_dict:
            parent = tag_dict[tag['parent_tag_id']]
            parent['children'].append(tag_dict[tag['id']])
    
    return root_tags


def display_tag_breadcrumb(tag_id: int, db) -> str:
    """
    Display tag breadcrumb showing the full hierarchy path.
    
    Args:
        tag_id: ID of the tag
        db: Database instance
        
    Returns:
        Breadcrumb string
    """
    hierarchy = db.get_tag_hierarchy(tag_id)
    hierarchy.reverse()  # Start from root
    
    all_tags = {tag['id']: tag for tag in db.get_all_tags()}
    
    breadcrumb_parts = []
    for tag_id in hierarchy:
        if tag_id in all_tags:
            breadcrumb_parts.append(all_tags[tag_id]['name'])
    
    return " > ".join(breadcrumb_parts)


def display_compact_tag_list(tags: List[Dict], removable: bool = True, 
                           paragraph_id: int = None, db=None) -> None:
    """
    Display tags in a compact, visually appealing format.
    
    Args:
        tags: List of tag dictionaries
        removable: Whether tags can be removed
        paragraph_id: ID of paragraph (needed for removal)
        db: Database instance (needed for removal)
    """
    if not tags:
        st.info("No tags assigned.")
        return
    
    # Group tags by hierarchy level for better display
    root_tags = [tag for tag in tags if tag.get('parent_tag_id') is None]
    child_tags = [tag for tag in tags if tag.get('parent_tag_id') is not None]
    
    # Display as styled badges
    tag_html_parts = []
    
    for tag in root_tags:
        breadcrumb = display_tag_breadcrumb(tag['id'], db) if db else tag['name']
        if removable and paragraph_id and db:
            tag_html_parts.append(f'''
                <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 4px 8px; border-radius: 12px; 
                           font-size: 11px; margin: 2px; display: inline-block;">
                    🏷️ {tag['name']}
                </span>
            ''')
        else:
            tag_html_parts.append(f'''
                <span style="background: #f8f9fa; color: #495057; border: 1px solid #dee2e6;
                           padding: 4px 8px; border-radius: 12px; 
                           font-size: 11px; margin: 2px; display: inline-block;">
                    🏷️ {tag['name']}
                </span>
            ''')
    
    if tag_html_parts:
        st.markdown(f'<div>{"".join(tag_html_parts)}</div>', unsafe_allow_html=True)
        
        # Add remove buttons if needed
        if removable and paragraph_id and db:
            cols = st.columns(min(len(tags), 6))
            for i, tag in enumerate(tags):
                with cols[i % 6]:
                    if st.button(f"❌", key=f"remove_compact_{paragraph_id}_{tag['id']}", 
                               help=f"Remove {tag['name']}"):
                        db.remove_tag_from_paragraph(paragraph_id, tag['id'])
                        if hasattr(db, 'update_paragraph_reviewed_status'):
                            db.update_paragraph_reviewed_status()
                        st.rerun()