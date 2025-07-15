"""
Manage Tags page module.
"""
import streamlit as st
from typing import List, Dict, Any, Optional


def render_manage_tags_page(database) -> None:
    """Render the Manage Tags page."""
    st.header("Manage Tags")
    
    # Add new tag section
    _render_add_tag_section(database)
    
    # Display existing tags
    st.subheader("Existing Tags")
    tags = database.get_all_tags()
    
    if tags:
        # Check if we're editing a tag
        if 'editing_tag' in st.session_state:
            _render_tag_edit_form(database, tags)
        else:
            _render_tags_list(tags)
    else:
        st.info("No tags created yet.")


def _render_add_tag_section(database) -> None:
    """Render the add new tag section."""
    # Clear form fields if flag is set
    if st.session_state.get("add_tag_clear", False):
        st.session_state["add_tag_name"] = ""
        st.session_state["add_tag_description"] = ""
        st.session_state["add_tag_parent"] = ""
        st.session_state["add_tag_clear"] = False

    with st.expander("Add New Tag", expanded=False):
        with st.form("add_tag_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                tag_name = st.text_input("Tag Name", key="add_tag_name")
                tag_description = st.text_area("Description (optional)", key="add_tag_description")
            
            with col2:
                # Parent tag selection
                all_tags = database.get_all_tags()
                parent_options = {tag['name']: tag['id'] for tag in all_tags}
                
                parent_tag = st.selectbox(
                    "Parent Tag (optional):",
                    options=[""] + list(parent_options.keys()),
                    key="add_tag_parent"
                )
            
            submitted = st.form_submit_button("Add Tag")
            
            if submitted and tag_name:
                try:
                    parent_id = parent_options[parent_tag] if parent_tag else None
                    tag_id = database.add_tag(tag_name, tag_description, parent_id)
                    st.success(f"Tag '{tag_name}' added with ID: {tag_id}")
                    st.session_state["add_tag_clear"] = True
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


def _render_tag_edit_form(database, tags: List[Dict[str, Any]]) -> None:
    """Render the tag editing form."""
    tag_to_edit = next((tag for tag in tags if tag['id'] == st.session_state.editing_tag), None)
    
    if tag_to_edit:
        st.markdown(f"**Editing Tag: {tag_to_edit['name']}**")
        
        # Check if we're in deletion confirmation mode
        if st.session_state.get(f"confirm_delete_{tag_to_edit['id']}", False):
            _render_tag_deletion_confirmation(database, tag_to_edit)
            return
        
        with st.form("edit_tag_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Tag Name", value=tag_to_edit['name'])
                new_description = st.text_area("Description", value=tag_to_edit['description'] or "")
            
            with col2:
                # Parent tag selection (exclude circular references)
                parent_options = _get_valid_parent_options(database, tags, tag_to_edit['id'])
                current_parent = _get_current_parent_name(tags, tag_to_edit['parent_tag_id'])
                
                parent_index = 0
                parent_keys = [""] + list(parent_options.keys())
                if current_parent and current_parent in parent_keys:
                    parent_index = parent_keys.index(current_parent)
                
                new_parent = st.selectbox(
                    "Parent Tag (optional):",
                    options=parent_keys,
                    index=parent_index
                )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                update_submitted = st.form_submit_button("Update Tag", type="primary")
            with col2:
                delete_submitted = st.form_submit_button("Delete Tag", type="secondary")
            with col3:
                cancel_edit = st.form_submit_button("Cancel")
            
            if update_submitted:
                _handle_tag_update(database, parent_options, tag_to_edit['id'], new_name, new_description, new_parent)
            
            if delete_submitted:
                # Set flag to show confirmation dialog
                st.session_state[f"confirm_delete_{tag_to_edit['id']}"] = True
                st.rerun()
            
            if cancel_edit:
                del st.session_state.editing_tag
                st.rerun()


def _render_tag_deletion_confirmation(database, tag_to_edit: Dict[str, Any]) -> None:
    """Render tag deletion confirmation dialog outside of form."""
    # Check if tag has any paragraphs using the abstract method
    paragraph_count = database.get_paragraph_count_for_tag(tag_to_edit['id'])
    
    if paragraph_count > 0:
        # Show confirmation dialog
        st.warning(f"⚠️ This tag is assigned to **{paragraph_count}** paragraph(s).")
        st.markdown("**Are you sure you want to delete this tag?** This will:")
        st.markdown("- Remove the tag from all assigned paragraphs")
        st.markdown("- Permanently delete the tag from the system")
    else:
        st.warning("**Are you sure you want to delete this tag?**")
        st.markdown("This will permanently delete the tag from the system.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Yes, Delete Tag", type="primary", key="confirm_delete"):
            if paragraph_count > 0:
                # Remove tag from all paragraphs first using the abstract method
                affected_count = database.remove_tag_from_all_paragraphs(tag_to_edit['id'])
                
                # Then delete the tag
                database.delete_tag(tag_to_edit['id'])
                st.success(f"✅ Tag '{tag_to_edit['name']}' deleted successfully and removed from {affected_count} paragraph(s)!")
            else:
                # No paragraphs assigned, safe to delete directly
                database.delete_tag(tag_to_edit['id'])
                st.success(f"✅ Tag '{tag_to_edit['name']}' deleted successfully!")
            
            # Clean up session state
            if f"confirm_delete_{tag_to_edit['id']}" in st.session_state:
                del st.session_state[f"confirm_delete_{tag_to_edit['id']}"]
            del st.session_state.editing_tag
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", key="cancel_delete"):
            # Clean up session state
            if f"confirm_delete_{tag_to_edit['id']}" in st.session_state:
                del st.session_state[f"confirm_delete_{tag_to_edit['id']}"]
            st.info("Tag deletion cancelled.")
            st.rerun()
    
    with col3:
        if st.button("↩️ Back to Edit", key="back_to_edit"):
            # Clean up session state
            if f"confirm_delete_{tag_to_edit['id']}" in st.session_state:
                del st.session_state[f"confirm_delete_{tag_to_edit['id']}"]
            st.rerun()


def _render_tags_list(tags: List[Dict[str, Any]]) -> None:
    """Render the hierarchical tags list with edit buttons using tree structure."""
    root_tags = [tag for tag in tags if tag['parent_tag_id'] is None]
    
    def render_tag_with_children(tag: Dict[str, Any], level: int = 0, is_last: bool = True, parent_prefixes: List[str] = None) -> None:
        """Recursively render a tag and all its children with proper tree structure."""
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
                st.markdown(f"🏷️ **{tag['name']}**")
            else:
                st.markdown(f"{prefix}🏷️ **{tag['name']}**")
            
            if tag['description']:
                description_prefix = prefix.replace("├─", "│ ").replace("└─", "  ") if level > 0 else "  "
                st.markdown(f"{description_prefix}*{tag['description']}*")
        
        with col2:
            if st.button("✏️ Edit", key=f"edit_tag_{tag['id']}", help="Edit this tag"):
                st.session_state.editing_tag = tag['id']
                st.rerun()
        
        # Find and render all children of this tag
        child_tags = [t for t in tags if t['parent_tag_id'] == tag['id']]
        
        # Update parent prefixes for children
        new_parent_prefixes = parent_prefixes.copy()
        if level > 0:
            if is_last:
                new_parent_prefixes.append("   ")  # Three spaces for completed branch
            else:
                new_parent_prefixes.append("│  ")  # Vertical line for continuing branch
        
        for i, child_tag in enumerate(child_tags):
            is_last_child = (i == len(child_tags) - 1)
            render_tag_with_children(child_tag, level + 1, is_last_child, new_parent_prefixes)
    
    # Render all root tags and their hierarchies
    for i, root_tag in enumerate(root_tags):
        is_last_root = (i == len(root_tags) - 1)
        render_tag_with_children(root_tag)
        if not is_last_root:
            st.divider()


def _get_valid_parent_options(database, tags: List[Dict[str, Any]], tag_id: int) -> Dict[str, int]:
    """Get valid parent options excluding circular references."""
    parent_options = {}
    for tag in tags:
        if tag['id'] != tag_id:
            # Don't allow circular references
            hierarchy = database.get_tag_hierarchy(tag['id'])
            if tag_id not in hierarchy:
                parent_options[tag['name']] = tag['id']
    return parent_options


def _get_current_parent_name(tags: List[Dict[str, Any]], parent_tag_id: Optional[int]) -> Optional[str]:
    """Get the current parent tag name."""
    if parent_tag_id:
        current_parent_tag = next((tag for tag in tags if tag['id'] == parent_tag_id), None)
        if current_parent_tag:
            return current_parent_tag['name']
    return None


def _handle_tag_update(database, parent_options: Dict[str, int], tag_id: int, 
                      new_name: str, new_description: str, new_parent: str) -> None:
    """Handle tag update."""
    try:
        new_parent_id = parent_options[new_parent] if new_parent else None
        database.update_tag(tag_id, new_name, new_description, new_parent_id)
        st.success(f"Tag '{new_name}' updated successfully!")
        del st.session_state.editing_tag
        st.rerun()
    except Exception as e:
        st.error(f"Error updating tag: {str(e)}")