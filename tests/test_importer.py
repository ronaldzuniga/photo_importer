import os
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import subprocess
from photo_importer.importer import PhotoImporter, ImportStats, ImportConfig

from PIL import Image
from PIL.ExifTags import TAGS
import piexif
import pytest

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

    @patch('subprocess.run')
    def test_raf_file_handling(self, mock_run):
        # Mock exiftool response
        mock_process = MagicMock()
        mock_process.stdout = "2024:01:01 12:00:00"
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Create a RAF file (just an empty file with .RAF extension)
        source_file = os.path.join(self.source_dir, "test.RAF")
        with open(source_file, 'wb') as f:
            f.write(b'dummy RAF data')

        config = ImportConfig(
            source_dir=self.source_dir,
            target_dir=self.target_dir
        )
        stats = ImportStats()

        # Process the RAF file
        self.assertTrue(self.importer.process_file(source_file, config, stats))

        # Verify exiftool was called correctly
        mock_run.assert_called_once_with(
            ['exiftool', '-DateTimeOriginal', '-s', '-s', '-s', source_file],
            capture_output=True, text=True
        )

        # Check if the file was imported correctly
        expected_path = os.path.join(self.target_dir, "2024", "01", "01", "test.RAF")
        self.assertTrue(os.path.exists(expected_path))
        self.assertEqual(stats.imported, 1)
        self.assertEqual(stats.errors, 0)

    def test_error_handling_invalid_image(self):
        # Create an invalid image file
        source_file = os.path.join(self.source_dir, "invalid.jpg")
        with open(source_file, 'w') as f:
            f.write("This is not a valid image file")

        config = ImportConfig(
            source_dir=self.source_dir,
            target_dir=self.target_dir
        )
        stats = ImportStats()

        # Process should continue but file should be skipped
        self.assertTrue(self.importer.process_file(source_file, config, stats))
        self.assertEqual(stats.imported, 0)
        self.assertEqual(stats.errors, 0)  # Not counted as error, just skipped
        self.assertEqual(stats.processed, 1)

    def test_error_handling_permission_denied(self):
        # Create a test image
        test_date = datetime(2024, 1, 1, 12, 0, 0)
        source_file = os.path.join(self.source_dir, "test.jpg")
        self.create_test_image(source_file, test_date)

        # Create year/month directories but make them read-only
        year_dir = os.path.join(self.target_dir, "2024")
        month_dir = os.path.join(year_dir, "01")
        os.makedirs(month_dir)
        os.chmod(month_dir, 0o444)

        # Test with max_errors=2
        config = ImportConfig(
            source_dir=self.source_dir,
            target_dir=self.target_dir,
            max_errors=2
        )
        stats = ImportStats()

        # First attempt should return True since we haven't hit max_errors
        self.assertTrue(self.importer.process_file(source_file, config, stats))
        self.assertEqual(stats.imported, 0)
        self.assertEqual(stats.errors, 1)

        # Second attempt should return False since we'll hit max_errors
        self.assertFalse(self.importer.process_file(source_file, config, stats))
        self.assertEqual(stats.imported, 0)
        self.assertEqual(stats.errors, 2)

        # Restore permissions for cleanup
        os.chmod(month_dir, 0o755)

    def test_error_handling_max_errors(self):
        # Create multiple test images
        test_date = datetime(2024, 1, 1, 12, 0, 0)
        source_files = []
        for i in range(5):
            source_file = os.path.join(self.source_dir, f"test_{i}.jpg")
            self.create_test_image(source_file, test_date)
            source_files.append(source_file)

        # Make target directory read-only
        os.chmod(self.target_dir, 0o444)

        config = ImportConfig(
            source_dir=self.source_dir,
            target_dir=self.target_dir,
            max_errors=3
        )
        stats = ImportStats()

        # Process files until max errors is reached
        for file in source_files:
            result = self.importer.process_file(file, config, stats)
            if stats.errors >= config.max_errors:
                self.assertFalse(result)
                break

        self.assertEqual(stats.errors, 3)
        self.assertEqual(stats.imported, 0)

        # Restore permissions for cleanup
        os.chmod(self.target_dir, 0o755)

    def test_validate_arguments_valid(self):
        # Create a mock args object
        class MockArgs:
            pass

        args = MockArgs()
        args.source = self.source_dir
        args.destination = self.target_dir
        args.skip_existing = False
        args.overwrite = False
        args.max_errors = 10

        valid, config = self.importer.validate_arguments(args)
        self.assertTrue(valid)
        self.assertIsNotNone(config)
        self.assertEqual(config.source_dir, os.path.abspath(self.source_dir))
        self.assertEqual(config.target_dir, os.path.abspath(self.target_dir))

    def test_validate_arguments_invalid_source(self):
        class MockArgs:
            def __init__(self):
                self.source = "/nonexistent/path"
                self.destination = "/valid/path"
                self.skip_existing = False
                self.overwrite = False
                self.max_errors = 10

        args = MockArgs()
        valid, config = self.importer.validate_arguments(args)
        self.assertFalse(valid)
        self.assertIsNone(config)

    def test_validate_arguments_mutually_exclusive_flags(self):
        class MockArgs:
            def __init__(self):
                self.source = "/valid/path"
                self.destination = "/valid/path"
                self.skip_existing = True
                self.overwrite = True
                self.max_errors = 10

        args = MockArgs()
        valid, config = self.importer.validate_arguments(args)
        self.assertFalse(valid)
        self.assertIsNone(config)

@pytest.mark.usefixtures("tmp_path", "capsys")
def test_get_date_taken_raf_file_no_unwanted_output(tmp_path, capsys):
    """Test that RAF file processing doesn't print 'File format not recognized'."""
    # Create a mock RAF file
    raf_file = tmp_path / "test.RAF"
    raf_file.write_bytes(b"Mock RAF file content")
    
    importer = PhotoImporter()
    importer.get_date_taken(str(raf_file))
    
    # Check captured output
    captured = capsys.readouterr()
    assert "File format not recognized" not in captured.out
    assert "File format not recognized" not in captured.err

if __name__ == '__main__':
    unittest.main()
