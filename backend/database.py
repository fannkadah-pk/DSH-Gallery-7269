from __future__ import annotations

import sqlite3
import os
from datetime import datetime

def init_database() -> None:
    """Initialize database with required tables."""
    # Create database directory if it doesn't exist
    os.makedirs('../database', exist_ok=True)
    
    conn: sqlite3.Connection = sqlite3.connect('../database/gallery.db')
    cursor: sqlite3.Cursor = conn.cursor()
    
    # Create files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            originalname TEXT NOT NULL,
            filepath TEXT NOT NULL,
            file_type TEXT NOT NULL,
            size INTEGER NOT NULL,
            mimetype TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            deleted BOOLEAN DEFAULT 0,
            deleted_at TIMESTAMP,
            trash_path TEXT
        )
    ''')
    
    # Create settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    ''')
    
    # Create backups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            size INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully")

if __name__ == '__main__':
    init_database()