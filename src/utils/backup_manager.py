"""
Backup manager for creating timestamped backups of database and CSV exports.
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from ..database.base_database import BaseDatabaseInterface
from .export_manager import ExportManager


class BackupManager:
    """Handles creating timestamped backups of database and CSV exports."""
    
    def __init__(self, database: BaseDatabaseInterface):
        """
        Initialize the backup manager.
        
        Args:
            database: The database instance to backup
        """
        self.database = database
        self.export_manager = ExportManager(database)
    
    def create_backup(self, db_path: str) -> Dict[str, Any]:
        """
        Create a timestamped backup of the database and CSV exports.
        
        Args:
            db_path: Path to the database file to backup
            
        Returns:
            Dictionary containing backup results and file paths
        """
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Extract database name (without extension)
        db_name = Path(db_path).stem
        
        # Create backup directory structure
        backup_base_dir = Path("backups")
        backup_timestamp_dir = backup_base_dir / timestamp
        csv_dir = backup_timestamp_dir / "csv_files"
        
        # Create directories
        backup_timestamp_dir.mkdir(parents=True, exist_ok=True)
        csv_dir.mkdir(exist_ok=True)
        
        backup_results = {
            'timestamp': timestamp,
            'backup_dir': str(backup_timestamp_dir),
            'csv_dir': str(csv_dir),
            'files_created': [],
            'errors': []
        }
        
        try:
            # 1. Copy database file
            db_backup_name = f"{db_name}_{timestamp}.db"
            db_backup_path = backup_timestamp_dir / db_backup_name
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, db_backup_path)
                backup_results['files_created'].append(str(db_backup_path))
                backup_results['db_backup_path'] = str(db_backup_path)
            else:
                backup_results['errors'].append(f"Database file not found: {db_path}")
            
            # 2. Create CSV exports in the csv_files subdirectory
            csv_file_prefix = csv_dir / f"{db_name}_{timestamp}"
            
            # Export all data to CSV
            export_data = self.export_manager.prepare_export_data()
            csv_summary = self.export_manager.export_to_csv(str(csv_file_prefix))
            
            # Get list of created CSV files
            csv_files = list(csv_dir.glob(f"{db_name}_{timestamp}*"))
            for csv_file in csv_files:
                backup_results['files_created'].append(str(csv_file))
            
            backup_results['csv_export_summary'] = csv_summary
            backup_results['success'] = True
            
        except Exception as e:
            backup_results['errors'].append(f"Backup creation failed: {str(e)}")
            backup_results['success'] = False
        
        return backup_results
    
    def list_backups(self) -> Dict[str, Any]:
        """
        List all available backups.
        
        Returns:
            Dictionary containing backup information
        """
        backup_base_dir = Path("backups")
        
        if not backup_base_dir.exists():
            return {
                'backups': [],
                'total_count': 0,
                'total_size': 0
            }
        
        backups = []
        total_size = 0
        
        # Get all timestamp directories
        for timestamp_dir in backup_base_dir.iterdir():
            if timestamp_dir.is_dir():
                backup_info = {
                    'timestamp': timestamp_dir.name,
                    'path': str(timestamp_dir),
                    'files': [],
                    'size': 0
                }
                
                # Get all files in the backup directory
                for file_path in timestamp_dir.rglob('*'):
                    if file_path.is_file():
                        file_size = file_path.stat().st_size
                        backup_info['files'].append({
                            'name': file_path.name,
                            'path': str(file_path),
                            'size': file_size,
                            'type': 'database' if file_path.suffix == '.db' else 'csv'
                        })
                        backup_info['size'] += file_size
                        total_size += file_size
                
                backups.append(backup_info)
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'backups': backups,
            'total_count': len(backups),
            'total_size': total_size
        }
    
    def restore_from_backup(self, backup_timestamp: str, target_db_path: str) -> Dict[str, Any]:
        """
        Restore database from a backup.
        
        Args:
            backup_timestamp: Timestamp of the backup to restore
            target_db_path: Path where to restore the database
            
        Returns:
            Dictionary containing restore results
        """
        backup_dir = Path("backups") / backup_timestamp
        
        if not backup_dir.exists():
            return {
                'success': False,
                'error': f"Backup directory not found: {backup_dir}"
            }
        
        # Find the database file in the backup
        db_files = list(backup_dir.glob("*.db"))
        
        if not db_files:
            return {
                'success': False,
                'error': f"No database file found in backup: {backup_dir}"
            }
        
        if len(db_files) > 1:
            return {
                'success': False,
                'error': f"Multiple database files found in backup: {backup_dir}"
            }
        
        source_db = db_files[0]
        
        try:
            # Copy the database file
            shutil.copy2(source_db, target_db_path)
            
            return {
                'success': True,
                'source_file': str(source_db),
                'target_file': target_db_path,
                'message': f"Database restored from backup {backup_timestamp}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to restore database: {str(e)}"
            }
    
    def delete_backup(self, backup_timestamp: str) -> Dict[str, Any]:
        """
        Delete a specific backup.
        
        Args:
            backup_timestamp: Timestamp of the backup to delete
            
        Returns:
            Dictionary containing deletion results
        """
        backup_dir = Path("backups") / backup_timestamp
        
        if not backup_dir.exists():
            return {
                'success': False,
                'error': f"Backup directory not found: {backup_dir}"
            }
        
        try:
            shutil.rmtree(backup_dir)
            return {
                'success': True,
                'message': f"Backup {backup_timestamp} deleted successfully"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to delete backup: {str(e)}"
            }
    
    def get_backup_size_formatted(self, size_bytes: int) -> str:
        """
        Format backup size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"