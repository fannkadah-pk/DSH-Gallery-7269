from __future__ import annotations

import os
import sqlite3
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from backup import BackupManager

class RestoreManager:
    """Manage restore operations from backups."""
    
    def __init__(self) -> None:
        """Initialize restore manager."""
        self.backup_manager: BackupManager = BackupManager()
        self.database_path: str = '../database/gallery.db'
    
    def restore_latest(self) -> bool:
        """Restore from the latest backup."""
        backups: List[Dict[str, Any]] = self.backup_manager.list_backups()
        
        if not backups:
            raise Exception("No backups available")
        
        latest_backup: str = backups[0]['filename']
        return self.restore_from_file(latest_backup)
    
    def restore_from_file(self, backup_filename: str) -> bool:
        """Restore from a specific backup file."""
        return self.backup_manager.restore_backup(backup_filename)
    
    def restore_point_in_time(self, timestamp: str) -> bool:
        """Restore to a specific point in time."""
        # Find backup closest to timestamp
        backups: List[Dict[str, Any]] = self.backup_manager.list_backups()
        
        closest_backup: Optional[Dict[str, Any]] = None
        min_diff: float = float('inf')
        
        target_time: datetime = datetime.fromisoformat(timestamp)
        
        for backup in backups:
            backup_time: datetime = datetime.fromisoformat(backup['created'])
            diff: float = abs((target_time - backup_time).total_seconds())
            
            if diff < min_diff:
                min_diff = diff
                closest_backup = backup
        
        if closest_backup:
            return self.restore_from_file(closest_backup['filename'])
        else:
            raise Exception("No suitable backup found")
    
    def selective_restore(self, file_ids: List[int]) -> List[str]:
        """Restore specific files from backup."""
        # Get latest backup
        backups: List[Dict[str, Any]] = self.backup_manager.list_backups()
        if not backups:
            raise Exception("No backups available")
        
        latest_backup: str = backups[0]['filename']
        backup_path: str = os.path.join(self.backup_manager.backup_dir, latest_backup)
        
        # Extract specific files
        import zipfile
        with zipfile.ZipFile(backup_path, 'r') as zip_ref:
            # Get file info from database backup
            db_backup: str = 'database.db'
            zip_ref.extract(db_backup, './temp_restore')
            
            # Connect to extracted database
            conn: sqlite3.Connection = sqlite3.connect('./temp_restore/database.db')
            cursor: sqlite3.Cursor = conn.cursor()
            
            placeholders: str = ','.join('?' * len(file_ids))
            cursor.execute(f"SELECT * FROM files WHERE id IN ({placeholders})", file_ids)
            files_to_restore: list = cursor.fetchall()
            conn.close()
            
            # Extract each file
            restored_files: List[str] = []
            for file in files_to_restore:
                filename: str = file[1]  # filename column
                upload_path: str = f"uploads/{filename}"
                
                try:
                    zip_ref.extract(upload_path, self.backup_manager.upload_dir)
                    restored_files.append(filename)
                except Exception as e:
                    print(f"Failed to restore {filename}: {e}")
            
            # Clean up
            shutil.rmtree('./temp_restore')
            
            return restored_files

# Usage example
if __name__ == '__main__':
    restore_manager = RestoreManager()
    
    try:
        # Restore latest backup
        print("Restoring latest backup...")
        restore_manager.restore_latest()
        print("Restore completed successfully")
        
    except Exception as e:
        print(f"Restore failed: {e}")