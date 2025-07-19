"""
Add Tags to Paragraphs page module - Flashcard-style tagging workflow.
"""
import streamlit as st
import time
from typing import Dict, Any, List
from streamlit_shortcuts import shortcut_button, add_shortcuts
from ..components.ui_components import FlashcardNavigator
from ..utils.helpers import highlight_keywords, display_hierarchical_tags_with_indentation, display_matched_keywords
from ..utils.ollama_helper import create_ollama_tag_suggester
from ..database.base_database import BaseDatabaseInterface


def render_add_tags_page(database: BaseDatabaseInterface) -> None:
    """Render the Add Tags to Paragraphs page with flashcard interface."""
    st.header("📝 Add Tags to Paragraphs")
    
    # AI Tag Suggestions Settings
    with st.expander("🤖 AI Tag Suggestions Settings", expanded=False):
        enable_ai_suggestions = st.checkbox(
            "Enable automatic tag suggestions",
            value=st.session_state.get('enable_ai_suggestions', False),
            key='enable_ai_suggestions',
            help="Use Ollama to suggest relevant tags based on paragraph content"
        )
        
        if enable_ai_suggestions:
            # Model selection
            suggester = create_ollama_tag_suggester()
            available_models = suggester.get_available_models()
            
            if available_models:
                # Find current model index, defaulting to auto-detected model
                current_model = suggester.model_name
                try:
                    current_index = available_models.index(current_model)
                except ValueError:
                    current_index = 0
                
                st.selectbox(
                    "Select Ollama model:",
                    options=available_models,
                    index=current_index,
                    key='ollama_model',
                    help="Choose which Ollama model to use for tag suggestions"
                )
                
                # Show auto-detected model info
                if suggester.model_name != st.session_state.get('ollama_model'):
                    st.info(f"ℹ️ Auto-detected model: **{suggester.model_name}**")
                
                # AI Configuration Options
                st.markdown("**AI Configuration:**")
                
                # Number of suggestions
                num_suggestions = st.slider(
                    "Number of tag suggestions:",
                    min_value=1,
                    max_value=5,
                    value=st.session_state.get('ai_num_suggestions', 2),
                    key='ai_num_suggestions',
                    help="How many tag suggestions to generate per paragraph"
                )
                
                # Custom prompt toggle
                use_custom_prompt = st.checkbox(
                    "Use custom prompt",
                    value=st.session_state.get('ai_use_custom_prompt', False),
                    key='ai_use_custom_prompt',
                    help="Enable to customize the AI prompt template"
                )
                
                if use_custom_prompt:
                    st.markdown("**Custom Prompt Template:**")
                    st.markdown("""
                    Available placeholders:
                    - `{tag_structure}` - The hierarchical list of available tags
                    - `{paragraph_content}` - The paragraph text to analyze
                    - `{existing_tags}` - Tags already applied to this paragraph
                    - `{num_suggestions}` - Number of suggestions requested
                    """)
                    
                    default_prompt = """You are an expert at analyzing religious conference talks and suggesting appropriate tags.

{tag_structure}

Paragraph to analyze:
"{paragraph_content}"

Currently applied tags: {existing_tags}

Instructions:
1. First, carefully analyze the paragraph content to understand its main themes, concepts, and doctrines
2. For each potential tag, think through the reasoning BEFORE deciding to suggest it
3. Suggest exactly {num_suggestions} tags that would be most appropriate for this paragraph
4. Only suggest tags that exist EXACTLY as written in the provided tag hierarchy
5. Do not suggest tags that are already applied to this paragraph
6. For each suggestion, provide the reasoning first, then the tag name and confidence level
7. Focus on the main themes, concepts, or doctrines discussed in the paragraph
8. Consider both specific topics and broader theological themes
9. Confidence levels: "high" (very certain), "medium" (reasonably certain), "low" (possible but uncertain)

Structure your response as JSON with exactly {num_suggestions} tag suggestions. Each suggestion must include:
- reasoning: A detailed explanation of why this tag fits the paragraph content
- tag_name: The exact tag name from the available tags (must match exactly)
- confidence: Either "high", "medium", or "low"

Think step by step: analyze the content, consider the reasoning for each potential tag, then provide your {num_suggestions} best suggestions."""
                    
                    custom_prompt = st.text_area(
                        "Custom prompt template:",
                        value=st.session_state.get('ai_custom_prompt', default_prompt),
                        height=300,
                        key='ai_custom_prompt',
                        help="Write your custom prompt using the placeholders above"
                    )
                    
                    # Validate prompt
                    required_placeholders = ['{tag_structure}', '{paragraph_content}', '{num_suggestions}']
                    missing_placeholders = [p for p in required_placeholders if p not in custom_prompt]
                    
                    if missing_placeholders:
                        st.warning(f"⚠️ Missing required placeholders: {', '.join(missing_placeholders)}")
                    else:
                        st.success("✅ Prompt template is valid")
                
                # Temperature and other model parameters
                with st.expander("Advanced Model Parameters", expanded=False):
                    temperature = st.slider(
                        "Temperature (creativity):",
                        min_value=0.0,
                        max_value=1.0,
                        value=st.session_state.get('ai_temperature', 0.3),
                        step=0.1,
                        key='ai_temperature',
                        help="Lower values = more focused/consistent, Higher values = more creative/varied"
                    )
                    
                    top_p = st.slider(
                        "Top-p (nucleus sampling):",
                        min_value=0.1,
                        max_value=1.0,
                        value=st.session_state.get('ai_top_p', 0.9),
                        step=0.1,
                        key='ai_top_p',
                        help="Controls diversity of token selection"
                    )
                
            else:
                st.error("⚠️ No Ollama models found. Please ensure Ollama is running and has models installed.")
                st.info("To install a model, run: `ollama pull llama3.2` or `ollama pull gemma2`")
    
    # Keyboard shortcuts help section
    with st.expander("⌨️ Keyboard Shortcuts Guide", expanded=False):
        st.markdown("""
        **🧭 Navigation Shortcuts:**
        - `←/→ Arrow Keys` - Previous/Next paragraph
        - `Ctrl+←/→` - First/Last paragraph
        - `Shift+←/→` - Previous/Next unreviewed paragraph
        - `Ctrl+Shift+←/→` - First/Last unreviewed paragraph
        - `R` - Random paragraph
        - `F5` - Refresh page
        - `Enter` - Jump to paragraph (when in jump field)
        - `Ctrl+J` - Focus jump input field
        
        **🏷️ Tagging Shortcuts:**
        - `Ctrl+T` - Focus tag selector dropdown
        - `Ctrl+Enter` - Complete & move to next paragraph
        - `Ctrl+Shift+Enter` - Skip to next paragraph
        
        **📝 Notes Shortcuts:**
        - `Ctrl+N` - Focus notes textarea
        - `Ctrl+S` - Save notes
        
        **💡 Pro Tips:**
        - Use arrow keys for quick navigation through paragraphs
        - Use Shift+Arrow keys to jump between unreviewed paragraphs only
        - Use Ctrl+Enter to quickly mark paragraphs as complete and move forward
        - Use Ctrl+T to quickly access the tag selector without scrolling
        """)
    
    # Store paragraph list in session state to prevent re-querying after tag additions
    if 'add_tags_paragraph_list' not in st.session_state:
        # Load ALL paragraphs instead of just untagged ones
        st.session_state['add_tags_paragraph_list'] = database.get_all_paragraphs_with_filters()
    
    paragraphs = st.session_state['add_tags_paragraph_list']
    
    if paragraphs:
        # Initialize flashcard navigator with all paragraphs
        navigator = FlashcardNavigator(paragraphs, "add_tags_paragraph_index")
        
        
        st.markdown("---")
        
        # Get current paragraph
        current_paragraph = navigator.get_current_item()
        
        if current_paragraph:
            _render_tagging_flashcard(current_paragraph, database, navigator)
        
        # Render dual navigation system at the top
        navigator.render_dual_navigation()

    else:
        st.info("No paragraphs found in the database.")
        
        # Add button to refresh the list
        if st.button("🔄 Refresh List"):
            st.session_state.pop('add_tags_paragraph_list', None)
            st.rerun()


