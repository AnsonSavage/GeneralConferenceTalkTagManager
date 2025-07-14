"""
Backup page for creating and managing database backups.
"""
import streamlit as st
from datetime import datetime
from pathlib import Path
import os
from ..database.base_database import BaseDatabaseInterface
from ..utils.backup_manager import BackupManager


def render_backup_page(database: BaseDatabaseInterface, backup_manager: BackupManager):
    """
    Render the backup management page.
    
    Args:
        database: The database instance
        backup_manager: The backup manager instance
    """
    st.header("💾 Database Backup Manager")
    
    # Get current database path from session state
    current_db = st.session_state.get('selected_database', 'conference_talks.db')
    
    # Backup creation section
    st.subheader("📦 Create New Backup")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"**Current Database:** `{current_db}`")
        if os.path.exists(current_db):
            file_size = os.path.getsize(current_db)
            size_str = backup_manager.get_backup_size_formatted(file_size)
            st.caption(f"Database size: {size_str}")
        else:
            st.warning("Database file not found!")
    
    with col2:
        if st.button("💾 Save a Backup", type="primary", help="Create a timestamped backup of the current database"):
            if os.path.exists(current_db):
                with st.spinner("Creating backup..."):
                    backup_results = backup_manager.create_backup(current_db)
                
                if backup_results['success']:
                    st.success("✅ Backup created successfully!")
                    
                    # Show backup details
                    st.write("**Backup Details:**")
                    st.write(f"- **Timestamp:** {backup_results['timestamp']}")
                    st.write(f"- **Backup Directory:** `{backup_results['backup_dir']}`")
                    st.write(f"- **Files Created:** {len(backup_results['files_created'])}")
                    
                    # Show created files in expandable section
                    with st.expander("📁 View Created Files"):
                        for file_path in backup_results['files_created']:
                            file_name = Path(file_path).name
                            if file_path.endswith('.db'):
                                st.write(f"🗄️ **Database:** `{file_name}`")
                            else:
                                st.write(f"📄 **CSV:** `{file_name}`")
                    
                    # Show CSV export summary
                    if 'csv_export_summary' in backup_results:
                        with st.expander("📊 CSV Export Summary"):
                            st.text(backup_results['csv_export_summary'])
                    
                    # Force refresh of backup list
                    st.rerun()
                else:
                    st.error("❌ Backup creation failed!")
                    for error in backup_results['errors']:
                        st.error(f"• {error}")
            else:
                st.error("❌ Database file not found!")
    
    st.markdown("---")
    
    # Backup management section
    st.subheader("📋 Manage Existing Backups")
    
    # Get list of backups
    backup_info = backup_manager.list_backups()
    
    if backup_info['total_count'] == 0:
        st.info("No backups found. Create your first backup above!")
        return
    
    # Show backup statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Backups", backup_info['total_count'])
    with col2:
        total_size_str = backup_manager.get_backup_size_formatted(backup_info['total_size'])
        st.metric("Total Size", total_size_str)
    with col3:
        # Show backup directory
        backup_dir = Path("backups")
        if backup_dir.exists():
            st.metric("Backup Directory", str(backup_dir.resolve()))
    
    # Display backups in a table-like format
    st.write("**Available Backups:**")
    
    for backup in backup_info['backups']:
        with st.expander(f"📅 {backup['timestamp']} ({backup_manager.get_backup_size_formatted(backup['size'])})"):
            
            # Backup details
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Path:** `{backup['path']}`")
                st.write(f"**Files:** {len(backup['files'])}")
                st.write(f"**Size:** {backup_manager.get_backup_size_formatted(backup['size'])}")
                
                # Show file details
                db_files = [f for f in backup['files'] if f['type'] == 'database']
                csv_files = [f for f in backup['files'] if f['type'] == 'csv']
                
                if db_files:
                    st.write("**Database Files:**")
                    for db_file in db_files:
                        size_str = backup_manager.get_backup_size_formatted(db_file['size'])
                        st.write(f"  🗄️ `{db_file['name']}` ({size_str})")
                
                if csv_files:
                    st.write("**CSV Files:**")
                    for csv_file in csv_files:
                        size_str = backup_manager.get_backup_size_formatted(csv_file['size'])
                        st.write(f"  📄 `{csv_file['name']}` ({size_str})")
            
            with col2:
                # Action buttons
                st.write("**Actions:**")
                
                # Restore button
                if st.button(f"🔄 Restore", key=f"restore_{backup['timestamp']}", 
                            help="Restore this backup to the current database"):
                    
                    # Confirmation dialog
                    if st.button(f"⚠️ Confirm Restore", key=f"confirm_restore_{backup['timestamp']}", 
                                type="secondary"):
                        
                        with st.spinner("Restoring backup..."):
                            restore_results = backup_manager.restore_from_backup(
                                backup['timestamp'], 
                                current_db
                            )
                        
                        if restore_results['success']:
                            st.success("✅ Backup restored successfully!")
                            st.info(f"Database restored from: `{restore_results['source_file']}`")
                            # Clear cached components to reload with restored data
                            if 'components' in st.session_state:
                                del st.session_state['components']
                            st.rerun()
                        else:
                            st.error(f"❌ Restore failed: {restore_results['error']}")
                
                # Delete button
                if st.button(f"🗑️ Delete", key=f"delete_{backup['timestamp']}", 
                            help="Delete this backup permanently"):
                    
                    # Confirmation dialog
                    if st.button(f"⚠️ Confirm Delete", key=f"confirm_delete_{backup['timestamp']}", 
                                type="secondary"):
                        
                        with st.spinner("Deleting backup..."):
                            delete_results = backup_manager.delete_backup(backup['timestamp'])
                        
                        if delete_results['success']:
                            st.success("✅ Backup deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Delete failed: {delete_results['error']}")
    
    # Help section
    st.markdown("---")
    st.subheader("ℹ️ Backup Information")
    
    st.write("""
    **Backup Structure:**
    ```
    ./backups/
    ├── YYYYMMDD_HHMMSS/
    │   ├── database_name_YYYYMMDD_HHMMSS.db
    │   └── csv_files/
    │       ├── database_name_YYYYMMDD_HHMMSS_talks.csv
    │       ├── database_name_YYYYMMDD_HHMMSS_paragraphs.csv
    │       ├── database_name_YYYYMMDD_HHMMSS_tags.csv
    │       └── ... (other CSV files)
    ```
    
    **What gets backed up:**
    - Complete database file (`.db`)
    - All data exported to CSV format for data recovery
    - Metadata about the backup
    
    **Restore Process:**
    - Restoring replaces the current database with the backup
    - Make sure to create a backup before restoring if needed
    - The application will reload automatically after restore
    """)