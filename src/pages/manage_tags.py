"""
Manage Tags page module.
"""
import streamlit as st
import sqlite3
from typing import List, Dict, Any, Optional


def render_manage_tags_page(db) -> None:
    """Render the Manage Tags page."""
    st.header("Manage Tags")
    
    # Add new tag section
    _render_add_tag_section(db)
    
    # Display existing tags
    st.subheader("Existing Tags")
    tags = db.get_all_tags()
    
    if tags:
        # Check if we're editing a tag
        if 'editing_tag' in st.session_state:
            _render_tag_edit_form(db, tags)
        else:
            _render_tags_list(tags)
    else:
        st.info("No tags created yet.")


def _render_add_tag_section(db) -> None:
    """Render the add new tag section."""
    with st.expander("Add New Tag", expanded=False):
        with st.form("add_tag_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                tag_name = st.text_input("Tag Name")
                tag_description = st.text_area("Description (optional)")
            
            with col2:
                # Parent tag selection
                all_tags = db.get_all_tags()
                parent_options = {tag['name']: tag['id'] for tag in all_tags}
                
                parent_tag = st.selectbox(
                    "Parent Tag (optional):",
                    options=[""] + list(parent_options.keys())
                )
            
            submitted = st.form_submit_button("Add Tag")
            
            if submitted and tag_name:
                try:
                    parent_id = parent_options[parent_tag] if parent_tag else None
                    tag_id = db.add_tag(tag_name, tag_description, parent_id)
                    st.success(f"Tag '{tag_name}' added with ID: {tag_id}")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


def _render_tag_edit_form(db, tags: List[Dict[str, Any]]) -> None:
    """Render the tag editing form."""
    tag_to_edit = next((tag for tag in tags if tag['id'] == st.session_state.editing_tag), None)
    
    if tag_to_edit:
        st.markdown(f"**Editing Tag: {tag_to_edit['name']}**")
        
        with st.form("edit_tag_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Tag Name", value=tag_to_edit['name'])
                new_description = st.text_area("Description", value=tag_to_edit['description'] or "")
            
            with col2:
                # Parent tag selection (exclude circular references)
                parent_options = _get_valid_parent_options(db, tags, tag_to_edit['id'])
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
                _handle_tag_update(db, parent_options, tag_to_edit['id'], new_name, new_description, new_parent)
            
            if delete_submitted:
                _handle_tag_deletion(db, tag_to_edit)
            
            if cancel_edit:
                del st.session_state.editing_tag
                st.rerun()


def _render_tags_list(tags: List[Dict[str, Any]]) -> None:
    """Render the hierarchical tags list with edit buttons."""
    root_tags = [tag for tag in tags if tag['parent_tag_id'] is None]
    child_tags = [tag for tag in tags if tag['parent_tag_id'] is not None]
    
    for root_tag in root_tags:
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"**{root_tag['name']}**")
            if root_tag['description']:
                st.markdown(f"  *{root_tag['description']}*")
        
        with col2:
            if st.button("✏️ Edit", key=f"edit_root_{root_tag['id']}", help="Edit this tag"):
                st.session_state.editing_tag = root_tag['id']
                st.rerun()
        
        # Display child tags
        children = [tag for tag in child_tags if tag['parent_tag_id'] == root_tag['id']]
        for child in children:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"  • {child['name']}")
                if child['description']:
                    st.markdown(f"    *{child['description']}*")
            
            with col2:
                if st.button("✏️ Edit", key=f"edit_child_{child['id']}", help="Edit this tag"):
                    st.session_state.editing_tag = child['id']
                    st.rerun()
        
        st.divider()


def _get_valid_parent_options(db, tags: List[Dict[str, Any]], tag_id: int) -> Dict[str, int]:
    """Get valid parent options excluding circular references."""
    parent_options = {}
    for tag in tags:
        if tag['id'] != tag_id:
            # Don't allow circular references
            hierarchy = db.get_tag_hierarchy(tag['id'])
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


def _handle_tag_update(db, parent_options: Dict[str, int], tag_id: int, 
                      new_name: str, new_description: str, new_parent: str) -> None:
    """Handle tag update."""
    try:
        new_parent_id = parent_options[new_parent] if new_parent else None
        db.update_tag(tag_id, new_name, new_description, new_parent_id)
        st.success(f"Tag '{new_name}' updated successfully!")
        del st.session_state.editing_tag
        st.rerun()
    except Exception as e:
        st.error(f"Error updating tag: {str(e)}")


def _handle_tag_deletion(db, tag_to_edit: Dict[str, Any]) -> None:
    """Handle tag deletion with dependency checking."""
    # Check if tag has any paragraphs
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM paragraph_tags WHERE tag_id = ?", (tag_to_edit['id'],))
    paragraph_count = cursor.fetchone()[0]
    conn.close()
    
    if paragraph_count > 0:
        st.error(f"Cannot delete tag '{tag_to_edit['name']}' because it's assigned to {paragraph_count} paragraph(s). Remove it from all paragraphs first.")
    else:
        db.delete_tag(tag_to_edit['id'])
        st.success(f"Tag '{tag_to_edit['name']}' deleted successfully!")
        del st.session_state.editing_tag
        st.rerun()