def _render_tagging_flashcard(paragraph: Dict[str, Any], database: BaseDatabaseInterface, navigator: FlashcardNavigator) -> None:
    """Render a single paragraph flashcard for tagging."""
    with st.container():
        # Get reviewed status for display
        reviewed_status = paragraph.get('reviewed', False)
        review_date = paragraph.get('review_date')
        
        # Talk information header with enhanced styling and reviewed status
        reviewed_indicator = ""
        if reviewed_status:
            reviewed_indicator = '<span style="background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-left: 10px;">✅ REVIEWED</span>'
            if review_date:
                import datetime
                try:
                    review_dt = datetime.datetime.fromisoformat(review_date)
                    reviewed_indicator += f'<span style="color: #6c757d; font-size: 10px; margin-left: 5px;">({review_dt.strftime("%m/%d/%Y")})</span>'
                except Exception:
                    pass
        else:
            reviewed_indicator = '<span style="background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-left: 10px;">⚠️ NOT REVIEWED</span>'
        
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1f4e7a, #2d5a87); color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="margin: 0; color: white;">📖 {paragraph['talk_title']}</h3>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">
                <strong>{paragraph['speaker']}</strong> • {paragraph['conference_date']} • Paragraph {paragraph['paragraph_number']}
                {reviewed_indicator}
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
        display_hierarchical_tags_with_indentation(paragraph['id'], database)
        
        st.divider()
        
        # AI Tag Suggestions (if enabled)
        if st.session_state.get('enable_ai_suggestions', False):
            _render_ai_tag_suggestions(paragraph, database)
        
        # Streamlined tagging interface
        _render_streamlined_tagging_interface(paragraph['id'], database, navigator)


