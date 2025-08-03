"""
Export page for the Conference Talks Analysis application.
Allows users to export database content to markdown or CSV format.
"""
import streamlit as st
import os
from datetime import datetime
from ..database.base_database import BaseDatabaseInterface  

def render_export_page(database: BaseDatabaseInterface, export_manager) -> None:
    """Render the export page."""
    st.header("📤 Export Database")
    st.markdown("Export your tagged conference talks to markdown or CSV format.")
    
    # Export format selection
    export_format = st.radio(
        "Export format:",
        options=["📄 Markdown", "📊 CSV"],
        horizontal=True,
        help="Markdown is for viewing, CSV is for data backup/transfer"
    )
    
    # Export options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Initialize default filename/folder in session state if not exists
        if 'export_filename' not in st.session_state:
            if export_format == "📄 Markdown":
                st.session_state.export_filename = f"conference_talks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            else:
                st.session_state.export_filename = f"conference_talks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # File name or folder input
        if export_format == "📄 Markdown":
            filename = st.text_input(
                "Export filename:", 
                value=st.session_state.export_filename,
                key="filename_input",
                help="Enter your desired filename for the export"
            )
        else:
            filename = st.text_input(
                "Export filename prefix:", 
                value=st.session_state.export_filename,
                key="filename_input",
                help="Enter the prefix for CSV files (multiple files will be created)"
            )
        
        # Update session state when user changes the filename
        if filename != st.session_state.export_filename:
            st.session_state.export_filename = filename
        
        # Markdown-specific options
        if export_format == "📄 Markdown":
            st.markdown("**Markdown Options:**")
            bold_keywords = st.checkbox(
                "Bold keywords in paragraph content",
                value=True,
                help="When enabled, matched keywords will be **bolded** in the paragraph text for better readability"
            )
        
        # Export location - different options for CSV vs Markdown
        if export_format == "📄 Markdown":
            export_location = st.selectbox(
                "Export location:",
                ["Current directory", "Downloads folder", "Custom path"]
            )
        else:
            export_location = st.selectbox(
                "Export folder:",
                ["Current directory", "Downloads folder", "Custom folder"]
            )
        
        if export_location in ["Custom path", "Custom folder"]:
            custom_path = st.text_input("Custom path:", placeholder="Enter full path to directory")
        else:
            custom_path = None
    
    with col2:
        st.markdown("### Export Preview")
        
        # Get export statistics
        stats = database.get_export_statistics()
        
        st.metric("Root Tags", stats['root_tags'])
        st.metric("Total Tags", stats['total_tags'])
        st.metric("Tagged Paragraphs", stats['tagged_paragraphs'])
        st.metric("Total Paragraphs", stats['total_paragraphs'])
    
    st.markdown("---")
    
    # Export format explanation
    if export_format == "📄 Markdown":
        _show_markdown_format_info()
    else:
        _show_csv_format_info()
    
    # Export buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔍 Preview Export", type="secondary"):
            with st.spinner("Generating preview..."):
                try:
                    if export_format == "📄 Markdown":
                        # Generate a limited preview (first few tags only)
                        preview_content = _generate_export_preview(database)
                        
                        st.markdown("### Export Preview (First 500 characters)")
                        st.code(preview_content[:500] + "..." if len(preview_content) > 500 else preview_content, language="markdown")
                        
                        if len(preview_content) > 500:
                            with st.expander("Show full preview"):
                                st.code(preview_content, language="markdown")
                    else:
                        # CSV preview
                        st.markdown("### CSV Export Preview")
                        st.info("CSV export will create the following files:")
                        st.write("- `{prefix}_talks.csv` - Conference talks metadata")
                        st.write("- `{prefix}_paragraphs.csv` - Paragraph content with notes")
                        st.write("- `{prefix}_tags.csv` - Tag hierarchy and descriptions")
                        st.write("- `{prefix}_paragraph_tags.csv` - Paragraph-tag associations")
                        st.write("- `{prefix}_keywords.csv` - Keywords list")
                        st.write("- `{prefix}_paragraph_keywords.csv` - Paragraph-keyword associations")
                        st.write("- `{prefix}_metadata.csv` - Export metadata")
                        st.write("- `{prefix}_summary.txt` - Export summary and instructions")
                            
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
                    elif export_location in ["Custom path", "Custom folder"] and custom_path:
                        output_path = os.path.join(custom_path, filename)
                    else:
                        output_path = filename
                    
                    # Generate and save export
                    if export_format == "📄 Markdown":
                        content = export_manager.export_to_markdown(output_path, bold_keywords=bold_keywords)
                        file_size = len(content.encode('utf-8'))
                        st.success("✅ Markdown export completed!")
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
                    else:
                        # CSV export
                        summary = export_manager.export_to_csv(output_path)
                        st.success("✅ CSV export completed!")
                        st.info("**Multiple CSV files created:**")
                        st.text(summary)
                    
                except Exception as e:
                    st.error(f"Error during export: {str(e)}")
    
    with col3:
        if export_format == "📄 Markdown":
            if st.button("📋 Copy to Clipboard"):
                with st.spinner("Generating content..."):
                    try:
                        markdown_content = export_manager.export_to_markdown(bold_keywords=bold_keywords)
                        
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
        else:
            st.write("*Copy to clipboard not available for CSV format*")
    
    # Additional options
    st.markdown("---")
    st.markdown("### Additional Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗂️ Export Statistics"):
            _show_export_statistics(database)
    
    with col2:
        if st.button("🔧 Database Info"):
            _show_database_info(database)


