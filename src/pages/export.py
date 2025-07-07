"""
Export page for the Conference Talks Analysis application.
Allows users to export database content to markdown format.
"""
import streamlit as st
import os
from datetime import datetime
from typing import Dict

def render_export_page(db):
    """Render the export page."""
    st.header("📤 Export Database")
    st.markdown("Export your tagged conference talks to a markdown file organized by tag hierarchy.")
    
    # Export options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File name input
        default_filename = f"conference_talks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filename = st.text_input("Export filename:", value=default_filename)
        
        # Export location
        export_location = st.selectbox(
            "Export location:",
            ["Current directory", "Downloads folder", "Custom path"]
        )
        
        if export_location == "Custom path":
            custom_path = st.text_input("Custom path:", placeholder="Enter full path to directory")
        else:
            custom_path = None
    
    with col2:
        st.markdown("### Export Preview")
        
        # Get some stats about what will be exported
        all_tags = db.get_all_tags()
        root_tags = [tag for tag in all_tags if tag['parent_tag_id'] is None]
        
        # Count paragraphs with tags
        conn = db.conn if hasattr(db, 'conn') else None
        if not conn:
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT paragraph_id) FROM paragraph_tags")
        tagged_paragraphs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM paragraphs")
        total_paragraphs = cursor.fetchone()[0]
        
        if not hasattr(db, 'conn'):
            conn.close()
        
        st.metric("Root Tags", len(root_tags))
        st.metric("Total Tags", len(all_tags))
        st.metric("Tagged Paragraphs", tagged_paragraphs)
        st.metric("Total Paragraphs", total_paragraphs)
    
    st.markdown("---")
    
    # Export format explanation
    with st.expander("📋 Export Format Details", expanded=False):
        st.markdown("""
        **Markdown Structure:**
        - Root tags become H1 headings (`#`)
        - Child tags become H2 headings (`##`)
        - Grandchild tags become H3 headings (`###`), etc.
        
        **For each paragraph under a tag:**
        - Paragraph text as a bullet point
        - Keywords listed with indentation
        - User notes (if any) with indentation
        - Cross-references to other tags (if paragraph appears in multiple tags)
        - Source information (speaker, talk title, conference date)
        
        **Example:**
        ```markdown
        # Gospel Principles
        
        ## Faith
        
        • Faith is the substance of things hoped for, the evidence of things not seen.
          - **Keywords:** faith, hope, evidence
          - **Note:** Key verse about faith
          - **Also found under:** Spiritual Growth, New Testament
          - **Source:** Elder Smith - On Faith (April 2020)
        ```
        """)
    
    # Export buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔍 Preview Export", type="secondary"):
            with st.spinner("Generating preview..."):
                try:
                    # Generate a limited preview (first few tags only)
                    preview_content = _generate_export_preview(db)
                    
                    st.markdown("### Export Preview (First 500 characters)")
                    st.code(preview_content[:500] + "..." if len(preview_content) > 500 else preview_content, language="markdown")
                    
                    if len(preview_content) > 500:
                        with st.expander("Show full preview"):
                            st.code(preview_content, language="markdown")
                            
                except Exception as e:
                    st.error(f"Error generating preview: {str(e)}")
    
    with col2:
        if st.button("📤 Export to File", type="primary"):
            with st.spinner("Generating export file..."):
                try:
                    # Determine output path
                    if export_location == "Downloads folder":
                        # Try to find downloads folder
                        home_dir = os.path.expanduser("~")
                        output_path = os.path.join(home_dir, "Downloads", filename)
                    elif export_location == "Custom path" and custom_path:
                        output_path = os.path.join(custom_path, filename)
                    else:
                        output_path = filename
                    
                    # Generate and save export
                    markdown_content = db.export_to_markdown(output_path)
                    
                    # Success message with file info
                    file_size = len(markdown_content.encode('utf-8'))
                    st.success(f"✅ Export completed!")
                    st.info(f"**File:** {output_path}\n**Size:** {file_size:,} bytes")
                    
                    # Offer download if file is in current directory
                    if export_location == "Current directory" or not custom_path:
                        try:
                            with open(output_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            
                            st.download_button(
                                label="💾 Download File",
                                data=file_content,
                                file_name=filename,
                                mime="text/markdown",
                                help="Download the exported file to your browser's download folder"
                            )
                        except Exception as e:
                            st.warning(f"File created but download button failed: {str(e)}")
                    
                except Exception as e:
                    st.error(f"Error during export: {str(e)}")
    
    with col3:
        if st.button("📋 Copy to Clipboard"):
            with st.spinner("Generating content..."):
                try:
                    markdown_content = db.export_to_markdown()
                    
                    # Display content in a text area for easy copying
                    st.markdown("### Copy the content below:")
                    st.text_area(
                        "Markdown content:",
                        value=markdown_content,
                        height=400,
                        help="Select all (Ctrl+A) and copy (Ctrl+C)"
                    )
                    
                    st.info("💡 Use Ctrl+A to select all, then Ctrl+C to copy")
                    
                except Exception as e:
                    st.error(f"Error generating content: {str(e)}")
    
    # Additional options
    st.markdown("---")
    st.markdown("### Additional Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗂️ Export Statistics"):
            _show_export_statistics(db)
    
    with col2:
        if st.button("🔧 Database Info"):
            _show_database_info(db)


def _generate_export_preview(db) -> str:
    """Generate a limited preview of the export."""
    # Get just the first few root tags for preview
    all_tags = db.get_all_tags()
    root_tags = [tag for tag in all_tags if tag['parent_tag_id'] is None]
    
    if not root_tags:
        return "No tags found in database."
    
    # Generate preview with first 2 root tags only
    preview_tags = sorted(root_tags, key=lambda x: x['name'])[:2]
    
    markdown_content = []
    markdown_content.append("# Conference Talks Database Export (PREVIEW)\n")
    markdown_content.append(f"*Preview generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    markdown_content.append("*This preview shows only the first 2 root tags. Full export will include all tags.*\n")
    
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Build tags dict for hierarchy
    tags_dict = {}
    for tag in all_tags:
        tag_info = {
            'id': tag['id'],
            'name': tag['name'],
            'description': tag['description'],
            'parent_id': tag['parent_tag_id'],
            'children': []
        }
        tags_dict[tag['id']] = tag_info
    
    # Build parent-child relationships
    for tag_info in tags_dict.values():
        if tag_info['parent_id'] is not None:
            parent = tags_dict.get(tag_info['parent_id'])
            if parent:
                parent['children'].append(tag_info)
    
    for root_tag in preview_tags:
        tag_info = tags_dict[root_tag['id']]
        db._export_tag_hierarchy(tag_info, markdown_content, cursor, level=1)
    
    if len(root_tags) > 2:
        markdown_content.append(f"\n*... and {len(root_tags) - 2} more root tags in full export*")
    
    conn.close()
    return '\n'.join(markdown_content)


def _show_export_statistics(db):
    """Show detailed statistics about what will be exported."""
    import sqlite3
    
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    st.markdown("### 📊 Export Statistics")
    
    # Tag statistics
    cursor.execute("SELECT COUNT(*) FROM tags")
    total_tags = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tags WHERE parent_tag_id IS NULL")
    root_tags = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tags WHERE parent_tag_id IS NOT NULL")
    child_tags = cursor.fetchone()[0]
    
    # Paragraph statistics
    cursor.execute("SELECT COUNT(*) FROM paragraphs")
    total_paragraphs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT paragraph_id) FROM paragraph_tags")
    tagged_paragraphs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM paragraphs WHERE notes IS NOT NULL AND notes != ''")
    paragraphs_with_notes = cursor.fetchone()[0]
    
    # Keyword statistics
    cursor.execute("SELECT COUNT(*) FROM keywords")
    total_keywords = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT keyword_id) FROM paragraph_keywords")
    used_keywords = cursor.fetchone()[0]
    
    # Display in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Tags", total_tags)
        st.metric("Root Tags", root_tags)
        st.metric("Child Tags", child_tags)
    
    with col2:
        st.metric("Total Paragraphs", total_paragraphs)
        st.metric("Tagged Paragraphs", tagged_paragraphs)
        st.metric("Paragraphs with Notes", paragraphs_with_notes)
    
    with col3:
        st.metric("Total Keywords", total_keywords)
        st.metric("Used Keywords", used_keywords)
        untagged = total_paragraphs - tagged_paragraphs
        st.metric("Untagged Paragraphs", untagged)
    
    # Top tags by paragraph count
    cursor.execute("""
        SELECT t.name, COUNT(pt.paragraph_id) as count
        FROM tags t
        LEFT JOIN paragraph_tags pt ON t.id = pt.tag_id
        GROUP BY t.id, t.name
        ORDER BY count DESC
        LIMIT 10
    """)
    
    top_tags = cursor.fetchall()
    
    if top_tags:
        st.markdown("### 🏷️ Top Tags by Paragraph Count")
        for i, (tag_name, count) in enumerate(top_tags, 1):
            st.write(f"{i}. **{tag_name}**: {count} paragraphs")
    
    conn.close()


def _show_database_info(db):
    """Show general database information."""
    st.markdown("### 🗄️ Database Information")
    
    # Database file info
    if os.path.exists(db.db_path):
        file_size = os.path.getsize(db.db_path)
        file_modified = datetime.fromtimestamp(os.path.getmtime(db.db_path))
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Database Path:** {db.db_path}")
            st.write(f"**File Size:** {file_size:,} bytes")
        
        with col2:
            st.write(f"**Last Modified:** {file_modified.strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Data Path:** {db.data_path}")
    
    # Schema info
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    st.markdown("**Database Tables:**")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        st.write(f"• {table[0]}: {count:,} records")
    
    conn.close()