"""
Manage Paragraphs page module - Comprehensive paragraph management interface.
"""
import streamlit as st
from typing import Dict, Any, List
from ..components.ui_components import FlashcardNavigator, TagSelector, FilterControls
from ..utils.helpers import highlight_keywords, display_hierarchical_tags_with_indentation, display_matched_keywords
from ..database.base_database import BaseDatabaseInterface


def render_manage_paragraphs_page(database: BaseDatabaseInterface) -> None:
    """Render the Manage Paragraphs page with comprehensive management features."""
    st.header("🔧 Manage Paragraphs")
    st.markdown("*Comprehensive paragraph management - Filter, edit, and review tagged paragraphs*")
    
    # Enhanced filter controls with search
    filter_controls = FilterControls(database)
    filters = filter_controls.render_comprehensive_paragraph_filters()
    
    # Add text search functionality
    search_filters = _render_text_search_filters()
    
    # Load filtered paragraphs
    paragraphs = database.get_all_paragraphs_with_filters(
        tag_filter=filters['tag_filter'],
        keyword_filter=filters['keyword_filter'],
        untagged_only=filters['untagged_only']
    )
    
    # Apply text search filters
    paragraphs = _apply_text_search_filters(paragraphs, search_filters)
    
    if paragraphs:
        # Show paragraph count and filters summary
        _render_paragraph_summary(paragraphs, filters, search_filters)
        
        # Choose view mode
        view_mode = st.radio(
            "View Mode:",
            options=["📋 List View", "📄 Flashcard View"],
            horizontal=True,
            help="Choose how to display paragraphs"
        )
        
        if view_mode == "📋 List View":
            _render_list_view(paragraphs, database, filters, search_filters)
        else:
            _render_flashcard_view(paragraphs, database, filters, search_filters)
    else:
        st.info("No paragraphs found with the current filters. Try adjusting your filter criteria.")


