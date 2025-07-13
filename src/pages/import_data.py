"""
Import page for the Conference Talks Analysis application.
Allows users to import database content from CSV files.
"""
import streamlit as st
import os
from typing import List
from ..database.base_database import BaseDatabaseInterface
from ..utils.import_manager import ImportManager


def render_import_page(database: BaseDatabaseInterface) -> None:
    """Render the import page."""
    st.header("📥 Import Database")
    st.markdown("Import conference talks data from CSV files to reconstruct or merge databases.")
    
    # Create import manager
    import_manager = ImportManager(database)
    
    # Import mode selection
    st.markdown("### Import Mode")
    import_mode = st.radio(
        "Choose import mode:",
        options=["🔄 Merge with Current Database", "🗃️ Create New Database (Replace All)"],
        help="Merge adds to existing data. Replace clears all data first."
    )
    
    merge_mode = import_mode.startswith("🔄")
    
    if not merge_mode:
        st.warning("⚠️ **Replace All mode will delete all existing data!** This cannot be undone.")
        
        # Confirmation checkbox for replace mode
        confirm_replace = st.checkbox(
            "I understand that all existing data will be deleted",
            value=False,
            help="Check this box to confirm you want to replace all data"
        )
    else:
        confirm_replace = True
    
    st.markdown("---")
    
    # File upload section
    st.markdown("### Select CSV Files")
    st.markdown("Upload the CSV files exported from this application:")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose CSV files",
        type=['csv'],
        accept_multiple_files=True,
        help="Select all CSV files from a previous export (talks.csv, paragraphs.csv, tags.csv, etc.)"
    )
    
    if uploaded_files:
        st.markdown("### Uploaded Files")
        
        # Display uploaded files
        for file in uploaded_files:
            st.write(f"📄 {file.name} ({file.size:,} bytes)")
        
        # Save uploaded files temporarily
        temp_file_paths = []
        for file in uploaded_files:
            temp_path = f"temp_{file.name}"
            with open(temp_path, 'wb') as f:
                f.write(file.getvalue())
            temp_file_paths.append(temp_path)
        
        # Validate files
        st.markdown("### File Validation")
        with st.spinner("Validating uploaded files..."):
            validation_result = import_manager.validate_csv_files(temp_file_paths)
        
        if validation_result['is_valid']:
            st.success("✅ All files are valid and ready for import!")
            
            # Show found files
            found_files = validation_result['found_files']
            st.markdown("**Found files:**")
            for file_type, file_path in found_files.items():
                if file_path:
                    st.write(f"✅ {file_type}.csv")
                else:
                    st.write(f"⚠️ {file_type}.csv (optional - not found)")
        else:
            st.error("❌ File validation failed!")
            st.markdown("**Errors:**")
            for error in validation_result['errors']:
                st.write(f"• {error}")
            
            # Clean up temp files
            _cleanup_temp_files(temp_file_paths)
            return
        
        # Show warnings if any
        if validation_result.get('warnings'):
            st.warning("⚠️ Warnings:")
            for warning in validation_result['warnings']:
                st.write(f"• {warning}")
        
        st.markdown("---")
        
        # Import preview
        st.markdown("### Import Preview")
        
        # Get preview statistics from the CSV files
        try:
            preview_stats = _get_import_preview_stats(validation_result['found_files'])
            
            # Show current database stats
            current_stats = database.get_export_statistics()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Database:**")
                st.metric("Total Tags", current_stats['total_tags'])
                st.metric("Total Paragraphs", current_stats['total_paragraphs'])
                st.metric("Tagged Paragraphs", current_stats['tagged_paragraphs'])
            
            with col2:
                st.markdown("**Will Import:**")
                st.metric("Talks", preview_stats.get('talks', 0))
                st.metric("Paragraphs", preview_stats.get('paragraphs', 0))
                st.metric("Tags", preview_stats.get('tags', 0))
                st.metric("Tag Associations", preview_stats.get('paragraph_tags', 0))
                st.metric("Keywords", preview_stats.get('keywords', 0))
            
            # Show import mode explanation
            if merge_mode:
                st.info("📄 **Merge Mode**: New data will be added to existing data")
                st.write("• Existing data will be preserved")
                st.write("• New data will be added")
                st.write("• Duplicate talks may be skipped")
                
                # Calculate estimated totals for merge mode
                st.markdown("**Estimated Totals After Import:**")
                est_talks = current_stats['total_talks'] + preview_stats.get('talks', 0)
                est_paragraphs = current_stats['total_paragraphs'] + preview_stats.get('paragraphs', 0)
                est_tags = current_stats['total_tags'] + preview_stats.get('tags', 0)
                
                st.write(f"• Talks: ~{est_talks} (current + imported)")
                st.write(f"• Paragraphs: ~{est_paragraphs} (current + imported)")
                st.write(f"• Tags: ~{est_tags} (current + imported)")
                st.write("*Note: Exact totals may vary due to duplicate handling*")
            else:
                st.warning("🗑️ **Replace Mode**: All existing data will be deleted")
                st.write("• All current data will be deleted")
                st.write("• Only imported data will remain")
                
                # Show final totals for replace mode
                st.markdown("**Final Totals After Import:**")
                st.write(f"• Talks: {preview_stats.get('talks', 0)}")
                st.write(f"• Paragraphs: {preview_stats.get('paragraphs', 0)}")
                st.write(f"• Tags: {preview_stats.get('tags', 0)}")
                
        except Exception as e:
            st.warning(f"Could not generate import preview: {str(e)}")
            # Fallback to generic preview
            current_stats = database.get_export_statistics()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Database:**")
                st.metric("Total Tags", current_stats['total_tags'])
                st.metric("Total Paragraphs", current_stats['total_paragraphs'])
                st.metric("Tagged Paragraphs", current_stats['tagged_paragraphs'])
            
            with col2:
                st.markdown("**After Import:**")
                if merge_mode:
                    st.info("New data will be merged with existing data")
                    st.write("• Existing data will be preserved")
                    st.write("• New data will be added")
                    st.write("• Duplicate talks may be skipped")
                else:
                    st.warning("All existing data will be replaced")
                    st.write("• All current data will be deleted")
                    st.write("• Only imported data will remain")
        
        st.markdown("---")
        
        # Import button
        if st.button("📥 Start Import", type="primary", disabled=not confirm_replace):
            if not confirm_replace:
                st.error("Please confirm that you want to replace all data.")
                return
            
            with st.spinner("Importing data..."):
                try:
                    # Perform import
                    import_result = import_manager.import_from_csv(temp_file_paths, merge_mode)
                    
                    if import_result['success']:
                        st.success("✅ Import completed successfully!")
                        
                        # Show import statistics
                        stats = import_result['stats']
                        st.markdown("### Import Statistics")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Talks Imported", stats['talks_imported'])
                            st.metric("Paragraphs Imported", stats['paragraphs_imported'])
                        
                        with col2:
                            st.metric("Tags Imported", stats['tags_imported'])
                            st.metric("Tag Associations", stats['paragraph_tags_imported'])
                        
                        with col3:
                            st.metric("Keywords Imported", stats['keywords_imported'])
                            st.metric("Keyword Associations", stats['paragraph_keywords_imported'])
                        
                        # Show errors if any
                        if stats['errors']:
                            st.warning(f"Import completed with {len(stats['errors'])} errors:")
                            with st.expander("Show errors"):
                                for error in stats['errors']:
                                    st.write(f"• {error}")
                        
                        # Success message
                        st.info("🎉 Database has been successfully updated! You can now use the application with the imported data.")
                        
                    else:
                        st.error("❌ Import failed!")
                        st.markdown("**Errors:**")
                        for error in import_result.get('errors', []):
                            st.write(f"• {error}")
                        
                        # Show partial statistics if available
                        if 'stats' in import_result:
                            stats = import_result['stats']
                            st.markdown("### Partial Import Statistics")
                            st.write(f"Talks imported: {stats['talks_imported']}")
                            st.write(f"Paragraphs imported: {stats['paragraphs_imported']}")
                            st.write(f"Tags imported: {stats['tags_imported']}")
                
                except Exception as e:
                    st.error(f"Import failed with error: {str(e)}")
                
                finally:
                    # Clean up temp files
                    _cleanup_temp_files(temp_file_paths)
        
        # Clean up temp files on rerun
        else:
            _cleanup_temp_files(temp_file_paths)
    
    else:
        # No files uploaded - show instructions
        st.markdown("### Instructions")
        st.info("""
        **How to import data:**
        
        1. **Get CSV files** from a previous export:
           - Use the Export page to create CSV files
           - Or obtain CSV files from another user
        
        2. **Upload files** using the file uploader above:
           - Select all CSV files from the export
           - Required: talks.csv, paragraphs.csv, tags.csv
           - Optional: paragraph_tags.csv, keywords.csv, paragraph_keywords.csv, metadata.csv
        
        3. **Choose import mode:**
           - **Merge:** Add to existing data (safer)
           - **Replace:** Delete all data and import only new data
        
        4. **Review and confirm** the import operation
        """)
        
        # Show supported formats
        st.markdown("### Supported Formats")
        formats = import_manager.get_supported_formats()
        st.write(f"Supported import formats: {', '.join(formats)}")
        
        # Example file structure
        with st.expander("📋 Expected File Structure"):
            st.markdown("""
            **Required CSV files:**
            - `talks.csv` - Conference talks metadata
            - `paragraphs.csv` - Paragraph content and notes
            - `tags.csv` - Tag hierarchy and descriptions
            
            **Optional CSV files:**
            - `paragraph_tags.csv` - Paragraph-tag associations
            - `keywords.csv` - Keywords list
            - `paragraph_keywords.csv` - Paragraph-keyword associations
            - `metadata.csv` - Export metadata
            
            **File naming:** Files should contain the type name (e.g., "talks.csv", "export_2024_talks.csv")
            """)


