import streamlit as st
import pandas as pd
from database import ConferenceTalksDB
from datetime import datetime
import json

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
        search_button = st.button("🔍 Search", type="primary")
    
    if search_button and keywords_input:
        # Parse keywords
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        
        # Add new keywords to database
        db.add_keywords(keywords)
        
        # Search paragraphs
        with st.spinner("Searching paragraphs..."):
            results = db.search_paragraphs(keywords)
        
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
                        st.rerun()
                
                st.divider()

elif page == "📚 Manage Talks":
    st.header("Manage Talks")
    
    # Add new talk
    with st.expander("Add New Talk", expanded=False):
        with st.form("add_talk_form"):
            title = st.text_input("Talk Title")
            speaker = st.text_input("Speaker")
            conference_date = st.text_input("Conference Date (e.g., 'April 2023')")
            session = st.text_input("Session (optional)")
            hyperlink = st.text_input("Hyperlink URL")
            
            submitted = st.form_submit_button("Add Talk")
            
            if submitted and title and speaker and conference_date and hyperlink:
                talk_id = db.add_talk(title, speaker, conference_date, hyperlink, session)
                st.success(f"Talk added with ID: {talk_id}")
                st.rerun()
    
    # Display existing talks
    st.subheader("Existing Talks")
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
    else:
        st.info("No talks added yet.")

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
    
    # Display existing tags
    st.subheader("Existing Tags")
    tags = db.get_all_tags()
    
    if tags:
        # Create hierarchical display
        root_tags = [tag for tag in tags if tag['parent_tag_id'] is None]
        child_tags = [tag for tag in tags if tag['parent_tag_id'] is not None]
        
        for root_tag in root_tags:
            st.markdown(f"**{root_tag['name']}**")
            if root_tag['description']:
                st.markdown(f"  *{root_tag['description']}*")
            
            # Display child tags
            children = [tag for tag in child_tags if tag['parent_tag_id'] == root_tag['id']]
            for child in children:
                st.markdown(f"  • {child['name']}")
                if child['description']:
                    st.markdown(f"    *{child['description']}*")
    else:
        st.info("No tags created yet.")

elif page == "🔤 Manage Keywords":
    st.header("Manage Keywords")
    
    # Add new keywords
    with st.expander("Add New Keywords", expanded=False):
        keywords_input = st.text_area(
            "Enter keywords (one per line or comma-separated):",
            placeholder="light\ntechnology\ngospel\nfaith"
        )
        
        if st.button("Add Keywords"):
            if keywords_input:
                # Parse keywords (handle both newlines and commas)
                keywords = []
                for line in keywords_input.split('\n'):
                    if ',' in line:
                        keywords.extend([k.strip() for k in line.split(',') if k.strip()])
                    else:
                        if line.strip():
                            keywords.append(line.strip())
                
                db.add_keywords(keywords)
                st.success(f"Added {len(keywords)} keywords")
                st.rerun()
    
    # Display existing keywords
    st.subheader("Existing Keywords")
    keywords = db.get_keywords()
    
    if keywords:
        # Display in columns
        cols = st.columns(4)
        for i, keyword in enumerate(keywords):
            with cols[i % 4]:
                st.text(keyword)
    else:
        st.info("No keywords added yet.")

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
st.sidebar.markdown("• Use specific keywords for better results")
st.sidebar.markdown("• Create hierarchical tags for better organization")
st.sidebar.markdown("• Review paragraphs to track progress")