def _show_markdown_format_info():
    """Show markdown format information."""
    with st.expander("📋 Markdown Format Details", expanded=False):
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


def _show_csv_format_info():
    """Show CSV format information."""
    with st.expander("📊 CSV Format Details", expanded=False):
        st.markdown("""
        **CSV Export creates multiple files for complete data reconstruction:**
        
        **Files Created:**
        - `talks.csv` - Conference talks metadata (title, speaker, date, etc.)
        - `paragraphs.csv` - Paragraph content, notes, and review status
        - `tags.csv` - Tag hierarchy and descriptions
        - `paragraph_tags.csv` - Which paragraphs are tagged with which tags
        - `keywords.csv` - List of all keywords
        - `paragraph_keywords.csv` - Which paragraphs match which keywords
        - `metadata.csv` - Export metadata and version information
        - `summary.txt` - Human-readable summary and import instructions
        
        **Use Cases:**
        - **Backup:** Complete database backup that can be fully restored
        - **Migration:** Transfer data between different systems
        - **Analysis:** Import into Excel, Google Sheets, or other tools
        - **Sharing:** Share dataset with others who can import it
        
        **Import:** Use the Import function to reconstruct the database from these files.
        """)


def _generate_export_preview(database: BaseDatabaseInterface) -> str:
    """Generate a limited preview of the export."""
    # Get just the first few root tags for preview
    all_tags = database.get_all_tags()
    root_tags = [tag for tag in all_tags if tag['parent_tag_id'] is None]
    
    if not root_tags:
        return "No tags found in database."
    
    # Generate preview with first 2 root tags only
    preview_tags = sorted(root_tags, key=lambda x: x['name'])[:2]
    
    markdown_content = []
    markdown_content.append("# Conference Talks Database Export (PREVIEW)\n")
    markdown_content.append(f"*Preview generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    markdown_content.append("*This preview shows only the first 2 root tags. Full export will include all tags.*\n")
    
    # For preview, we'll just show the tag structure without full content
    for root_tag in preview_tags:
        markdown_content.append(f"\n## {root_tag['name']}")
        if root_tag['description']:
            markdown_content.append(f"*{root_tag['description']}*")
        
        # Find children
        child_tags = [tag for tag in all_tags if tag['parent_tag_id'] == root_tag['id']]
        for child_tag in child_tags[:3]:  # Limit to first 3 children
            markdown_content.append(f"\n### {child_tag['name']}")
            if child_tag['description']:
                markdown_content.append(f"*{child_tag['description']}*")
        
        if len(child_tags) > 3:
            markdown_content.append(f"\n*... and {len(child_tags) - 3} more subtags*")
    
    if len(root_tags) > 2:
        markdown_content.append(f"\n*... and {len(root_tags) - 2} more root tags in full export*")
    
    return '\n'.join(markdown_content)


def _show_export_statistics(database: BaseDatabaseInterface) -> None:
    """Show detailed statistics about what will be exported."""
    st.markdown("### 📊 Export Statistics")
    
    # Get statistics
    stats = database.get_export_statistics()
    
    # Display in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Tags", stats['total_tags'])
        st.metric("Root Tags", stats['root_tags'])
        st.metric("Child Tags", stats['child_tags'])
    
    with col2:
        st.metric("Total Paragraphs", stats['total_paragraphs'])
        st.metric("Tagged Paragraphs", stats['tagged_paragraphs'])
        st.metric("Paragraphs with Notes", stats['paragraphs_with_notes'])
    
    with col3:
        st.metric("Total Keywords", stats['total_keywords'])
        st.metric("Used Keywords", stats['used_keywords'])
        st.metric("Untagged Paragraphs", stats['untagged_paragraphs'])
    
    # Top tags by paragraph count
    top_tags = database.get_top_tags_by_usage(10)
    
    if top_tags:
        st.markdown("### 🏷️ Top Tags by Paragraph Count")
        for i, tag in enumerate(top_tags, 1):
            st.write(f"{i}. **{tag['name']}**: {tag['usage_count']} paragraphs")


def _show_database_info(database: BaseDatabaseInterface) -> None:
    """Show general database information."""
    st.markdown("### 🗄️ Database Information")
    
    # Get database info
    db_info = database.get_database_info()
    
    # Database file info
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Database Path:** {db_info['db_path']}")
        if 'file_size' in db_info:
            st.write(f"**File Size:** {db_info['file_size']:,} bytes")
    
    with col2:
        if 'last_modified' in db_info:
            st.write(f"**Last Modified:** {db_info['last_modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Schema info
    st.markdown("**Database Tables:**")
    for table_name, count in db_info['tables'].items():
        st.write(f"• {table_name}: {count:,} records")