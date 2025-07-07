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

    def render_enhanced_navigation(self) -> None:
        """Render enhanced navigation controls with better styling and keyboard shortcuts."""
        if not self.items:
            return
            
        current_index = self.get_current_index()
        
        # Enhanced navigation with progress bar
        progress = (current_index + 1) / self.total_items
        st.progress(progress, text=f"Flashcard {current_index + 1} of {self.total_items}")
        
        # Navigation buttons with keyboard shortcuts
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])
        
        with col1:
            if st.button(
                "⬅️ Previous", 
                disabled=current_index == 0,
                help="Previous flashcard (Left Arrow)",
                key=f"prev_{self.session_key}"
            ):
                st.session_state[self.session_key] = current_index - 1
                st.rerun()
        
        with col2:
            if st.button(
                "➡️ Next", 
                disabled=current_index == self.total_items - 1,
                help="Next flashcard (Right Arrow)",
                key=f"next_{self.session_key}"
            ):
                st.session_state[self.session_key] = current_index + 1
                st.rerun()
        
        with col3:
            if st.button(
                "🔄 Random",
                help="Random flashcard (R key)",
                key=f"random_{self.session_key}"
            ):
                st.session_state[self.session_key] = get_random_index(self.total_items)
                st.rerun()
        
        with col4:
            if st.button(
                "⏭️ First",
                help="Go to first flashcard",
                key=f"first_{self.session_key}"
            ):
                st.session_state[self.session_key] = 0
                st.rerun()
        
        with col5:
            if st.button(
                "⏮️ Last",
                help="Go to last flashcard",
                key=f"last_{self.session_key}"
            ):
                st.session_state[self.session_key] = self.total_items - 1
                st.rerun()
        
        with col6:
            # Quick jump input
            jump_col1, jump_col2 = st.columns([2, 1])
            with jump_col1:
                jump_to = st.number_input(
                    "Jump to:", 
                    min_value=1, 
                    max_value=self.total_items,
                    value=current_index + 1, 
                    key=f"jump_input_enhanced_{self.session_key}",
                    help="Enter a number to jump to that flashcard"
                )
            with jump_col2:
                if st.button("Go", key=f"go_button_enhanced_{self.session_key}"):
                    st.session_state[self.session_key] = jump_to - 1
                    st.rerun()

    def render_floating_navigation(self) -> None:
        """Render floating navigation controls at the bottom of the page."""
        if not self.items:
            return
            
        current_index = self.get_current_index()
        
        # Create floating navigation container
        st.markdown("""
        <style>
        .floating-nav {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(28, 131, 225, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 50px;
            padding: 15px 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 15px;
            color: white;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Progress and navigation in columns
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⬅️", disabled=current_index == 0, key=f"floating_prev_{self.session_key}", help="Previous"):
                st.session_state[self.session_key] = current_index - 1
                st.rerun()
        
        with col2:
            if st.button("➡️", disabled=current_index == self.total_items - 1, key=f"floating_next_{self.session_key}", help="Next"):
                st.session_state[self.session_key] = current_index + 1
                st.rerun()
        
        with col3:
            progress = (current_index + 1) / self.total_items
            st.progress(progress, text=f"{current_index + 1} of {self.total_items}")
        
        with col4:
            if st.button("🔄", key=f"floating_random_{self.session_key}", help="Random"):
                st.session_state[self.session_key] = get_random_index(self.total_items)
                st.rerun()
        
        with col5:
            if st.button("⏭️", key=f"floating_first_{self.session_key}", help="First"):
                st.session_state[self.session_key] = 0
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
                            self.db.update_paragraph_reviewed_status()
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
                            self.db.update_paragraph_reviewed_status()
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
                                self.db.update_paragraph_reviewed_status()
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
                                        self.db.update_paragraph_reviewed_status()
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
                cancel_create = st.form_submit_button("❌ Cancel")
            
            if create_submitted and tag_name:
                try:
                    parent_id = parent_options[parent_tag] if parent_tag else None
                    tag_id = self.db.add_tag(tag_name, tag_description, parent_id)
                    
                    if self.paragraph_id:
                        # Add the new tag to the paragraph
                        self.db.tag_paragraph_with_hierarchy(self.paragraph_id, tag_id)
                        self.db.update_paragraph_reviewed_status()
                    
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
                            self.db.update_paragraph_reviewed_status()
                        
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
        with st.expander("🔍 Filter Options", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Tag filter
                all_tags = self.db.get_all_tags()
                tag_options = ["All Tags", "No Tags"] + [tag['name'] for tag in all_tags]
                selected_tag_filter = st.selectbox(
                    "Filter by Tag:",
                    options=tag_options,
                    index=1,  # Default to "No Tags"
                    help="Filter paragraphs by tag assignment"
                )
            
            with col2:
                # Keyword filter
                keywords = self.db.get_keywords()
                keyword_options = ["All Keywords"] + keywords
                selected_keyword_filter = st.selectbox(
                    "Filter by Keyword:",
                    options=keyword_options,
                    help="Filter paragraphs by keyword matches"
                )
            
            with col3:
                # Additional filters
                show_reviewed = st.checkbox(
                    "Include Reviewed", 
                    value=False,
                    help="Include paragraphs that have been reviewed"
                )
        
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
    
    def render_comprehensive_paragraph_filters(self) -> Dict[str, Any]:
        """Render comprehensive paragraph filtering controls for management interface."""
        with st.expander("🔍 Advanced Filter Options", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Tag filter
                all_tags = self.db.get_all_tags()
                tag_options = ["All Tags", "No Tags"] + [tag['name'] for tag in all_tags]
                selected_tag_filter = st.selectbox(
                    "Filter by Tag:",
                    options=tag_options,
                    help="Filter paragraphs by tag assignment"
                )
            
            with col2:
                # Keyword filter
                keywords = self.db.get_keywords()
                keyword_options = ["All Keywords"] + keywords
                selected_keyword_filter = st.selectbox(
                    "Filter by Keyword:",
                    options=keyword_options,
                    help="Filter paragraphs by keyword matches"
                )
            
            with col3:
                # Review status filter
                review_filter = st.selectbox(
                    "Review Status:",
                    options=["All", "Reviewed Only", "Unreviewed Only"],
                    help="Filter by review status"
                )
            
            with col4:
                # Date range filter
                conference_years = ["All Years"] + [str(year) for year in range(2000, 2026)]
                selected_year = st.selectbox(
                    "Conference Year:",
                    options=conference_years,
                    help="Filter by conference year"
                )
        
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
        
        reviewed_only = None
        if review_filter == "Reviewed Only":
            reviewed_only = True
        elif review_filter == "Unreviewed Only":
            reviewed_only = False
        
        return {
            'tag_filter': tag_filter,
            'keyword_filter': keyword_filter,
            'untagged_only': untagged_only,
            'reviewed_only': reviewed_only,
            'year_filter': selected_year if selected_year != "All Years" else None
        }