import unittest
import os
import shutil
import database
import file_manager

class TestFolderProtection(unittest.TestCase):
    def setUp(self):
        # Setup test environment
        self.test_dir = "test_folder_data"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        
        # Create subdirectories and files
        os.makedirs(os.path.join(self.test_dir, "sub1"))
        os.makedirs(os.path.join(self.test_dir, "sub2"))
        
        with open(os.path.join(self.test_dir, "file1.txt"), "w") as f:
            f.write("content1")
        with open(os.path.join(self.test_dir, "sub1", "file2.txt"), "w") as f:
            f.write("content2")
        with open(os.path.join(self.test_dir, "sub2", "file3.txt"), "w") as f:
            f.write("content3")
        
        # Use a separate test database
        database.DB_NAME = "test_folder_protection.db"
        database.init_db()
        
        # Use a separate vault
        file_manager.VAULT_DIR = "test_folder_vault"
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

    def test_protect_folder_recursive(self):
        # Simulate what the GUI does: walk and protect
        count = 0
        for root, dirs, files in os.walk(self.test_dir):
            for file in files:
                filepath = os.path.join(root, file)
                file_manager.protect_file(filepath)
                count += 1
        
        # Verify count
        self.assertEqual(count, 3)
        
        # Verify database entries
        files = database.get_all_files()
        self.assertEqual(len(files), 3)
        
        # Verify paths in database
        paths = [f[1] for f in files]
        self.assertIn(os.path.abspath(os.path.join(self.test_dir, "file1.txt")), paths)
        self.assertIn(os.path.abspath(os.path.join(self.test_dir, "sub1", "file2.txt")), paths)
        self.assertIn(os.path.abspath(os.path.join(self.test_dir, "sub2", "file3.txt")), paths)

if __name__ == '__main__':
    unittest.main()
