use rusqlite::{Connection, params};
use std::path::Path;

pub fn init_database() -> rusqlite::Result<()> {
    let db_path = Path::new("../database/gallery.db");
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let conn = Connection::open(db_path)?;
    conn.execute_batch("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            originalname TEXT NOT NULL,
            filepath TEXT NOT NULL,
            file_type TEXT NOT NULL,
            size INTEGER NOT NULL,
            mimetype TEXT NOT NULL,
            created_at TEXT NOT NULL,
            deleted INTEGER DEFAULT 0,
            deleted_at TEXT,
            trash_path TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            size INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
    """)?;
    Ok(())
}

pub fn get_connection() -> rusqlite::Result<Connection> {
    Connection::open(Path::new("../database/gallery.db"))
}