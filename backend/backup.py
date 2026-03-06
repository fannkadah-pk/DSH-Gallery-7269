from __future__ import annotations

import os
import shutil
import sqlite3
import json
from datetime import datetime
import zipfile
from typing import Dict, Any, List

class BackupManager:
    """Manage backup and restore operations."""
    
    def __init__(self) -> None:
        """Initialize backup manager."""
        self.backup_dir: str = '../backups'
        self.upload_dir: str = '../uploads'
        self.database_path: str = '../database/gallery.db'
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self) -> str:
        """Create a full backup of database and uploads."""
        timestamp: str = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name: str = f'backup_{timestamp}'
        backup_path: str = os.path.join(self.backup_dir, backup_name)
        
        # Create temporary backup directory
        temp_dir: str = f'{backup_path}_temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Backup database
            db_backup_path: str = os.path.join(temp_dir, 'database.db')
            shutil.copy2(self.database_path, db_backup_path)
            
            # Backup uploads
            uploads_backup_path: str = os.path.join(temp_dir, 'uploads')
            if os.path.exists(self.upload_dir):
                shutil.copytree(self.upload_dir, uploads_backup_path)
            
            # Create metadata file
            metadata: Dict[str, Any] = {
                'timestamp': timestamp,
                'version': '1.0',
                'files_count': self.get_files_count(),
                'backup_type': 'full'
            }
            
            with open(os.path.join(temp_dir, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create zip archive
            shutil.make_archive(backup_path, 'zip', temp_dir)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            # Record backup in database
            self.record_backup(backup_name + '.zip', os.path.getsize(backup_path + '.zip'))
            
            return backup_name + '.zip'
            
        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
    
    def restore_backup(self, backup_filename: str) -> bool:
        """Restore from a backup file."""
        backup_path: str = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup {backup_filename} not found")
        
        # Create restore directory
        restore_dir: str = f'{backup_path}_restore'
        os.makedirs(restore_dir, exist_ok=True)
        
        try:
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                zip_ref.extractall(restore_dir)
            
            # Restore database
            db_backup: str = os.path.join(restore_dir, 'database.db')
            if os.path.exists(db_backup):
                # Backup current database before restore
                self.create_backup()
                shutil.copy2(db_backup, self.database_path)
            
            # Restore uploads
            uploads_backup = os.path.join(restore_dir, 'uploads')
            if os.path.exists(uploads_backup):
                # Clear current uploads
                if os.path.exists(self.upload_dir):
                    shutil.rmtree(self.upload_dir)
                # Restore from backup
                shutil.copytree(uploads_backup, self.upload_dir)
            
            return True
            
        finally:
            # Clean up restore directory
            if os.path.exists(restore_dir):
                shutil.rmtree(restore_dir)
    
    def get_files_count(self) -> int:
        """Get count of non-deleted files."""
        conn: sqlite3.Connection = sqlite3.connect(self.database_path)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM files WHERE deleted = 0")
        count: int = cursor.fetchone()[0]
        conn.close()
        return count
    
    def record_backup(self, filename: str, size: int) -> None:
        """Record backup in database."""
        conn: sqlite3.Connection = sqlite3.connect(self.database_path)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO backups (filename, size, created_at)
            VALUES (?, ?, ?)
        ''', (filename, size, datetime.now()))
        conn.commit()
        conn.close()
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        backups: List[Dict[str, Any]] = []
        for file in os.listdir(self.backup_dir):
            if file.endswith('.zip'):
                filepath: str = os.path.join(self.backup_dir, file)
                backups.append({
                    'filename': file,
                    'size': os.path.getsize(filepath),
                    'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })
        return sorted(backups, key=lambda x: x['created'], reverse=True)

# Usage example
if __name__ == '__main__':
    backup_manager = BackupManager()
    
    # Create backup
    print("Creating backup...")
    backup_file = backup_manager.create_backup()
    print(f"Backup created: {backup_file}")
    
    # List backups
    print("\nAvailable backups:")
    for backup in backup_manager.list_backups():
        print(f"- {backup['filename']} ({backup['size']} bytes) - {backup['created']}")