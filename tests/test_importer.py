import os
import shutil
import tempfile
import unittest
from datetime import datetime
from photo_importer.importer import PhotoImporter, ImportStats, ImportConfig

from PIL import Image
from PIL.ExifTags import TAGS
import piexif

class TestPhotoImporter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.test_dir, "source")
        self.target_dir = os.path.join(self.test_dir, "target")
        os.makedirs(self.source_dir)
        os.makedirs(self.target_dir)
        self.importer = PhotoImporter()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_test_image(self, filename, date_time=None):
        img = Image.new('RGB', (100, 100), color='red')
        if date_time:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_time.strftime("%Y:%m:%d %H:%M:%S")
            exif_bytes = piexif.dump(exif_dict)
            img.save(filename, exif=exif_bytes)
        else:
            img.save(filename)

    def test_import_single_image(self):
        # Create a test image with EXIF data
        test_date = datetime(2024, 1, 1, 12, 0, 0)
        source_file = os.path.join(self.source_dir, "test.jpg")
        self.create_test_image(source_file, test_date)

        # Configure and run the importer
        config = ImportConfig(
            source_dir=self.source_dir,
            target_dir=self.target_dir
        )
        stats = ImportStats()

        # Process the file
        self.assertTrue(self.importer.process_file(source_file, config, stats))

        # Check if the file was imported correctly
        expected_path = os.path.join(self.target_dir, "2024", "01", "01", "test.jpg")
        self.assertTrue(os.path.exists(expected_path))
        self.assertEqual(stats.imported, 1)
        self.assertEqual(stats.errors, 0)

    def test_skip_existing_files(self):
        # Create a test image
        test_date = datetime(2024, 1, 1, 12, 0, 0)
        source_file = os.path.join(self.source_dir, "test.jpg")
        self.create_test_image(source_file, test_date)

        # Create the target directory and a file with the same name
        target_dir = os.path.join(self.target_dir, "2024", "01", "01")
        os.makedirs(target_dir)
        target_file = os.path.join(target_dir, "test.jpg")
        self.create_test_image(target_file)

        # Configure and run the importer with skip_existing=True
        config = ImportConfig(
            source_dir=self.source_dir,
            target_dir=self.target_dir,
            skip_existing=True
        )
        stats = ImportStats()

        # Process the file
        self.assertTrue(self.importer.process_file(source_file, config, stats))
        self.assertEqual(stats.skipped, 1)
        self.assertEqual(stats.imported, 0)

    def test_case_insensitive_extensions(self):
        # Create test images with different case extensions
        test_date = datetime(2024, 1, 1, 12, 0, 0)
        source_files = [
            os.path.join(self.source_dir, f"test{ext}")
            for ext in [".jpg", ".JPG", ".JPEG", ".jpeg"]
        ]
        
        for file in source_files:
            self.create_test_image(file, test_date)

        # Configure and run the importer
        config = ImportConfig(
            source_dir=self.source_dir,
            target_dir=self.target_dir
        )
        
        for file in source_files:
            stats = ImportStats()
            self.assertTrue(self.importer.process_file(file, config, stats))
            self.assertEqual(stats.imported, 1)
            self.assertEqual(stats.errors, 0)

if __name__ == '__main__':
    unittest.main()