def _cleanup_temp_files(file_paths: List[str]) -> None:
    """Clean up temporary files."""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors


def _get_import_preview_stats(found_files: dict) -> dict:
    """
    Get preview statistics from CSV files to show what will be imported.
    
    Args:
        found_files: Dictionary of found CSV files from validation
        
    Returns:
        Dictionary with counts of items to be imported
    """
    import csv
    
    stats = {
        'talks': 0,
        'paragraphs': 0,
        'tags': 0,
        'paragraph_tags': 0,
        'keywords': 0,
        'paragraph_keywords': 0
    }
    
    try:
        # Count talks
        if found_files.get('talks'):
            with open(found_files['talks'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                stats['talks'] = sum(1 for row in reader)
        
        # Count paragraphs
        if found_files.get('paragraphs'):
            with open(found_files['paragraphs'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                stats['paragraphs'] = sum(1 for row in reader)
        
        # Count tags
        if found_files.get('tags'):
            with open(found_files['tags'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                stats['tags'] = sum(1 for row in reader)
        
        # Count paragraph-tag associations
        if found_files.get('paragraph_tags'):
            with open(found_files['paragraph_tags'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                stats['paragraph_tags'] = sum(1 for row in reader)
        
        # Count unique keywords
        if found_files.get('keywords'):
            with open(found_files['keywords'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                stats['keywords'] = sum(1 for row in reader)
        
        # Count paragraph-keyword associations
        if found_files.get('paragraph_keywords'):
            with open(found_files['paragraph_keywords'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                stats['paragraph_keywords'] = sum(1 for row in reader)
                
    except Exception as e:
        # If there's an error reading any file, return empty stats
        pass
    
    return stats