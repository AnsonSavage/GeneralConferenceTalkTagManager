import streamlit as st
import pandas as pd
from database import ConferenceTalksDB
import sqlite3

# Initialize database
@st.cache_resource
def init_database():
    return ConferenceTalksDB()

db = init_database()

# Page configuration
st.set_page_config(
    page_title="Conference Talks Analysis",
    page_icon="📖",
    layout="wide"
)

st.title("📖 Conference Talks Analysis")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "🔍 Search & Tag",
    "📄 Manage Paragraphs", 
    "📚 Manage Talks",
    "🏷️ Manage Tags",
    "🔤 Manage Keywords",
    "📊 Summary"
])

# Main content based on page selection
if page == "🔍 Search & Tag":
    st.header("Search and Tag Paragraphs")
    
    # Keywords input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get existing keywords for suggestions
        existing_keywords = db.get_keywords()
        
        # Text input for keywords
        keywords_input = st.text_input(
            "Enter keywords (comma-separated):",
            placeholder="light, technology, gospel, faith"
        )
        
        # Display existing keywords as suggestions
        if existing_keywords:
            st.write("**Existing keywords:**")
            keywords_display = ", ".join(existing_keywords)
            st.text(keywords_display)
    
    with col2:
        match_whole_words = st.checkbox("Match whole words only", value=True)
        search_button = st.button("🔍 Search", type="primary")
    
    if search_button and keywords_input:
        # Parse keywords
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        
        # Search files and populate database with matching content
        with st.spinner("Scanning files for keywords..."):
            results = db.search_and_populate_database(keywords, match_whole_words=match_whole_words)
        
        st.success(f"Found {len(results)} paragraphs matching your keywords")
        
        # Store results in session state
        st.session_state.search_results = results
        st.session_state.search_keywords = keywords
    
    # Display search results
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.header("Search Results")
        
        # Get all tags for tagging interface
        all_tags = db.get_all_tags()
        tag_options = {tag['name']: tag['id'] for tag in all_tags}
        
        # Display each paragraph
        for i, result in enumerate(st.session_state.search_results):
            with st.expander(f"**{result['talk_title']}** - {result['speaker']} ({result['conference_date']}) - Para {result['paragraph_number']}", expanded=True):
                
                # Talk information
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Talk:** [{result['talk_title']}]({result['hyperlink']})")
                    st.markdown(f"**Speaker:** {result['speaker']}")
                    st.markdown(f"**Date:** {result['conference_date']}")
                    if result['session']:
                        st.markdown(f"**Session:** {result['session']}")
                
                with col2:
                    # Reviewed status
                    reviewed = st.checkbox(
                        "Reviewed", 
                        value=result['reviewed'], 
                        key=f"reviewed_{result['id']}"
                    )
                    
                    if reviewed != result['reviewed']:
                        db.mark_paragraph_reviewed(result['id'], reviewed)
                        st.rerun()
                
                # Paragraph content
                st.markdown("**Paragraph Content:**")
                
                # Highlight matched keywords
                content = result['content']
                for keyword in result['matched_keywords']:
                    content = content.replace(
                        keyword, 
                        f"**:red[{keyword}]**"
                    )
                    content = content.replace(
                        keyword.capitalize(), 
                        f"**:red[{keyword.capitalize()}]**"
                    )
                
                st.markdown(content)
                
                # Current tags
                current_tags = db.get_paragraph_tags(result['id'])
                if current_tags:
                    st.markdown("**Current Tags:**")
                    tag_cols = st.columns(len(current_tags))
                    for j, tag in enumerate(current_tags):
                        with tag_cols[j]:
                            if st.button(f"❌ {tag['name']}", key=f"remove_tag_{result['id']}_{tag['id']}"):
                                db.remove_tag_from_paragraph(result['id'], tag['id'])
                                st.rerun()
                
                # Add new tags
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if tag_options:
                        selected_tag = st.selectbox(
                            "Add Tag:",
                            options=[""] + list(tag_options.keys()),
                            key=f"tag_select_{result['id']}"
                        )
                    else:
                        st.info("No tags available. Create tags in the 'Manage Tags' section.")
                        selected_tag = None
                
                with col2:
                    if selected_tag and st.button("Add Tag", key=f"add_tag_{result['id']}"):
                        db.tag_paragraph(result['id'], tag_options[selected_tag])
                        # Clear the selection by removing from session state
                        if f"tag_select_{result['id']}" in st.session_state:
                            del st.session_state[f"tag_select_{result['id']}"]
                        st.success(f"Tag '{selected_tag}' added!")
                        st.rerun()
                
                st.divider()

