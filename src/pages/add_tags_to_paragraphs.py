"""
Add Tags to Paragraphs page module - Flashcard-style tagging workflow.
"""
import streamlit as st
from typing import Dict, Any
from ..components.ui_components import FlashcardNavigator, TagSelector
from ..utils.helpers import highlight_keywords, display_hierarchical_tags_with_indentation, display_matched_keywords


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
        display_hierarchical_tags_with_indentation(paragraph['id'], db)
        
        st.divider()
        
        # Streamlined tagging interface
        _render_streamlined_tagging_interface(paragraph['id'], db, navigator)


def _render_streamlined_tagging_interface(paragraph_id: int, db, navigator: FlashcardNavigator) -> None:
    """Render streamlined tagging interface with hierarchical tag display."""
    st.markdown("### 🏷️ Add Tags")
    
    # Get all tags organized by hierarchy
    all_tags = db.get_all_tags()
    root_tags = [tag for tag in all_tags if tag['parent_tag_id'] is None]
    
    # Tag selection dropdown - similar to Parent Tag dropdown in Manage Tags
    if all_tags:
        # Create options dictionary with tag names as keys and IDs as values
        tag_options = {tag['name']: tag['id'] for tag in all_tags}
        
        # Add search functionality with selectbox
        selected_tag_name = st.selectbox(
            "🔍 Select a tag to add:",
            options=[""] + list(tag_options.keys()),
            key=f"tag_selector_dropdown_{paragraph_id}",
            help="Choose a tag from the dropdown to add it to this paragraph"
        )
        
        # Automatically add the selected tag, but only if it's a new selection
        if selected_tag_name and selected_tag_name != "":
            # Use a session state key to track the last processed tag for this paragraph
            last_processed_key = f"last_processed_tag_{paragraph_id}"
            
            # Only process if this is a different selection than last time
            if st.session_state.get(last_processed_key) != selected_tag_name:
                selected_tag_id = tag_options[selected_tag_name]
                db.tag_paragraph_with_hierarchy(paragraph_id, selected_tag_id)
                db.update_paragraph_reviewed_status()
                st.success(f"✅ Added '{selected_tag_name}'!")
                
                # Mark this tag as processed for this paragraph
                st.session_state[last_processed_key] = selected_tag_name
                st.rerun()
    
    # Option to create new tag if none selected
    with st.expander("✨ Create New Tag", expanded=False):
        with st.form("quick_create_tag_form"):
            new_tag_name = st.text_input("New Tag Name:")
            new_tag_description = st.text_area("Description (optional):")
            
            # Parent tag selection for new tag
            if all_tags:
                parent_options = {tag['name']: tag['id'] for tag in all_tags}
                parent_tag = st.selectbox(
                    "Parent Tag (optional):",
                    options=[""] + list(parent_options.keys()),
                    key="new_tag_parent"
                )
            else:
                parent_tag = ""
            
            if st.form_submit_button("Create & Add Tag"):
                if new_tag_name:
                    try:
                        parent_id = parent_options.get(parent_tag) if parent_tag and all_tags else None
                        tag_id = db.add_tag(new_tag_name, new_tag_description, parent_id)
                        db.tag_paragraph_with_hierarchy(paragraph_id, tag_id)
                        db.update_paragraph_reviewed_status()
                        st.success(f"✅ Created and added '{new_tag_name}'!")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                else:
                    st.error("Please enter a tag name.")
    
    # Display hierarchical tag structure for reference
    with st.expander("📋 View All Tags", expanded=False):
        if all_tags:
            def render_tag_hierarchy(tag, level=0, is_last=True, parent_prefixes=None):
                """Recursively render tag hierarchy with proper Unicode tree structure."""
                if parent_prefixes is None:
                    parent_prefixes = []
                
                # Create the tree prefix
                if level == 0:
                    prefix = ""
                else:
                    # Build prefix from parent levels
                    prefix_parts = parent_prefixes.copy()
                    if is_last:
                        prefix_parts.append("└─ ")
                    else:
                        prefix_parts.append("├─ ")
                    prefix = "".join(prefix_parts)
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    if level == 0:
                        tag_display = f"🏷️ **{tag['name']}**"
                    else:
                        tag_display = f"{prefix}🏷️ **{tag['name']}**"
                    
                    if tag['description']:
                        tag_display += f" - *{tag['description']}*"
                    st.markdown(tag_display)
                
                with col2:
                    if st.button("➕", key=f"hier_add_{tag['id']}", help=f"Add {tag['name']}"):
                        db.tag_paragraph_with_hierarchy(paragraph_id, tag['id'])
                        db.update_paragraph_reviewed_status()
                        st.success(f"✅ Added '{tag['name']}'!")
                        st.rerun()
                
                # Render children with proper tree structure
                child_tags = [t for t in all_tags if t['parent_tag_id'] == tag['id']]
                
                # Update parent prefixes for children
                new_parent_prefixes = parent_prefixes.copy()
                if level >= 0:  # Apply to all levels including root
                    if is_last:
                        new_parent_prefixes.append("   ")  # Three spaces for completed branch
                    else:
                        new_parent_prefixes.append("│  ")  # Vertical line for continuing branch
                
                for i, child_tag in enumerate(child_tags):
                    is_last_child = (i == len(child_tags) - 1)
                    render_tag_hierarchy(child_tag, level + 1, is_last_child, new_parent_prefixes)
            
            # Render all root tags and their hierarchies
            for i, root_tag in enumerate(root_tags):
                is_last_root = (i == len(root_tags) - 1)
                render_tag_hierarchy(root_tag, 0, is_last_root)
                if not is_last_root:
                    st.markdown("---")
        else:
            st.info("No tags available. Create your first tag above!")

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