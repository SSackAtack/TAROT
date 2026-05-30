import unittest
import tempfile
import os
import shutil
from pathlib import Path
from tarotvision.status.path_validator import validate_recording_path

class TestPathValidator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_valid_existing_directory(self):
        valid, message = validate_recording_path(self.temp_dir)
        self.assertTrue(valid)
        self.assertIn("Katalog istnieje", message)
        
    def test_empty_path(self):
        valid, message = validate_recording_path("")
        self.assertFalse(valid)
        self.assertEqual(message, "Ścieżka nie może być pusta")
        
        valid, message = validate_recording_path("   ")
        self.assertFalse(valid)
        self.assertEqual(message, "Ścieżka nie może być pusta")
        
    def test_path_is_file(self):
        # Tworzymy plik tymczasowy w naszym katalogu
        temp_file_path = os.path.join(self.temp_dir, "test_file.txt")
        with open(temp_file_path, "w") as f:
            f.write("hello")
            
        valid, message = validate_recording_path(temp_file_path)
        self.assertFalse(valid)
        self.assertIn("Podana ścieżka jest plikiem", message)
        
    def test_path_traversal(self):
        traversal_path = os.path.join(self.temp_dir, "../some_dir")
        valid, message = validate_recording_path(traversal_path)
        self.assertFalse(valid)
        self.assertIn("nie może zawierać sekwencji '..'", message)
        
    def test_system_directory(self):
        valid, message = validate_recording_path("C:\\Windows")
        self.assertFalse(valid)
        self.assertIn("Dostęp zabroniony: katalog systemowy", message)
        
    def test_create_new_directory(self):
        new_dir_path = os.path.join(self.temp_dir, "new_sub_dir")
        valid, message = validate_recording_path(new_dir_path)
        self.assertTrue(valid)
        self.assertIn("Utworzono nowy katalog", message)
        self.assertTrue(os.path.exists(new_dir_path))
        self.assertTrue(os.path.isdir(new_dir_path))

if __name__ == "__main__":
    unittest.main()
