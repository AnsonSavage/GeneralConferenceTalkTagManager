"""
Reusable UI components for the Conference Talks Analysis application.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from ..utils.helpers import get_random_index, update_navigation_state


class FlashcardNavigator:
    """Component for navigating through items in a flashcard-style interface."""
    
    def __init__(self, items: List[Any], session_key: str = "current_index"):
        self.items = items
        self.session_key = session_key
        self.total_items = len(items)
        
    def get_current_index(self) -> int:
        """Get the current index from session state."""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = 0
        
        # Ensure index is within bounds
        if st.session_state[self.session_key] >= self.total_items:
            st.session_state[self.session_key] = 0
            
        return st.session_state[self.session_key]
    
    def get_current_item(self) -> Any:
        """Get the current item based on the index."""
        if not self.items:
            return None
        return self.items[self.get_current_index()]
    
    def render_navigation(self) -> None:
        """Render the navigation controls."""
        if not self.items:
            return
            
        current_index = self.get_current_index()
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=current_index == 0):
                st.session_state[self.session_key] = current_index - 1
                st.rerun()
        
        with col2:
            if st.button("➡️ Next", disabled=current_index == self.total_items - 1):
                st.session_state[self.session_key] = current_index + 1
                st.rerun()
        
        with col3:
            st.write(f"**Item {current_index + 1} of {self.total_items}**")
        
        with col4:
            if st.button("🔄 Random"):
                st.session_state[self.session_key] = get_random_index(self.total_items)
                st.rerun()
        
        with col5:
            jump_to = st.number_input(
                "Jump to:", 
                min_value=1, 
                max_value=self.total_items,
                value=current_index + 1, 
                key=f"jump_input_{self.session_key}"
            )
            if st.button("Go", key=f"go_button_{self.session_key}"):
                st.session_state[self.session_key] = jump_to - 1
                st.rerun()


class TagSelector:
    """Component for selecting and managing tags."""
    
    def __init__(self, db, paragraph_id: int = None):
        self.db = db
        self.paragraph_id = paragraph_id
        self.all_tags = db.get_all_tags()
    
    def render_tag_search(self, key_suffix: str = "") -> None:
        """Render tag search interface."""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            tag_search = st.text_input(
                "Search tags:",
                key=f"tag_search_{key_suffix}",
                placeholder="Type to search for tags..."
            )
            
            if tag_search:
                matching_tags = self.db.search_tags(tag_search)
                if matching_tags:
                    # Display matching tags as buttons
                    tag_cols = st.columns(min(len(matching_tags), 4))
                    for i, tag in enumerate(matching_tags):
                        with tag_cols[i % 4]:
                            if st.button(f"➕ {tag['name']}", key=f"add_existing_{tag['id']}_{key_suffix}"):
                                if self.paragraph_id:
                                    self.db.tag_paragraph_with_hierarchy(self.paragraph_id, tag['id'])
                                    self.db.update_paragraph_reviewed_status()
                                    st.success(f"Added tag '{tag['name']}' with hierarchy!")
                                    st.rerun()
                                return tag
                else:
                    st.info("No matching tags found.")
                    
                    # Option to create new tag
                    if st.button(f"➕ Create tag '{tag_search}'", key=f"create_tag_{key_suffix}"):
                        st.session_state[f'creating_tag_{key_suffix}'] = tag_search
                        st.rerun()
        
        with col2:
            if st.button("🏷️ Show All Tags", key=f"show_all_tags_{key_suffix}"):
                st.session_state[f'show_all_tags_{key_suffix}'] = True
                st.rerun()
    
    def render_tag_creation_popup(self, key_suffix: str = "") -> None:
        """Render tag creation popup."""
        creating_key = f'creating_tag_{key_suffix}'
        
        if creating_key in st.session_state:
            st.markdown("---")
            st.markdown(f"**Creating new tag: '{st.session_state[creating_key]}'**")
            
            with st.form(f"create_tag_form_{key_suffix}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    tag_description = st.text_area("Description (optional):")
                
                with col2:
                    # Parent tag selection
                    parent_options = {tag['name']: tag['id'] for tag in self.all_tags}
                    parent_tag = st.selectbox(
                        "Parent Tag (optional):",
                        options=[""] + list(parent_options.keys())
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    create_submitted = st.form_submit_button("Create Tag", type="primary")
                with col2:
                    cancel_create = st.form_submit_button("Cancel")
                
                if create_submitted:
                    try:
                        parent_id = parent_options[parent_tag] if parent_tag else None
                        tag_id = self.db.add_tag(st.session_state[creating_key], tag_description, parent_id)
                        
                        if self.paragraph_id:
                            # Add the new tag to the paragraph
                            self.db.tag_paragraph_with_hierarchy(self.paragraph_id, tag_id)
                            self.db.update_paragraph_reviewed_status()
                        
                        st.success(f"Tag '{st.session_state[creating_key]}' created!")
                        del st.session_state[creating_key]
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                
                if cancel_create:
                    del st.session_state[creating_key]
                    st.rerun()
    
    def render_all_tags_popup(self, key_suffix: str = "") -> None:
        """Render all tags popup."""
        show_all_key = f'show_all_tags_{key_suffix}'
        
        if show_all_key in st.session_state:
            st.markdown("---")
            st.markdown("**All Available Tags:**")
            
            if self.all_tags:
                # Group tags by parent
                root_tags = [tag for tag in self.all_tags if tag['parent_tag_id'] is None]
                
                for root_tag in root_tags:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{root_tag['name']}**")
                    with col2:
                        if st.button(f"➕ Add", key=f"add_root_{root_tag['id']}_{key_suffix}"):
                            if self.paragraph_id:
                                self.db.tag_paragraph_with_hierarchy(self.paragraph_id, root_tag['id'])
                                self.db.update_paragraph_reviewed_status()
                                st.success(f"Added tag '{root_tag['name']}'!")
                                st.rerun()
                    
                    # Show child tags
                    child_tags = [tag for tag in self.all_tags if tag['parent_tag_id'] == root_tag['id']]
                    for child_tag in child_tags:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"  • {child_tag['name']}")
                        with col2:
                            if st.button(f"➕ Add", key=f"add_child_{child_tag['id']}_{key_suffix}"):
                                if self.paragraph_id:
                                    self.db.tag_paragraph_with_hierarchy(self.paragraph_id, child_tag['id'])
                                    self.db.update_paragraph_reviewed_status()
                                    st.success(f"Added tag '{child_tag['name']}' with hierarchy!")
                                    st.rerun()
            
            if st.button("✖️ Close", key=f"close_all_tags_{key_suffix}"):
                del st.session_state[show_all_key]
                st.rerun()


class FilterControls:
    """Component for rendering filter controls."""
    
    def __init__(self, db):
        self.db = db
        
    def render_paragraph_filters(self) -> Dict[str, Any]:
        """Render paragraph filtering controls."""
        with st.expander("Filter Options", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Tag filter
                all_tags = self.db.get_all_tags()
                tag_options = ["All Tags", "No Tags"] + [tag['name'] for tag in all_tags]
                selected_tag_filter = st.selectbox(
                    "Filter by Tag:",
                    options=tag_options,
                    index=1  # Default to "No Tags"
                )
            
            with col2:
                # Keyword filter
                keywords = self.db.get_keywords()
                keyword_options = ["All Keywords"] + keywords
                selected_keyword_filter = st.selectbox(
                    "Filter by Keyword:",
                    options=keyword_options
                )
            
            with col3:
                # Additional filters
                show_reviewed = st.checkbox("Include Reviewed", value=False)
        
        # Process filters
        if selected_tag_filter == "All Tags":
            tag_filter = None
            untagged_only = False
        elif selected_tag_filter == "No Tags":
            tag_filter = None
            untagged_only = True
        else:
            tag_filter = selected_tag_filter
            untagged_only = False
        
        keyword_filter = selected_keyword_filter if selected_keyword_filter != "All Keywords" else None
        
        return {
            'tag_filter': tag_filter,
            'keyword_filter': keyword_filter,
            'untagged_only': untagged_only,
            'show_reviewed': show_reviewed
        }