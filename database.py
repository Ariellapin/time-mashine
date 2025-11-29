import sqlite3
import os

DB_NAME = "history_saver.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT NOT NULL UNIQUE,
            backup_path TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS monitored_folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE
        );
    ''')
    conn.commit()
    conn.close()

def add_file(original_path, backup_path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO files (original_path, backup_path) VALUES (?, ?)', (original_path, backup_path))
        conn.commit()
    except sqlite3.IntegrityError:
        # If file already exists, update the backup path
        cursor.execute('UPDATE files SET backup_path = ?, timestamp = CURRENT_TIMESTAMP WHERE original_path = ?', (backup_path, original_path))
        conn.commit()
    finally:
        conn.close()

def get_all_files():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, original_path, backup_path, timestamp FROM files')
    rows = cursor.fetchall()
    conn.close()
    return rows

def remove_file(file_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()

def get_file_by_id(file_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, original_path, backup_path, timestamp FROM files WHERE id = ?', (file_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_monitored_folder(path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT OR IGNORE INTO monitored_folders (path) VALUES (?)', (path,))
        conn.commit()
    finally:
        conn.close()

def remove_monitored_folder(path):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM monitored_folders WHERE path = ?', (path,))
    conn.commit()
    conn.close()

def get_monitored_folders():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Check if table exists first (migration for existing users)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monitored_folders'")
    if not cursor.fetchone():
        return []
    
    cursor.execute('SELECT path FROM monitored_folders')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

