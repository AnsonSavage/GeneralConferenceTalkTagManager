"""
Add Tags to Paragraphs page module - Flashcard-style tagging workflow.
"""
import streamlit as st
from typing import Dict, Any
from ..components.ui_components import FlashcardNavigator, TagSelector
from ..utils.helpers import highlight_keywords, display_hierarchical_tags, display_matched_keywords


def render_add_tags_page(db) -> None:
    """Render the Add Tags to Paragraphs page with flashcard interface."""
    st.header("📝 Add Tags to Paragraphs")
    st.markdown("*Quick tagging workflow - Add tags and notes to untagged paragraphs*")
    
    # Load only untagged paragraphs
    paragraphs = db.get_all_paragraphs_with_filters(untagged_only=True)
    
    if paragraphs:
        # Initialize flashcard navigator
        navigator = FlashcardNavigator(paragraphs, "add_tags_paragraph_index")
        
        # Get current paragraph
        current_paragraph = navigator.get_current_item()
        
        if current_paragraph:
            _render_tagging_flashcard(current_paragraph, db, navigator)
            
            # Floating navigation at bottom
            navigator.render_floating_navigation()
    else:
        st.success("🎉 All paragraphs have been tagged!")
        st.info("Great job! All paragraphs in your database now have tags. You can go to 'Manage Paragraphs' to review and edit existing tags.")
        
        # Show some stats
        total_paragraphs = len(db.get_all_paragraphs_with_filters())
        st.metric("Total Paragraphs", total_paragraphs)