def _render_ai_tag_suggestions(paragraph: Dict[str, Any], database: BaseDatabaseInterface) -> None:
    """Render AI-powered tag suggestions section with async background processing."""
    st.markdown("### 🤖 AI Tag Suggestions")
    
    # Get current tags for this paragraph
    current_tags_data = database.get_paragraph_tags(paragraph['id'])
    current_tag_names = [tag['name'] for tag in current_tags_data]
    
    # Get all tags for hierarchy
    all_tags = database.get_all_tags()
    
    # Get AI configuration from session state
    num_suggestions = st.session_state.get('ai_num_suggestions', 2)
    use_custom_prompt = st.session_state.get('ai_use_custom_prompt', False)
    custom_prompt = st.session_state.get('ai_custom_prompt', None) if use_custom_prompt else None
    
    # Create suggester and check availability
    suggester = create_ollama_tag_suggester()
    
    if not suggester.is_available():
        st.error("⚠️ Ollama is not available. Please ensure Ollama is running and the selected model is installed.")
        return
    
    # Sync any thread results to session state
    suggester._sync_thread_results_to_session_state()
    
    # Check for existing async request status
    paragraph_id = paragraph['id']
    request_status = suggester.get_request_status(paragraph_id)
    
    # Handle different request states
    if request_status.get('status') == 'pending':
        # Show pending status with option to cancel
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("🤖 AI is analyzing the paragraph... Please wait.")
            # Add a progress indicator
            progress_placeholder = st.empty()
            with progress_placeholder:
                st.progress(0.5, "Getting AI suggestions...")
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_ai_{paragraph_id}"):
                suggester.cancel_request(paragraph_id)
                st.info("AI request cancelled.")
                st.rerun()
        
        # Auto-refresh to check for completion (with a slower refresh rate to avoid constant reloading)
        time.sleep(0.5)
        st.rerun()
        
    elif request_status.get('status') == 'processing':
        # Show processing status
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("🧠 AI is thinking... This may take a few moments.")
            progress_placeholder = st.empty()
            with progress_placeholder:
                st.progress(0.8, "Processing with AI model...")
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_ai_{paragraph_id}"):
                suggester.cancel_request(paragraph_id)
                st.info("AI request cancelled.")
                st.rerun()
        
        # Auto-refresh to check for completion
        time.sleep(1.0)
        st.rerun()
        
    elif request_status.get('status') == 'completed':
        # Display the results
        suggestions = request_status.get('result')
        
        if suggestions:
            # Show configuration info
            config_info = f"**{len(suggestions)} suggestions"
            if use_custom_prompt:
                config_info += " (custom prompt)"
            config_info += ":**"
            st.markdown(config_info)
            
            for i, suggestion in enumerate(suggestions):
                tag_name = suggestion.get('tag_name', 'Unknown')
                confidence = suggestion.get('confidence', 'unknown')
                reasoning = suggestion.get('reasoning', 'No reasoning provided')
                
                # Find the tag in the database to get its ID
                tag_data = next((tag for tag in all_tags if tag['name'] == tag_name), None)
                
                if tag_data:
                    # Color code based on confidence
                    confidence_colors = {
                        'high': '#28a745',
                        'medium': '#ffc107', 
                        'low': '#dc3545'
                    }
                    confidence_color = confidence_colors.get(confidence, '#6c757d')
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="border: 1px solid #e0e0e0; padding: 12px; border-radius: 8px; margin-bottom: 10px; background-color: #f8f9fa;">
                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                <strong style="color: #007bff;">🏷️ {tag_name}</strong>
                                <span style="background-color: {confidence_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: 10px; font-weight: bold;">
                                    {confidence.upper()}
                                </span>
                            </div>
                            <div style="font-size: 14px; color: #6c757d; font-style: italic;">
                                {reasoning}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if tag_name not in current_tag_names:
                            if st.button(
                                "✨ Add", 
                                key=f"add_ai_suggestion_{paragraph_id}_{i}",
                                help=f"Add '{tag_name}' to this paragraph",
                                type="primary"
                            ):
                                database.tag_paragraph(paragraph_id, tag_data['id'])
                                st.success(f"✅ Added '{tag_name}'!")
                                # Clear AI suggestion cache when a tag is manually added
                                suggester.cancel_request(paragraph_id)
                                st.rerun()
                        else:
                            st.markdown("✅ *Already added*")
                else:
                    st.warning(f"⚠️ Suggested tag '{tag_name}' not found in database")
            
            # Button to refresh suggestions
            if st.button("🔄 Get New Suggestions", key=f"refresh_ai_{paragraph_id}"):
                # Cancel any existing request and start a new one
                suggester.cancel_request(paragraph_id)
                _start_async_ai_request(suggester, paragraph, all_tags, current_tag_names, 
                                      custom_prompt, num_suggestions)
                st.rerun()
        else:
            st.info("No AI suggestions available for this paragraph.")
            # Button to retry
            if st.button("🔄 Try Again", key=f"retry_ai_{paragraph_id}"):
                suggester.cancel_request(paragraph_id)
                _start_async_ai_request(suggester, paragraph, all_tags, current_tag_names, 
                                      custom_prompt, num_suggestions)
                st.rerun()
    
    elif request_status.get('status') == 'failed':
        # Show error and option to retry
        error_msg = request_status.get('error', 'Unknown error occurred')
        st.error(f"❌ AI request failed: {error_msg}")
        
        if st.button("🔄 Try Again", key=f"retry_failed_ai_{paragraph_id}"):
            suggester.cancel_request(paragraph_id)
            _start_async_ai_request(suggester, paragraph, all_tags, current_tag_names, 
                                  custom_prompt, num_suggestions)
            st.rerun()
    
    else:
        # No request in progress - show button to start one
        if st.button("🚀 Get AI Suggestions", key=f"start_ai_{paragraph_id}", type="primary"):
            _start_async_ai_request(suggester, paragraph, all_tags, current_tag_names, 
                                  custom_prompt, num_suggestions)
            st.rerun()
    
    st.divider()


