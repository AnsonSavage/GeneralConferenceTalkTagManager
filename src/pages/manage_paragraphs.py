"""
Manage Paragraphs page module - Comprehensive paragraph management interface.
"""
import streamlit as st
from typing import Dict, Any
from ..components.ui_components import FlashcardNavigator, TagSelector, FilterControls
from ..utils.helpers import highlight_keywords, display_hierarchical_tags_with_indentation, display_matched_keywords
from ..database.base_database import BaseDatabaseInterface


def render_manage_paragraphs_page(database: BaseDatabaseInterface) -> None:
    """Render the Manage Paragraphs page with comprehensive management features."""
    st.header("🔧 Manage Paragraphs")
    st.markdown("*Comprehensive paragraph management - Filter, edit, and review tagged paragraphs*")
    
    # Enhanced filter controls
    filter_controls = FilterControls(database)
    filters = filter_controls.render_comprehensive_paragraph_filters()
    
    # Load filtered paragraphs
    paragraphs = database.get_all_paragraphs_with_filters(
        tag_filter=filters['tag_filter'],
        keyword_filter=filters['keyword_filter'],
        untagged_only=filters['untagged_only']
    )
    
    if paragraphs:
        # Show paragraph count and filters summary
        _render_paragraph_summary(paragraphs, filters)
        
        # Choose view mode
        view_mode = st.radio(
            "View Mode:",
            options=["📋 List View", "📄 Flashcard View"],
            horizontal=True,
            help="Choose how to display paragraphs"
        )
        
        if view_mode == "📋 List View":
            _render_list_view(paragraphs, database, filters)
        else:
            _render_flashcard_view(paragraphs, database, filters)
    else:
        st.info("No paragraphs found with the current filters. Try adjusting your filter criteria.")


def _render_paragraph_summary(paragraphs, filters):
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


def _render_list_view(paragraphs, database: BaseDatabaseInterface, filters):
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
            
            # Truncated content
            content = paragraph['content']
            if len(content) > 300:
                content = content[:300] + "..."
            
            if paragraph.get('matched_keywords'):
                content = highlight_keywords(content, paragraph['matched_keywords'])
            
            st.markdown(content)
            
            # Tags and management
            display_hierarchical_tags_with_indentation(paragraph['id'], database)
            
            # Notes
            if paragraph.get('notes'):
                st.markdown(f"**📝 Notes:** {paragraph['notes']}")
            
            # Quick tag management
            with st.expander("🏷️ Manage Tags", expanded=False):
                tag_selector = TagSelector(database, paragraph['id'])
                tag_selector.render_enhanced_tag_search(f"list_{paragraph['id']}")


def _render_flashcard_view(paragraphs, database: BaseDatabaseInterface, filters):
    """Render paragraphs in flashcard view for detailed editing."""
    st.subheader("📄 Flashcard View")
    
    # Initialize flashcard navigator
    navigator = FlashcardNavigator(paragraphs, "manage_paragraph_index")
    
    # Render navigation controls
    navigator.render_enhanced_navigation()
    
    # Get current paragraph
    current_paragraph = navigator.get_current_item()
    
    if current_paragraph:
        st.divider()
        _render_management_flashcard(current_paragraph, database, navigator, filters['keyword_filter'])


def _render_management_flashcard(paragraph: Dict[str, Any], database: BaseDatabaseInterface, navigator: FlashcardNavigator, keyword_filter: str = None) -> None:
    """Render a single paragraph as a management flashcard."""
    with st.container():
        # Talk information header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {paragraph['talk_title']}")
            st.markdown(f"**Speaker:** {paragraph['speaker']} | **Date:** {paragraph['conference_date']} | **Paragraph:** {paragraph['paragraph_number']}")
            
            if paragraph['hyperlink']:
                st.markdown(f"[🔗 View Talk]({paragraph['hyperlink']})")
        
        with col2:
            # Review status and actions
            current_status = paragraph.get('reviewed', False)
            
            # Mark as reviewed button - moves to next unreviewed
            if not current_status:
                if st.button(
                    "✅ Mark Reviewed & Continue",
                    type="primary",
                    key=f"mark_reviewed_continue_{paragraph['id']}",
                    help="Mark this paragraph as reviewed and move to next unreviewed paragraph"
                ):
                    moved_to_next = navigator.mark_current_reviewed_and_move_to_next_unreviewed(database)
                    if moved_to_next:
                        st.success("Marked as reviewed! Moving to next unreviewed paragraph.")
                    else:
                        st.success("Marked as reviewed! No more unreviewed paragraphs.")
                    st.rerun()
            
            # Toggle review status button
            if st.button(
                "🔄 Mark Unreviewed" if current_status else "✅ Mark Reviewed",
                type="secondary",
                key=f"toggle_review_{paragraph['id']}",
                help="Toggle review status without moving to next paragraph"
            ):
                database.mark_paragraph_reviewed(paragraph['id'], not current_status)
                # Update the navigator's local data
                current_index = navigator.get_current_index()
                navigator.items[current_index]['reviewed'] = not current_status
                st.rerun()
        
        # Display matched keywords
        display_matched_keywords(paragraph)
        
        # Paragraph content
        st.markdown("---")
        
        # Highlight keywords
        content = paragraph['content']
        if keyword_filter and keyword_filter != "All Keywords":
            content = highlight_keywords(content, [keyword_filter])
        elif paragraph.get('matched_keywords'):
            content = highlight_keywords(content, paragraph['matched_keywords'])
        
        st.markdown(content)
        st.markdown("---")
        
        # Notes management
        _render_notes_management(paragraph, database)
        
        # Tags management
        st.markdown("**🏷️ Current Tags:**")
        display_hierarchical_tags_with_indentation(paragraph['id'], database)
        
        # Tag management interface
        with st.expander("➕ Add/Edit Tags", expanded=False):
            tag_selector = TagSelector(database, paragraph['id'])
            
            tab1, tab2, tab3 = st.tabs(["🔍 Search Tags", "🏷️ Browse All", "➕ Create New"])
            
            with tab1:
                tag_selector.render_enhanced_tag_search("manage_flashcard")
            
            with tab2:
                tag_selector.render_enhanced_all_tags("manage_flashcard")
            
            with tab3:
                tag_selector.render_enhanced_tag_creation("manage_flashcard")


def _render_notes_management(paragraph: Dict[str, Any], database: BaseDatabaseInterface) -> None:
    """Render notes management section."""
    st.markdown("**📝 Notes:**")
    
    current_notes = paragraph.get('notes', '') or ''
    
    if current_notes:
        # Display current notes
        st.markdown(f"> {current_notes}")
        
        if st.button("✏️ Edit Notes", key=f"edit_notes_{paragraph['id']}"):
            st.session_state[f"editing_notes_{paragraph['id']}"] = True
            st.rerun()
    else:
        st.markdown("*No notes added yet.*")
        if st.button("➕ Add Notes", key=f"add_notes_{paragraph['id']}"):
            st.session_state[f"editing_notes_{paragraph['id']}"] = True
            st.rerun()
    
    # Notes editing form
    if st.session_state.get(f"editing_notes_{paragraph['id']}", False):
        with st.form(f"notes_edit_form_{paragraph['id']}"):
            notes = st.text_area(
                "Edit notes:",
                value=current_notes,
                height=100
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save", type="primary"):
                    database.update_paragraph_notes(paragraph['id'], notes)
                    st.session_state[f"editing_notes_{paragraph['id']}"] = False
                    st.success("Notes saved!")
                    st.rerun()
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state[f"editing_notes_{paragraph['id']}"] = False
                    st.rerun()