elif page == "📄 Manage Paragraphs":
    st.header("Manage Paragraphs - Flashcard View")
    
    # Filter controls
    with st.expander("Filter Options", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Tag filter
            all_tags = db.get_all_tags()
            tag_options = ["All Tags", "No Tags"] + [tag['name'] for tag in all_tags]
            selected_tag_filter = st.selectbox(
                "Filter by Tag:",
                options=tag_options,
                index=1  # Default to "No Tags"
            )
        
        with col2:
            # Keyword filter
            keywords = db.get_keywords()
            keyword_options = ["All Keywords"] + keywords
            selected_keyword_filter = st.selectbox(
                "Filter by Keyword:",
                options=keyword_options
            )
        
        with col3:
            # Additional filters
            show_reviewed = st.checkbox("Include Reviewed", value=False)
    
    # Get filtered paragraphs
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
    
    # Load paragraphs
    paragraphs = db.get_all_paragraphs_with_filters(
        tag_filter=tag_filter,
        keyword_filter=keyword_filter,
        untagged_only=untagged_only
    )
    
    if paragraphs:
        # Initialize session state for flashcard navigation
        if 'current_paragraph_index' not in st.session_state:
            st.session_state.current_paragraph_index = 0
        
        # Ensure index is within bounds
        if st.session_state.current_paragraph_index >= len(paragraphs):
            st.session_state.current_paragraph_index = 0
        
        current_paragraph = paragraphs[st.session_state.current_paragraph_index]
        
        # Navigation controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=st.session_state.current_paragraph_index == 0):
                st.session_state.current_paragraph_index -= 1
                st.rerun()
        
        with col2:
            if st.button("➡️ Next", disabled=st.session_state.current_paragraph_index == len(paragraphs) - 1):
                st.session_state.current_paragraph_index += 1
                st.rerun()
        
        with col3:
            st.write(f"**Paragraph {st.session_state.current_paragraph_index + 1} of {len(paragraphs)}**")
        
        with col4:
            if st.button("🔄 Random"):
                import random
                st.session_state.current_paragraph_index = random.randint(0, len(paragraphs) - 1)
                st.rerun()
        
        with col5:
            jump_to = st.number_input("Jump to:", min_value=1, max_value=len(paragraphs), 
                                     value=st.session_state.current_paragraph_index + 1, key="jump_input")
            if st.button("Go"):
                st.session_state.current_paragraph_index = jump_to - 1
                st.rerun()
        
        st.divider()
        
        # Display current paragraph as flashcard
        with st.container():
            # Talk information header
            st.markdown(f"### {current_paragraph['talk_title']}")
            st.markdown(f"**Speaker:** {current_paragraph['speaker']} | **Date:** {current_paragraph['conference_date']} | **Paragraph:** {current_paragraph['paragraph_number']}")
            
            if current_paragraph['hyperlink']:
                st.markdown(f"[🔗 View Talk]({current_paragraph['hyperlink']})")
            
            # Paragraph content
            st.markdown("---")
            
            # Highlight keywords if keyword filter is active
            content = current_paragraph['content']
            if keyword_filter and keyword_filter != "All Keywords":
                content = content.replace(
                    keyword_filter, 
                    f"**:red[{keyword_filter}]**"
                )
                content = content.replace(
                    keyword_filter.capitalize(), 
                    f"**:red[{keyword_filter.capitalize()}]**"
                )
            
            st.markdown(content)
            st.markdown("---")
            
            # Tags section
            tag_data = db.get_paragraph_tags_with_hierarchy(current_paragraph['id'])
            
            if tag_data['explicit'] or tag_data['implicit']:
                st.markdown("**Current Tags:**")
                
                # Display explicit tags (removable)
                if tag_data['explicit']:
                    st.markdown("*Explicit tags:*")
                    cols = st.columns(len(tag_data['explicit']))
                    for i, tag in enumerate(tag_data['explicit']):
                        with cols[i]:
                            if st.button(f"❌ {tag['name']}", key=f"remove_explicit_{tag['id']}"):
                                db.remove_tag_from_paragraph(current_paragraph['id'], tag['id'])
                                # Update paragraph reviewed status
                                db.update_paragraph_reviewed_status()
                                st.rerun()
                
                # Display implicit tags (grayed out)
                if tag_data['implicit']:
                    st.markdown("*Implicit tags (from parent hierarchy):*")
                    cols = st.columns(len(tag_data['implicit']))
                    for i, tag in enumerate(tag_data['implicit']):
                        with cols[i]:
                            st.markdown(f"🔗 :gray[{tag['name']}]")
            else:
                st.info("No tags assigned to this paragraph yet.")
            
            # Tag search and addition
            st.markdown("**Add Tags:**")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Quick tag search
                tag_search = st.text_input(
                    "Search tags:",
                    key="tag_search",
                    placeholder="Type to search for tags..."
                )
                
                if tag_search:
                    matching_tags = db.search_tags(tag_search)
                    if matching_tags:
                        # Display matching tags as buttons
                        tag_cols = st.columns(min(len(matching_tags), 4))
                        for i, tag in enumerate(matching_tags):
                            with tag_cols[i % 4]:
                                if st.button(f"➕ {tag['name']}", key=f"add_existing_{tag['id']}"):
                                    db.tag_paragraph_with_hierarchy(current_paragraph['id'], tag['id'])
                                    # Update paragraph reviewed status
                                    db.update_paragraph_reviewed_status()
                                    st.success(f"Added tag '{tag['name']}' with hierarchy!")
                                    st.rerun()
                    else:
                        st.info("No matching tags found.")
                        
                        # Option to create new tag
                        if st.button(f"➕ Create tag '{tag_search}'"):
                            st.session_state.creating_tag = tag_search
                            st.rerun()
            
            with col2:
                if st.button("🏷️ Show All Tags"):
                    st.session_state.show_all_tags = True
                    st.rerun()
            
            # Tag creation popup
            if 'creating_tag' in st.session_state:
                st.markdown("---")
                st.markdown(f"**Creating new tag: '{st.session_state.creating_tag}'**")
                
                with st.form("create_tag_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        tag_description = st.text_area("Description (optional):")
                    
                    with col2:
                        # Parent tag selection
                        parent_options = {tag['name']: tag['id'] for tag in all_tags}
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
                            tag_id = db.add_tag(st.session_state.creating_tag, tag_description, parent_id)
                            
                            # Add the new tag to the paragraph
                            db.tag_paragraph_with_hierarchy(current_paragraph['id'], tag_id)
                            # Update paragraph reviewed status
                            db.update_paragraph_reviewed_status()
                            
                            st.success(f"Tag '{st.session_state.creating_tag}' created and added!")
                            del st.session_state.creating_tag
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                    
                    if cancel_create:
                        del st.session_state.creating_tag
                        st.rerun()
            
            # Show all tags popup
            if 'show_all_tags' in st.session_state:
                st.markdown("---")
                st.markdown("**All Available Tags:**")
                
                if all_tags:
                    # Group tags by parent
                    root_tags = [tag for tag in all_tags if tag['parent_tag_id'] is None]
                    
                    for root_tag in root_tags:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{root_tag['name']}**")
                        with col2:
                            if st.button(f"➕ Add", key=f"add_root_{root_tag['id']}"):
                                db.tag_paragraph_with_hierarchy(current_paragraph['id'], root_tag['id'])
                                # Update paragraph reviewed status
                                db.update_paragraph_reviewed_status()
                                st.success(f"Added tag '{root_tag['name']}'!")
                                st.rerun()
                        
                        # Show child tags
                        child_tags = [tag for tag in all_tags if tag['parent_tag_id'] == root_tag['id']]
                        for child_tag in child_tags:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"  • {child_tag['name']}")
                            with col2:
                                if st.button(f"➕ Add", key=f"add_child_{child_tag['id']}"):
                                    db.tag_paragraph_with_hierarchy(current_paragraph['id'], child_tag['id'])
                                    # Update paragraph reviewed status
                                    db.update_paragraph_reviewed_status()
                                    st.success(f"Added tag '{child_tag['name']}' with hierarchy!")
                                    st.rerun()
                
                if st.button("✖️ Close"):
                    del st.session_state.show_all_tags
                    st.rerun()
    
    else:
        st.info("No paragraphs found with the current filters. Try adjusting your filter criteria.")

elif page == "📚 Manage Talks":
    st.header("Talks in Database")
    st.info("💡 Talks are automatically added to the database when you search for keywords. Only talks with matching paragraphs are stored.")
    
    # Display existing talks
    st.subheader("Talks with Keyword Matches")
    talks = db.get_talks_summary()
    
    if talks:
        df = pd.DataFrame(talks)
        
        # Make hyperlinks clickable
        df['hyperlink'] = df['hyperlink'].apply(lambda x: f"[Link]({x})")
        
        st.dataframe(
            df,
            column_config={
                "hyperlink": st.column_config.LinkColumn("Link"),
                "paragraph_count": "Paragraphs",
                "reviewed_count": "Reviewed"
            },
            use_container_width=True
        )
        
        # Show keyword associations
        st.subheader("Keyword Usage")
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT k.keyword, COUNT(DISTINCT pk.paragraph_id) as usage_count
            FROM keywords k
            JOIN paragraph_keywords pk ON k.id = pk.keyword_id
            GROUP BY k.keyword
            ORDER BY usage_count DESC
        """)
        
        keyword_usage = cursor.fetchall()
        conn.close()
        
        if keyword_usage:
            cols = st.columns(3)
            for i, (keyword, count) in enumerate(keyword_usage):
                with cols[i % 3]:
                    st.metric(keyword, count, help=f"Found in {count} paragraphs")
    else:
        st.info("No talks in database yet. Start by searching for keywords to populate the database with matching content.")

elif page == "🏷️ Manage Tags":
    st.header("Manage Tags")
    
    # Add new tag
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
    
    # Display existing tags with edit/delete options
    st.subheader("Existing Tags")
    tags = db.get_all_tags()
    
    if tags:
        # Check if we're editing a tag
        if 'editing_tag' in st.session_state:
            tag_to_edit = next((tag for tag in tags if tag['id'] == st.session_state.editing_tag), None)
            
            if tag_to_edit:
                st.markdown(f"**Editing Tag: {tag_to_edit['name']}**")
                
                with st.form("edit_tag_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_name = st.text_input("Tag Name", value=tag_to_edit['name'])
                        new_description = st.text_area("Description", value=tag_to_edit['description'] or "")
                    
                    with col2:
                        # Parent tag selection (exclude the tag being edited and its descendants)
                        parent_options = {}
                        for tag in tags:
                            if tag['id'] != tag_to_edit['id']:
                                # Don't allow circular references
                                hierarchy = db.get_tag_hierarchy(tag['id'])
                                if tag_to_edit['id'] not in hierarchy:
                                    parent_options[tag['name']] = tag['id']
                        
                        current_parent = None
                        if tag_to_edit['parent_tag_id']:
                            current_parent_tag = next((tag for tag in tags if tag['id'] == tag_to_edit['parent_tag_id']), None)
                            if current_parent_tag:
                                current_parent = current_parent_tag['name']
                        
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
                        try:
                            new_parent_id = parent_options[new_parent] if new_parent else None
                            db.update_tag(tag_to_edit['id'], new_name, new_description, new_parent_id)
                            st.success(f"Tag '{new_name}' updated successfully!")
                            del st.session_state.editing_tag
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating tag: {str(e)}")
                    
                    if delete_submitted:
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
                    
                    if cancel_edit:
                        del st.session_state.editing_tag
                        st.rerun()
        
        else:
            # Display tags in hierarchical view with edit buttons
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
    
    else:
        st.info("No tags created yet.")

elif page == "🔤 Manage Keywords":
    st.header("Manage Keywords")
    
    st.info("💡 Keywords are automatically added when you search for them. Click on a keyword to see all matching paragraphs.")
    
    # Display existing keywords
    st.subheader("Existing Keywords")
    keywords = db.get_keywords()
    
    if keywords:
        # Check if we're viewing paragraphs for a specific keyword
        if 'viewing_keyword' in st.session_state:
            keyword = st.session_state.viewing_keyword
            st.subheader(f"Paragraphs matching '{keyword}'")
            
            # Back button
            if st.button("← Back to Keywords List"):
                del st.session_state.viewing_keyword
                st.rerun()
            
            # Get paragraphs for this keyword
            paragraphs = db.get_paragraphs_by_keyword(keyword)
            
            if paragraphs:
                st.write(f"Found {len(paragraphs)} paragraphs")
                
                # Display each paragraph
                for para in paragraphs:
                    with st.expander(f"**{para['talk_title']}** - {para['speaker']} ({para['conference_date']}) - Para {para['paragraph_number']}", expanded=False):
                        st.markdown(f"**Talk:** [{para['talk_title']}]({para['hyperlink']})")
                        st.markdown(f"**Speaker:** {para['speaker']}")
                        st.markdown(f"**Date:** {para['conference_date']}")
                        
                        # Highlight the keyword in the content
                        content = para['content']
                        content = content.replace(
                            keyword, 
                            f"**:red[{keyword}]**"
                        )
                        content = content.replace(
                            keyword.capitalize(), 
                            f"**:red[{keyword.capitalize()}]**"
                        )
                        
                        st.markdown("**Paragraph Content:**")
                        st.markdown(content)
                        
                        # Show review status
                        if para['reviewed']:
                            st.success(f"✅ Reviewed on {para['review_date']}")
                        else:
                            st.warning("⏳ Not reviewed yet")
            else:
                st.info("No paragraphs found for this keyword.")
        
        else:
            # Display keywords as clickable buttons with delete option
            st.write("Click on a keyword to see all matching paragraphs:")
            
            # Create columns for keyword display
            cols = st.columns(3)
            for i, keyword in enumerate(keywords):
                with cols[i % 3]:
                    # Keyword button and delete button in same row
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if st.button(f"🔍 {keyword}", key=f"view_keyword_{keyword}"):
                            st.session_state.viewing_keyword = keyword
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_keyword_{keyword}", help=f"Delete '{keyword}'"):
                            db.delete_keyword(keyword)
                            st.success(f"Keyword '{keyword}' deleted!")
                            st.rerun()
    else:
        st.info("No keywords added yet. Start by searching for keywords in the '🔍 Search & Tag' section.")

elif page == "📊 Summary":
    st.header("Project Summary")
    
    # Get statistics
    talks = db.get_talks_summary()
    all_tags = db.get_all_tags()
    keywords = db.get_keywords()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Talks", len(talks))
    
    with col2:
        total_paragraphs = sum(talk['paragraph_count'] for talk in talks)
        st.metric("Total Paragraphs", total_paragraphs)
    
    with col3:
        total_reviewed = sum(talk['reviewed_count'] for talk in talks)
        st.metric("Reviewed Paragraphs", total_reviewed)
    
    with col4:
        st.metric("Total Tags", len(all_tags))
    
    # Progress bar
    if total_paragraphs > 0:
        progress = total_reviewed / total_paragraphs
        st.progress(progress)
        st.write(f"Review Progress: {progress:.1%}")
    
    # Recent talks
    if talks:
        st.subheader("Recent Talks")
        recent_talks = talks[:5]  # Show first 5 (sorted by date DESC)
        
        for talk in recent_talks:
            st.markdown(f"**[{talk['title']}]({talk['hyperlink']})** - {talk['speaker']} ({talk['conference_date']})")
            st.markdown(f"Paragraphs: {talk['paragraph_count']}, Reviewed: {talk['reviewed_count']}")
            st.divider()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Tips:**")
st.sidebar.markdown("• Enter keywords to scan conference talks")
st.sidebar.markdown("• Only matching paragraphs are stored in database")
st.sidebar.markdown("• Use specific keywords for better results")
st.sidebar.markdown("• Create hierarchical tags for better organization")
st.sidebar.markdown("• Review paragraphs to track progress")