def _start_async_ai_request(suggester, paragraph: Dict[str, Any], all_tags: List[Dict[str, Any]], 
                           current_tag_names: List[str], custom_prompt: str = None, 
                           num_suggestions: int = 2) -> None:
    """Start an asynchronous AI tag suggestion request."""
    paragraph_id = paragraph['id']
    
    # Get AI model parameters from session state
    temperature = st.session_state.get('ai_temperature', 0.3)
    top_p = st.session_state.get('ai_top_p', 0.9)
    
    # Start the async request
    suggester.suggest_tags_async(
        paragraph_id=paragraph_id,
        paragraph_content=paragraph['content'],
        tag_hierarchy=all_tags,
        existing_tags=current_tag_names,
        custom_prompt=custom_prompt,
        num_suggestions=num_suggestions,
        temperature=temperature,
        top_p=top_p
    )


def _render_streamlined_tagging_interface(paragraph_id: int, database: BaseDatabaseInterface, navigator: FlashcardNavigator) -> None:
    """Render streamlined tagging interface with hierarchical tag display."""
    st.markdown("### 🏷️ Add Tags")
    
    # Get all tags organized by hierarchy
    all_tags = database.get_all_tags()
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
                database.tag_paragraph(paragraph_id, selected_tag_id)
                st.success(f"✅ Added '{selected_tag_name}'!")
                
                # Mark this tag as processed for this paragraph
                st.session_state[last_processed_key] = selected_tag_name
                
                # Clear AI suggestions cache when a tag is manually added
                ai_cache_key = f"ai_suggestions_{paragraph_id}"
                st.session_state.pop(ai_cache_key, None)
                
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
                        tag_id = database.add_tag(new_tag_name, new_tag_description, parent_id)
                        database.tag_paragraph(paragraph_id, tag_id)
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
                        database.tag_paragraph(paragraph_id, tag['id'])
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
        _render_notes_section(paragraph_id, database)
    
    # Completion workflow
    st.divider()
    st.markdown("### ✅ Mark as Complete")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if shortcut_button(
            "✅ Complete & Next", 
            "ctrl+enter",
            type="primary", 
            key="complete_and_next",
            help="Mark as complete and move to next paragraph (Ctrl+Enter)"
        ):
            database.mark_paragraph_reviewed(paragraph_id, True)
            
            # Update the paragraph data in session state to reflect the reviewed status
            if 'add_tags_paragraph_list' in st.session_state:
                for i, para in enumerate(st.session_state['add_tags_paragraph_list']):
                    if para['id'] == paragraph_id:
                        st.session_state['add_tags_paragraph_list'][i]['reviewed'] = True
                        from datetime import datetime
                        st.session_state['add_tags_paragraph_list'][i]['review_date'] = datetime.now().isoformat()
                        break
            
            # Move to next paragraph automatically
            current_index = navigator.get_current_index()
            if current_index < navigator.total_items - 1:
                st.session_state[navigator.session_key] = current_index + 1
            st.success("✅ Paragraph marked as reviewed!")
            st.rerun()
    
    with col2:
        if shortcut_button(
            "⏭️ Skip for Now", 
            "ctrl+shift+enter",
            key="skip_paragraph",
            help="Skip to next paragraph without marking as complete (Ctrl+Shift+Enter)"
        ):
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
    
    # Add shortcuts for the tag selector dropdown
    add_shortcuts(
        **{f"tag_selector_dropdown_{paragraph_id}": "ctrl+t"}
    )


