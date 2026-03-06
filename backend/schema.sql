-- SQL schema for DSH Gallery application
-- Run this script in sqlite3 to initialize the database manually.

BEGIN TRANSACTION;

CREATE TABLE files (
    id INT IDENTITY(1,1) PRIMARY KEY,
    filename TEXT NOT NULL,
    originalname TEXT NOT NULL,
    filepath TEXT NOT NULL,
    file_type TEXT NOT NULL,
    size INT NOT NULL,
    mimetype TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    deleted BIT DEFAULT 0,
    deleted_at DATETIME,
    trash_path TEXT
);

CREATE TABLE settings (
    id INT IDENTITY(1,1) PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    size INT NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    contact_country_code TEXT NOT NULL,
    contact_number TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role INTEGER DEFAULT 4,
    status TEXT DEFAULT 'pending',
    created_at DATETIME NOT NULL
);

COMMIT;
