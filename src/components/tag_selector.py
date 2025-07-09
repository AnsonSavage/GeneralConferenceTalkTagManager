"""
Tag selection and management component for the Conference Talks Analysis application.
"""
import streamlit as st
from ..database.base_database import BaseDatabaseInterface


class TagSelector:
    """Component for selecting and managing tags."""
    
    def __init__(self, db: BaseDatabaseInterface, paragraph_id: int = None):
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
                                    st.success(f"Added tag '{tag['name']}' with hierarchy!")
                                    st.rerun()
                                return tag
                else:
                    st.info("No matching tags found.")
                    
                    # Option to create new tag
                    if st.button(f"➕ Create tag '{tag_search}'", key=f"create_tag_{key_suffix}"):
                        # Use a different approach to trigger tag creation
                        if f'creating_tag_{key_suffix}' not in st.session_state:
                            st.session_state[f'creating_tag_{key_suffix}'] = tag_search
                        st.rerun()
        
        with col2:
            # Use button callback instead of directly setting session state
            show_all_key = f'show_all_tags_{key_suffix}'
            if st.button("🏷️ Show All Tags", key=f"show_all_tags_btn_{key_suffix}"):
                # Set the state only if it doesn't exist yet
                if show_all_key not in st.session_state:
                    st.session_state[show_all_key] = True
                st.rerun()

    def render_enhanced_tag_search(self, key_suffix: str = "") -> None:
        """Render enhanced tag search interface with real-time autocomplete functionality."""
        # Search input with live filtering using on_change callback
        tag_search_key = f"enhanced_tag_search_{key_suffix}"
        
        # Clear search field if flag is set
        if st.session_state.get(f"clear_search_{key_suffix}", False):
            st.session_state[tag_search_key] = ""
            st.session_state[f"tag_suggestions_{key_suffix}"] = []
            st.session_state[f"clear_search_{key_suffix}"] = False
        
        def update_tag_suggestions():
            """Callback to update tag suggestions in real-time."""
            search_term = st.session_state.get(tag_search_key, "")
            if search_term:
                st.session_state[f"tag_suggestions_{key_suffix}"] = self.db.search_tags(search_term)
            else:
                st.session_state[f"tag_suggestions_{key_suffix}"] = []
        
        tag_search = st.text_input(
            "🔍 Search or create tags:",
            key=tag_search_key,
            placeholder="Start typing to search existing tags or create new ones...",
            help="Search for existing tags or type a new tag name to create it",
            on_change=update_tag_suggestions
        )
        
        # Get current suggestions from session state
        matching_tags = st.session_state.get(f"tag_suggestions_{key_suffix}", [])
        
        if tag_search and matching_tags:
            st.markdown("**🎯 Matching tags:**")
            
            # Add dropdown selection for matching tags
            if len(matching_tags) > 1:
                tag_options = [f"{tag['name']} - {tag['description'] or 'No description'}" for tag in matching_tags]
                selected_option = st.selectbox(
                    "Select a tag to add:",
                    options=[""] + tag_options,
                    key=f"tag_dropdown_{key_suffix}",
                    help="Use arrow keys to navigate and Enter to select"
                )
                
                if selected_option:
                    # Find the selected tag
                    selected_tag_name = selected_option.split(" - ")[0]
                    selected_tag = next((tag for tag in matching_tags if tag['name'] == selected_tag_name), None)
                    
                    if selected_tag and st.button("➕ Add Selected Tag", key=f"add_selected_{key_suffix}"):
                        if self.paragraph_id:
                            self.db.tag_paragraph_with_hierarchy(self.paragraph_id, selected_tag['id'])
                            # Set flag to clear search and suggestions
                            st.session_state[f"clear_search_{key_suffix}"] = True
                            st.success(f"✅ Added '{selected_tag['name']}' with hierarchy!")
                            st.rerun()
            
            # Display matching tags in a more compact format
            st.markdown("**Quick add buttons:**")
            cols = st.columns(min(len(matching_tags), 3))
            for i, tag in enumerate(matching_tags[:6]):  # Limit to 6 matches for better layout
                with cols[i % 3]:
                    if st.button(f"➕ {tag['name']}", key=f"add_enhanced_{tag['id']}_{key_suffix}"):
                        if self.paragraph_id:
                            self.db.tag_paragraph_with_hierarchy(self.paragraph_id, tag['id'])
                            # Set flag to clear search and suggestions
                            st.session_state[f"clear_search_{key_suffix}"] = True
                            st.success(f"✅ Added '{tag['name']}' with hierarchy!")
                            st.rerun()
        
        elif tag_search and not matching_tags:
            st.info(f"No matching tags found for '{tag_search}'")
            # Always show option to create new tag
            if st.button(f"✨ Create new tag: **{tag_search}**", key=f"create_enhanced_{key_suffix}"):
                st.session_state[f'creating_enhanced_tag_{key_suffix}'] = tag_search
                st.rerun()
        
        # Handle tag creation
        self._handle_enhanced_tag_creation(key_suffix)

    def render_enhanced_all_tags(self, key_suffix: str = "") -> None:
        """Render enhanced view of all tags with hierarchical organization."""
        if not self.all_tags:
            st.info("No tags available. Create some tags first!")
            return
        
        # Group tags by parent
        root_tags = [tag for tag in self.all_tags if tag['parent_tag_id'] is None]
        
        # Search within all tags
        search_all = st.text_input(
            "🔍 Filter all tags:",
            key=f"filter_all_tags_{key_suffix}",
            placeholder="Filter the tag list..."
        )
        
        filtered_tags = root_tags
        if search_all:
            filtered_tags = [tag for tag in root_tags if search_all.lower() in tag['name'].lower()]
        
        if filtered_tags:
            for root_tag in filtered_tags:
                with st.expander(f"🏷️ {root_tag['name']}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if root_tag['description']:
                            st.markdown(f"*{root_tag['description']}*")
                    with col2:
                        if st.button("➕ Add", key=f"add_root_enhanced_{root_tag['id']}_{key_suffix}"):
                            if self.paragraph_id:
                                self.db.tag_paragraph_with_hierarchy(self.paragraph_id, root_tag['id'])
                                st.success(f"Added '{root_tag['name']}'!")
                                st.rerun()
                    
                    # Show child tags
                    child_tags = [tag for tag in self.all_tags if tag['parent_tag_id'] == root_tag['id']]
                    if child_tags:
                        st.markdown("**Sub-tags:**")
                        for child_tag in child_tags:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"  • {child_tag['name']}")
                                if child_tag['description']:
                                    st.caption(f"    {child_tag['description']}")
                            with col2:
                                if st.button("➕", key=f"add_child_enhanced_{child_tag['id']}_{key_suffix}"):
                                    if self.paragraph_id:
                                        self.db.tag_paragraph_with_hierarchy(self.paragraph_id, child_tag['id'])
                                        st.success(f"Added '{child_tag['name']}' with hierarchy!")
                                        st.rerun()
        else:
            st.info("No tags match your filter.")

    def render_enhanced_tag_creation(self, key_suffix: str = "") -> None:
        """Render enhanced tag creation interface."""
        st.markdown("**✨ Create a new tag:**")
        
        with st.form(f"create_new_tag_form_{key_suffix}"):
            tag_name = st.text_input("Tag name:", placeholder="Enter tag name...")
            tag_description = st.text_area("Description (optional):", placeholder="Describe what this tag represents...")
            
            # Parent tag selection with search
            parent_options = {tag['name']: tag['id'] for tag in self.all_tags}
            parent_tag = st.selectbox(
                "Parent Tag (optional):",
                options=[""] + list(parent_options.keys()),
                help="Select a parent tag to create a hierarchy"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                create_submitted = st.form_submit_button("✨ Create Tag", type="primary")
            with col2:
                st.form_submit_button("❌ Cancel")
            
            if create_submitted and tag_name:
                try:
                    parent_id = parent_options[parent_tag] if parent_tag else None
                    tag_id = self.db.add_tag(tag_name, tag_description, parent_id)
                    
                    if self.paragraph_id:
                        # Add the new tag to the paragraph
                        self.db.tag_paragraph_with_hierarchy(self.paragraph_id, tag_id)
                    
                    st.success(f"Created tag '{tag_name}' and added to paragraph!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    def _handle_enhanced_tag_creation(self, key_suffix: str) -> None:
        """Handle the enhanced tag creation process."""
        creating_key = f'creating_enhanced_tag_{key_suffix}'
        
        if creating_key in st.session_state:
            tag_name = st.session_state[creating_key]
            
            with st.form(f"enhanced_create_form_{key_suffix}"):
                st.markdown(f"**Creating tag: '{tag_name}'**")
                
                tag_description = st.text_area("Description (optional):")
                
                # Parent tag selection
                parent_options = {tag['name']: tag['id'] for tag in self.all_tags}
                parent_tag = st.selectbox(
                    "Parent Tag (optional):",
                    options=[""] + list(parent_options.keys())
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    create_submitted = st.form_submit_button("✨ Create", type="primary")
                with col2:
                    cancel_create = st.form_submit_button("❌ Cancel")
                
                if create_submitted:
                    try:
                        parent_id = parent_options[parent_tag] if parent_tag else None
                        tag_id = self.db.add_tag(tag_name, tag_description, parent_id)
                        
                        if self.paragraph_id:
                            self.db.tag_paragraph_with_hierarchy(self.paragraph_id, tag_id)
                        
                        st.success(f"Created and added tag '{tag_name}'!")
                        del st.session_state[creating_key]
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                
                if cancel_create:
                    del st.session_state[creating_key]
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
                        if st.button("➕ Add", key=f"add_root_{root_tag['id']}_{key_suffix}"):
                            if self.paragraph_id:
                                self.db.tag_paragraph_with_hierarchy(self.paragraph_id, root_tag['id'])
                                st.success(f"Added tag '{root_tag['name']}'!")
                                st.rerun()
                    
                    # Show child tags
                    child_tags = [tag for tag in self.all_tags if tag['parent_tag_id'] == root_tag['id']]
                    for child_tag in child_tags:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"  • {child_tag['name']}")
                        with col2:
                            if st.button("➕ Add", key=f"add_child_{child_tag['id']}_{key_suffix}"):
                                if self.paragraph_id:
                                    self.db.tag_paragraph_with_hierarchy(self.paragraph_id, child_tag['id'])
                                    st.success(f"Added tag '{child_tag['name']}' with hierarchy!")
                                    st.rerun()
            
            if st.button("✖️ Close", key=f"close_all_tags_{key_suffix}"):
                del st.session_state[show_all_key]
                st.rerun()