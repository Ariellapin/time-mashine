import os
import file_manager
import database
import time

def test_hard_link_protection():
    print("--- Testing Hard Link Protection ---")
    
    # 1. Create a dummy file
    test_file = "test_doc.txt"
    with open(test_file, "w") as f:
        f.write("Important Data")
    
    print(f"Created {test_file}")
    
    # 2. Protect it
    try:
        backup_path = file_manager.protect_file(os.path.abspath(test_file))
        print(f"Protected file. Backup at: {backup_path}")
    except Exception as e:
        print(f"Protection failed: {e}")
        return

    # 3. Verify it is a hard link (same inode/index)
    # On Windows, we can check if st_nlink > 1
    stat_orig = os.stat(test_file)
    stat_backup = os.stat(backup_path)
    
    print(f"Original Links: {stat_orig.st_nlink}")
    print(f"Backup Links: {stat_backup.st_nlink}")
    
    if stat_orig.st_nlink >= 2 and stat_backup.st_nlink >= 2:
        print("SUCCESS: File is hard linked (nlink >= 2)")
    else:
        print("FAILURE: File is NOT hard linked (nlink < 2). Did it copy instead?")

    # 4. Delete Original
    os.remove(test_file)
    print(f"Deleted original {test_file}")
    
    if not os.path.exists(test_file):
        print("Confirmed file is gone.")
    
    # 5. Restore
    print("Attempting restore...")
    file_manager.restore_file(os.path.abspath(test_file), backup_path)
    
    if os.path.exists(test_file):
        print("SUCCESS: File restored.")
        with open(test_file, "r") as f:
            content = f.read()
            if content == "Important Data":
                print("SUCCESS: Content matches.")
            else:
                print("FAILURE: Content mismatch.")
    else:
        print("FAILURE: File not restored.")

    # Cleanup
    try:
        os.remove(test_file)
        os.remove(backup_path)
        # Clean DB
        conn = sqlite3.connect(database.DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM files WHERE original_path=?", (os.path.abspath(test_file),))
        conn.commit()
        conn.close()
    except:
        pass

if __name__ == "__main__":
    import sqlite3
    database.init_db()
    test_hard_link_protection()