def _render_tagging_flashcard(paragraph: Dict[str, Any], db, navigator: FlashcardNavigator) -> None:
    """Render a single paragraph flashcard for tagging."""
    with st.container():
        # Talk information header with enhanced styling
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1f4e7a, #2d5a87); color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="margin: 0; color: white;">📖 {paragraph['talk_title']}</h3>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">
                <strong>{paragraph['speaker']}</strong> • {paragraph['conference_date']} • Paragraph {paragraph['paragraph_number']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if paragraph['hyperlink']:
            st.markdown(f"[🔗 View Original Talk]({paragraph['hyperlink']})")
        
        # Display matched keywords prominently
        display_matched_keywords(paragraph)
        
        # Paragraph content with better visibility
        st.markdown("### 📄 Paragraph Content")
        content = paragraph['content']
        if paragraph.get('matched_keywords'):
            content = highlight_keywords(content, paragraph['matched_keywords'])
        
        # Display content with proper contrast
        st.markdown(f"""
        <div style="background-color: #ffffff; color: #000000; padding: 20px; border-radius: 10px; border-left: 4px solid #007bff; margin: 10px 0; border: 1px solid #e0e0e0;">
            {content.replace('\n', '<br>')}
        </div>
        """, unsafe_allow_html=True)
        
        # Current tags display
        display_hierarchical_tags(paragraph['id'], db)
        
        st.divider()
        
        # Streamlined tagging interface
        _render_streamlined_tagging_interface(paragraph['id'], db, navigator)


def _render_streamlined_tagging_interface(paragraph_id: int, db, navigator: FlashcardNavigator) -> None:
    """Render streamlined tagging interface with hierarchical tag display."""
    st.markdown("### 🏷️ Add Tags")
    
    # Get all tags organized by hierarchy
    all_tags = db.get_all_tags()
    root_tags = [tag for tag in all_tags if tag['parent_tag_id'] is None]
    
    # Search/filter box
    search_term = st.text_input(
        "🔍 Search existing tags:",
        placeholder="Type to filter tags or search...",
        key="streamlined_tag_search"
    )
    
    # Filter tags based on search
    if search_term:
        filtered_tags = [tag for tag in all_tags if search_term.lower() in tag['name'].lower()]
        st.markdown(f"**🎯 Matching tags ({len(filtered_tags)} found):**")
        
        # Display filtered tags as clickable buttons
        if filtered_tags:
            cols = st.columns(min(len(filtered_tags), 4))
            for i, tag in enumerate(filtered_tags[:12]):  # Limit to 12 results
                with cols[i % 4]:
                    if st.button(f"➕ {tag['name']}", key=f"filtered_tag_{tag['id']}", help=tag['description'] or 'No description'):
                        db.tag_paragraph_with_hierarchy(paragraph_id, tag['id'])
                        db.update_paragraph_reviewed_status()
                        st.success(f"✅ Added '{tag['name']}'!")
                        st.rerun()
        else:
            st.info("No existing tags match your search.")
            # Quick create button
            if st.button(f"✨ Create new tag: '{search_term}'", key="quick_create_tag"):
                try:
                    tag_id = db.add_tag(search_term)
                    db.tag_paragraph_with_hierarchy(paragraph_id, tag_id)
                    db.update_paragraph_reviewed_status()
                    st.success(f"✅ Created and added '{search_term}'!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    
    else:
        # Display hierarchical tag structure
        st.markdown("**📋 All Tags (click to add):**")
        
        def render_tag_hierarchy(tag, level=0):
            """Recursively render tag hierarchy."""
            indent = "  " * level
            prefix = "└─ " if level > 0 else ""
            
            col1, col2 = st.columns([4, 1])
            with col1:
                tag_display = f"{indent}{prefix}**{tag['name']}**"
                if tag['description']:
                    tag_display += f" - *{tag['description']}*"
                st.markdown(tag_display)
            
            with col2:
                if st.button("➕", key=f"hier_tag_{tag['id']}", help=f"Add {tag['name']}"):
                    db.tag_paragraph_with_hierarchy(paragraph_id, tag['id'])
                    db.update_paragraph_reviewed_status()
                    st.success(f"✅ Added '{tag['name']}'!")
                    st.rerun()
            
            # Render children
            child_tags = [t for t in all_tags if t['parent_tag_id'] == tag['id']]
            for child_tag in child_tags:
                render_tag_hierarchy(child_tag, level + 1)
        
        # Render all root tags and their hierarchies
        for root_tag in root_tags:
            render_tag_hierarchy(root_tag)
            if root_tag != root_tags[-1]:  # Don't add divider after last item
                st.markdown("---")
    
    # Notes as dropdown (request #3)
    with st.expander("📝 Add Notes (Optional)", expanded=False):
        _render_notes_section(paragraph_id, db)
    
    # Completion workflow
    st.divider()
    st.markdown("### ✅ Mark as Complete")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Complete & Next", type="primary", key="complete_and_next"):
            db.mark_paragraph_reviewed(paragraph_id, True)
            # Move to next paragraph automatically
            current_index = navigator.get_current_index()
            if current_index < navigator.total_items - 1:
                st.session_state[navigator.session_key] = current_index + 1
            st.success("✅ Paragraph marked as reviewed!")
            st.rerun()
    
    with col2:
        if st.button("⏭️ Skip for Now", key="skip_paragraph"):
            # Move to next without marking as reviewed
            current_index = navigator.get_current_index()
            if current_index < navigator.total_items - 1:
                st.session_state[navigator.session_key] = current_index + 1
            st.info("⏭️ Skipped to next paragraph")
            st.rerun()
    
    with col3:
        # Progress indicator
        remaining = navigator.total_items - navigator.get_current_index() - 1
        st.info(f"📊 {remaining} paragraphs remaining")


def _render_notes_section(paragraph_id: int, db) -> None:
    """Render the notes section for the paragraph."""
    # Get current paragraph data to access notes
    paragraph_data = db.get_paragraph_with_notes(paragraph_id)
    current_notes = paragraph_data.get('notes', '') or ''
    
    with st.form(f"notes_form_{paragraph_id}"):
        notes = st.text_area(
            "Add your notes about this paragraph:",
            value=current_notes,
            height=100,
            placeholder="What insights, connections, or thoughts do you have about this paragraph?"
        )
        
        if st.form_submit_button("💾 Save Notes", type="primary"):
            db.update_paragraph_notes(paragraph_id, notes)
            st.success("✅ Notes saved!")
            st.rerun()