def _render_text_search_filters() -> Dict[str, Any]:
    """Render text search and filtering controls."""
    with st.expander("🔍 Text Search & Filters", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            search_text = st.text_input(
                "Search in content:",
                placeholder="Enter words to search in paragraph content...",
                help="Search for specific words or phrases in paragraph text"
            )
            
            search_title = st.text_input(
                "Search in titles:",
                placeholder="Enter words to search in talk titles...",
                help="Search for specific words or phrases in talk titles"
            )
        
        with col2:
            search_speaker = st.text_input(
                "Search speaker:",
                placeholder="Enter speaker name...",
                help="Search for specific speakers"
            )
            
            search_notes = st.text_input(
                "Search in notes:",
                placeholder="Enter words to search in notes...",
                help="Search for specific words or phrases in paragraph notes"
            )
        
        # Search options
        case_sensitive = st.checkbox("Case sensitive search", value=False)
        whole_words = st.checkbox("Match whole words only", value=False)
    
    return {
        'search_text': search_text.strip() if search_text else None,
        'search_title': search_title.strip() if search_title else None,
        'search_speaker': search_speaker.strip() if search_speaker else None,
        'search_notes': search_notes.strip() if search_notes else None,
        'case_sensitive': case_sensitive,
        'whole_words': whole_words
    }


def _apply_text_search_filters(paragraphs: List[Dict], search_filters: Dict[str, Any]) -> List[Dict]:
    """Apply text search filters to paragraphs."""
    if not any([search_filters['search_text'], search_filters['search_title'], 
                search_filters['search_speaker'], search_filters['search_notes']]):
        return paragraphs
    
    import re
    
    filtered_paragraphs = []
    
    for paragraph in paragraphs:
        matches = True
        
        # Helper function to check if text matches search criteria
        def text_matches(text: str, search_term: str) -> bool:
            if not search_term or not text:
                return True
            
            if not search_filters['case_sensitive']:
                text = text.lower()
                search_term = search_term.lower()
            
            if search_filters['whole_words']:
                # Use regex for whole word matching
                pattern = r'\b' + re.escape(search_term) + r'\b'
                return bool(re.search(pattern, text, re.IGNORECASE if not search_filters['case_sensitive'] else 0))
            else:
                return search_term in text
        
        # Check content search
        if search_filters['search_text']:
            if not text_matches(paragraph.get('content', ''), search_filters['search_text']):
                matches = False
        
        # Check title search
        if search_filters['search_title']:
            if not text_matches(paragraph.get('talk_title', ''), search_filters['search_title']):
                matches = False
        
        # Check speaker search
        if search_filters['search_speaker']:
            if not text_matches(paragraph.get('speaker', ''), search_filters['search_speaker']):
                matches = False
        
        # Check notes search
        if search_filters['search_notes']:
            if not text_matches(paragraph.get('notes', '') or '', search_filters['search_notes']):
                matches = False
        
        if matches:
            filtered_paragraphs.append(paragraph)
    
    return filtered_paragraphs


def _render_paragraph_summary(paragraphs, filters, search_filters):
    """Render summary information about the filtered paragraphs."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Paragraphs", len(paragraphs))
    
    with col2:
        tagged_count = len([p for p in paragraphs if p.get('has_tags', False)])
        st.metric("Tagged", tagged_count)
    
    with col3:
        reviewed_count = len([p for p in paragraphs if p.get('reviewed', False)])
        st.metric("Reviewed", reviewed_count)
    
    with col4:
        untagged_count = len(paragraphs) - tagged_count
        st.metric("Untagged", untagged_count)
    
    # Show active search filters
    active_filters = []
    if search_filters['search_text']:
        active_filters.append(f"Content: '{search_filters['search_text']}'")
    if search_filters['search_title']:
        active_filters.append(f"Title: '{search_filters['search_title']}'")
    if search_filters['search_speaker']:
        active_filters.append(f"Speaker: '{search_filters['search_speaker']}'")
    if search_filters['search_notes']:
        active_filters.append(f"Notes: '{search_filters['search_notes']}'")
    
    if active_filters:
        st.info(f"🔍 Active search filters: {', '.join(active_filters)}")


def _render_list_view(paragraphs, database: BaseDatabaseInterface, filters, search_filters):
    """Render paragraphs in a list view for quick scanning and editing."""
    st.subheader("📋 Paragraph List")
    
    # Pagination with "Show All" option
    items_per_page_options = [10, 25, 50, 100, "Show All"]
    items_per_page = st.selectbox("Items per page:", items_per_page_options, index=1)
    
    if items_per_page == "Show All":
        # Show all items without pagination
        page_paragraphs = paragraphs
        st.info(f"Showing all {len(paragraphs)} paragraphs")
    else:
        # Regular pagination
        total_pages = (len(paragraphs) - 1) // items_per_page + 1
        current_page = st.number_input("Page:", min_value=1, max_value=total_pages, value=1)
        
        start_idx = (current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(paragraphs))
        page_paragraphs = paragraphs[start_idx:end_idx]
        
        st.info(f"Showing {len(page_paragraphs)} of {len(paragraphs)} paragraphs (Page {current_page} of {total_pages})")
    
    # Display paragraphs
    for i, paragraph in enumerate(page_paragraphs):
        with st.expander(
            f"📄 {paragraph['talk_title']} - Par. {paragraph['paragraph_number']} "
            f"{'✅' if paragraph.get('reviewed') else '⏳'}",
            expanded=False
        ):
            # Talk info
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Speaker:** {paragraph['speaker']}")
                st.markdown(f"**Date:** {paragraph['conference_date']}")
                if paragraph['hyperlink']:
                    st.markdown(f"[🔗 View Talk]({paragraph['hyperlink']})")
            
            with col2:
                # Quick actions
                if not paragraph.get('reviewed'):
                    if st.button("✅ Mark Reviewed", key=f"review_{paragraph['id']}"):
                        database.mark_paragraph_reviewed(paragraph['id'], True)
                        st.success("Marked as reviewed!")
                        st.rerun()
                else:
                    if st.button("🔄 Mark Unreviewed", key=f"unreview_{paragraph['id']}"):
                        database.mark_paragraph_reviewed(paragraph['id'], False)
                        st.info("Marked as unreviewed!")
                        st.rerun()
            
            # Keywords and content
            display_matched_keywords(paragraph)
            
            # Highlight content based on search filters
            content = paragraph['content']
            if len(content) > 300:
                content = content[:300] + "..."
            
            # Highlight search terms
            content = _highlight_search_terms(content, search_filters)
            
            # Also highlight matched keywords
            if paragraph.get('matched_keywords'):
                content = highlight_keywords(content, paragraph['matched_keywords'])
            
            st.markdown(content)
            
            # Tags and management
            display_hierarchical_tags_with_indentation(paragraph['id'], database)
            
            # Inline notes editing
            _render_inline_notes_editor(paragraph, database, f"list_{paragraph['id']}")
            
            # Quick tag management
            with st.expander("🏷️ Manage Tags", expanded=False):
                tag_selector = TagSelector(database, paragraph['id'])
                tag_selector.render_enhanced_tag_search(f"list_{paragraph['id']}")


def _render_inline_notes_editor(paragraph: Dict[str, Any], database: BaseDatabaseInterface, key_suffix: str):
    """Render inline notes editor for a paragraph."""
    current_notes = paragraph.get('notes', '') or ''
    notes_key = f"notes_{paragraph['id']}_{key_suffix}"
    
    # Notes editor
    new_notes = st.text_area(
        "📝 Notes:",
        value=current_notes,
        key=notes_key,
        height=70,  # Fixed: minimum height must be 68, using 70 to be safe
        placeholder="Add your notes here...",
        help="Your notes will be saved automatically when you click 'Save Notes'"
    )
    
    # Only show save button if notes have changed
    if new_notes != current_notes:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Save Notes", key=f"save_notes_{paragraph['id']}_{key_suffix}"):
                database.update_paragraph_notes(paragraph['id'], new_notes)
                st.success("Notes saved!")
                st.rerun()
        with col2:
            if st.button("↩️ Cancel", key=f"cancel_notes_{paragraph['id']}_{key_suffix}"):
                st.rerun()


def _highlight_search_terms(text: str, search_filters: Dict[str, Any]) -> str:
    """Highlight search terms in text."""
    if not text:
        return text
    
    import re
    
    search_terms = []
    if search_filters['search_text']:
        search_terms.append(search_filters['search_text'])
    if search_filters['search_title']:
        search_terms.append(search_filters['search_title'])
    if search_filters['search_speaker']:
        search_terms.append(search_filters['search_speaker'])
    if search_filters['search_notes']:
        search_terms.append(search_filters['search_notes'])
    
    if not search_terms:
        return text
    
    highlighted_text = text
    for term in search_terms:
        if term:
            flags = 0 if search_filters['case_sensitive'] else re.IGNORECASE
            if search_filters['whole_words']:
                pattern = r'\b' + re.escape(term) + r'\b'
            else:
                pattern = re.escape(term)
            
            highlighted_text = re.sub(
                pattern,
                lambda m: f"<mark style='background-color: yellow; padding: 1px 2px;'>{m.group()}</mark>",
                highlighted_text,
                flags=flags
            )
    
    return highlighted_text


def _render_flashcard_view(paragraphs, database: BaseDatabaseInterface, filters, search_filters):
    """Render paragraphs in flashcard view for detailed editing."""
    st.subheader("📄 Flashcard View")
    
    # Initialize flashcard navigator
    navigator = FlashcardNavigator(paragraphs, "manage_paragraph_index")
    
    # Render dual navigation system
    navigator.render_dual_navigation()
    
    # Get current paragraph
    current_paragraph = navigator.get_current_item()
    
    if current_paragraph:
        st.divider()
        _render_management_flashcard(current_paragraph, database, navigator, filters['keyword_filter'], search_filters)


def _render_management_flashcard(paragraph: Dict[str, Any], database: BaseDatabaseInterface, navigator: FlashcardNavigator, keyword_filter: str = None, search_filters: Dict[str, Any] = None) -> None:
    """Render a single paragraph as a management flashcard."""
    with st.container():
        # Talk information header
        title_text = paragraph['talk_title']
        speaker_text = paragraph['speaker']
        
        # Highlight search terms in title and speaker
        if search_filters:
            title_text = _highlight_search_terms(title_text, search_filters)
            speaker_text = _highlight_search_terms(speaker_text, search_filters)
        
        st.markdown(f"### {title_text}")
        st.markdown(f"**Speaker:** {speaker_text} | **Date:** {paragraph['conference_date']} | **Paragraph:** {paragraph['paragraph_number']}")
        
        if paragraph['hyperlink']:
            st.markdown(f"[🔗 View Talk]({paragraph['hyperlink']})")
        
        # Display matched keywords
        display_matched_keywords(paragraph)
        
        # Paragraph content
        st.markdown("---")
        
        # Highlight keywords and search terms
        content = paragraph['content']
        
        # First highlight search terms
        if search_filters:
            content = _highlight_search_terms(content, search_filters)
        
        # Then highlight keywords
        if keyword_filter and keyword_filter != "All Keywords":
            content = highlight_keywords(content, [keyword_filter])
        elif paragraph.get('matched_keywords'):
            content = highlight_keywords(content, paragraph['matched_keywords'])
        
        st.markdown(content)
        st.markdown("---")
        
        # Enhanced notes section with inline editing
        _render_inline_notes_editor(paragraph, database, "flashcard")
        
        # Tags management
        st.markdown("**🏷️ Current Tags:**")
        display_hierarchical_tags_with_indentation(paragraph['id'], database)
        
        # Tag management interface
        st.markdown("**➕ Add Tags:**")
        tag_selector = TagSelector(database, paragraph['id'])
        tag_selector.render_enhanced_tag_search("manage_flashcard")
        
        # Completion button - NO auto-navigation
        st.markdown("---")
        current_status = paragraph.get('reviewed', False)
        
        if not current_status:
            if st.button(
                "✅ Mark Complete",
                type="primary",
                key=f"mark_complete_{paragraph['id']}",
                help="Mark this paragraph as reviewed"
            ):
                database.mark_paragraph_reviewed(paragraph['id'], True)
                # Update the navigator's local data
                current_index = navigator.get_current_index()
                navigator.items[current_index]['reviewed'] = True
                # DON'T move to next card - just stay here
                st.success("Marked as complete!")
                st.rerun()
        else:
            st.success("✅ This paragraph is already marked as complete")
            if st.button(
                "🔄 Mark Incomplete",
                type="secondary",
                key=f"mark_incomplete_{paragraph['id']}",
                help="Mark this paragraph as not reviewed"
            ):
                database.mark_paragraph_reviewed(paragraph['id'], False)
                # Update the navigator's local data
                current_index = navigator.get_current_index()
                navigator.items[current_index]['reviewed'] = False
                st.info("Marked as incomplete!")
                st.rerun()