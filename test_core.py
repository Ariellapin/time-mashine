import unittest
import os
import shutil
import database
import file_manager
import time

class TestHistorySaver(unittest.TestCase):
    def setUp(self):
        # Setup test environment
        self.test_dir = "test_data"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        # Use a separate test database
        database.DB_NAME = "test_history_saver.db"
        database.init_db()
        
        # Use a separate vault
        file_manager.VAULT_DIR = "test_vault"
        if os.path.exists(file_manager.VAULT_DIR):
            shutil.rmtree(file_manager.VAULT_DIR)
        file_manager.ensure_vault()

    def tearDown(self):
        # Clean up
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(file_manager.VAULT_DIR):
            shutil.rmtree(file_manager.VAULT_DIR)
        if os.path.exists(database.DB_NAME):
            os.remove(database.DB_NAME)

    def test_protect_and_restore(self):
        # 1. Create a dummy file
        file_path = os.path.join(self.test_dir, "important.txt")
        with open(file_path, "w") as f:
            f.write("This is important data.")
        
        # 2. Protect the file
        file_manager.protect_file(file_path)
        
        # Verify it's in the database
        files = database.get_all_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0][1], os.path.abspath(file_path))
        
        # Verify backup exists
        backup_path = files[0][2]
        self.assertTrue(os.path.exists(backup_path))
        
        # 3. Delete the original file
        os.remove(file_path)
        self.assertFalse(os.path.exists(file_path))
        
        # 4. Restore the file
        file_manager.restore_file(os.path.abspath(file_path), backup_path)
        
        # Verify it's back
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, "This is important data.")

if __name__ == '__main__':
    unittest.main()
