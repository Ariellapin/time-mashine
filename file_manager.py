import os
import shutil
import uuid
import database
import sqlite3

VAULT_DIR = "_vault"

def ensure_vault():
    if not os.path.exists(VAULT_DIR):
        os.makedirs(VAULT_DIR)

def backup_file(original_path):
    ensure_vault()
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"File not found: {original_path}")
    
    # Create a unique name for the backup to avoid collisions
    filename = os.path.basename(original_path)
    unique_name = f"{uuid.uuid4()}_{filename}"
    backup_path = os.path.join(VAULT_DIR, unique_name)
    
    try:
        # Use Hard Link instead of Copy
        os.link(original_path, backup_path)
    except OSError as e:
        # Fallback or Error? User requested "low price", so we should probably NOT copy.
        # However, if it's a different drive, hard link fails.
        # We will raise an error for now to be strict about the "no full backup" rule.
        if e.winerror == 17: # ERROR_NOT_SAME_DEVICE
             raise OSError("Cannot protect file on a different drive than the Vault (System Drive). Hard Links require same volume.")
        raise e

    return backup_path

def restore_file(original_path, backup_path):
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Ensure the directory for the original path exists
    original_dir = os.path.dirname(original_path)
    if not os.path.exists(original_dir):
        os.makedirs(original_dir)
        
    # When restoring, we want to recreate the link back to the original location
    # But if the original was deleted, we just link it back.
    if os.path.exists(original_path):
         raise FileExistsError(f"File already exists: {original_path}")

    try:
        os.link(backup_path, original_path)
    except OSError:
        # If link fails (unlikely if it's same drive), try copy as last resort
        shutil.copy2(backup_path, original_path)

def check_file_status(original_path):
    return os.path.exists(original_path)

def protect_file(original_path):
    original_path = os.path.abspath(original_path)
    
    # Check if already protected
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM files WHERE original_path = ?', (original_path,))
    exists = cursor.fetchone()
    conn.close()
    
    if exists:
        return None # Already protected

    # 1. Backup the file (Create Hard Link)
    backup_path = backup_file(original_path)
    # 2. Add to database
    database.add_file(original_path, backup_path)
    return backup_path

def scan_and_protect(folder_path):
    """Recursively scans a folder and protects all files."""
    count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            filepath = os.path.join(root, file)
            try:
                if protect_file(filepath):
                    count += 1
            except Exception as e:
                print(f"Skipping {filepath}: {e}")
    return count