def _render_notes_section(paragraph_id: int, database: BaseDatabaseInterface) -> None:
    """Render the notes section for the paragraph."""
    # Get current paragraph data to access notes
    paragraph_data = database.get_paragraph_with_notes(paragraph_id)
    
    # Handle case where paragraph doesn't exist in database
    if paragraph_data is None:
        st.error(f"⚠️ Paragraph with ID {paragraph_id} not found in database. This may indicate a data synchronization issue.")
        if st.button("🔄 Refresh Paragraph List", key=f"refresh_from_notes_{paragraph_id}"):
            st.session_state.pop('add_tags_paragraph_list', None)
            st.rerun()
        return
    
    current_notes = paragraph_data.get('notes', '') or ''
    
    with st.form(f"notes_form_{paragraph_id}"):
        notes = st.text_area(
            "Add your notes about this paragraph:",
            value=current_notes,
            height=100,
            placeholder="What insights, connections, or thoughts do you have about this paragraph?",
            key=f"notes_textarea_{paragraph_id}"
        )
        
        if st.form_submit_button(
            "💾 Save Notes", 
            type="primary",
            help="Save notes (Ctrl+S)"
        ):
            database.update_paragraph_notes(paragraph_id, notes)
            st.success("✅ Notes saved!")
            st.rerun()
    
    # Add shortcuts for notes textarea and form submit
    add_shortcuts(
        **{
            f"notes_textarea_{paragraph_id}": "ctrl+n",
            f"notes_form_{paragraph_id}": "ctrl+s"
        }
    )