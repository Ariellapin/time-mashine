import os
import shutil
import uuid
import database

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
    
    shutil.copy2(original_path, backup_path)
    return backup_path

def restore_file(original_path, backup_path):
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Ensure the directory for the original path exists
    original_dir = os.path.dirname(original_path)
    if not os.path.exists(original_dir):
        os.makedirs(original_dir)
        
    shutil.copy2(backup_path, original_path)

def check_file_status(original_path):
    return os.path.exists(original_path)

def protect_file(original_path):
    original_path = os.path.abspath(original_path)
    # 1. Backup the file
    backup_path = backup_file(original_path)
    # 2. Add to database
    database.add_file(original_path, backup_path)
    return backup_path
