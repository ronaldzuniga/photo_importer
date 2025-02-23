#!/usr/bin/env python3
import os
import argparse
import shutil
import datetime
import exifread
import subprocess
from dataclasses import dataclass, field
from typing import Optional, Set, Tuple

@dataclass
class ImportStats:
    """Statistics for the import process."""
    processed: int = 0
    imported: int = 0
    skipped: int = 0
    errors: int = 0

@dataclass
class ImportConfig:
    """Configuration for the import process."""
    source_dir: str
    target_dir: str
    skip_existing: bool = False
    overwrite: bool = False
    max_errors: int = 10
    allowed_extensions: Set[str] = field(default_factory=lambda: {'.jpg', '.jpeg', '.raf'})

class PhotoImporter:
    """Main class for importing and organizing photos."""

    def extract_date_with_exifread(self, file_path: str) -> Optional[datetime.datetime]:
        """Extract date from image file using exifread library."""
        # Skip RAF files to avoid unwanted output
        if os.path.splitext(file_path)[1].lower() == '.raf':
            return None
            
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                date_str = tags.get("EXIF DateTimeOriginal") or tags.get("Image DateTime")
                if date_str:
                    return datetime.datetime.strptime(str(date_str), '%Y:%m:%d %H:%M:%S')
        except Exception as e:
            print(f"Error reading metadata from {file_path} with exifread: {e}")
        return None

    def extract_date_with_exiftool(self, file_path: str) -> Optional[datetime.datetime]:
        """Extract date from RAF file using exiftool command."""
        try:
            result = subprocess.run(
                ['exiftool', '-DateTimeOriginal', '-s', '-s', '-s', file_path],
                capture_output=True, text=True
            )
            date_str = result.stdout.strip()
            if date_str:
                return datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except Exception as e:
            print(f"Error using exiftool on {file_path}: {e}")
        return None

    def get_date_taken(self, file_path: str) -> Optional[datetime.datetime]:
        """
        Extract the date taken from an image file.
        Uses exiftool for RAF files and exifread for other formats.
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        # Use exiftool directly for RAF files
        if ext == '.raf':
            return self.extract_date_with_exiftool(file_path)
            
        # Use exifread for other formats
        date = self.extract_date_with_exifread(file_path)
        return date

    def create_destination_directory(self, path: str) -> bool:
        """Create directory and return success status."""
        try:
            os.makedirs(path, exist_ok=True)
            # Verify we can write to the directory
            if not os.access(path, os.W_OK):
                print(f"Error: No write permission for directory '{path}'")
                return False
            return True
        except Exception as e:
            print(f"Error creating directory '{path}': {e}")
            return False

    def get_unique_destination_path(self, dest_path: str) -> str:
        """Generate a unique destination path by appending a counter if needed."""
        if not os.path.exists(dest_path):
            return dest_path
        
        base, ext = os.path.splitext(dest_path)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = f"{base}_{counter}{ext}"
            counter += 1
        return dest_path

    def copy_file(self, source: str, destination: str) -> bool:
        """Copy file and return success status."""
        try:
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            print(f"Error copying '{source}' to '{destination}': {e}")
            return False

    def process_file(self, file_path: str, config: ImportConfig, stats: ImportStats) -> bool:
        """Process a single file and return True if processing should continue."""
        stats.processed += 1
        
        # Check if we've already hit max errors
        if stats.errors >= config.max_errors:
            return False

        date_taken = self.get_date_taken(file_path)
        if date_taken is None:
            print(f"[{stats.processed}] Skipping '{file_path}': No valid date metadata found.")
            return True

        dest_dir = os.path.join(
            config.target_dir,
            date_taken.strftime('%Y'),
            date_taken.strftime('%m'),
            date_taken.strftime('%d')
        )
        
        if not self.create_destination_directory(dest_dir):
            stats.errors += 1
            return stats.errors < config.max_errors

        dest_path = os.path.join(dest_dir, os.path.basename(file_path))
        
        if os.path.exists(dest_path):
            if config.skip_existing:
                print(f"[{stats.processed}] Skipping existing file: '{dest_path}'")
                stats.skipped += 1
                return True
            elif not config.overwrite:
                dest_path = self.get_unique_destination_path(dest_path)

        action_msg = "Overwriting" if config.overwrite and os.path.exists(dest_path) else "Copying"
        
        if self.copy_file(file_path, dest_path):
            stats.imported += 1
            percent = (stats.processed / (stats.processed or 1)) * 100
            print(f"[{stats.processed} - {percent:.1f}%] {action_msg} '{file_path}' -> '{dest_path}'")
            return True
        else:
            stats.errors += 1
            return stats.errors < config.max_errors

    def validate_arguments(self, args: argparse.Namespace) -> Tuple[bool, Optional[ImportConfig]]:
        """Validate command line arguments and return config if valid."""
        if args.skip_existing and args.overwrite:
            print("Error: Cannot use both --skip-existing and --overwrite flags")
            return False, None

        source_dir = os.path.abspath(args.source_dir)
        target_dir = os.path.abspath(args.target_dir)

        if not os.path.exists(source_dir):
            print(f"Error: Source directory '{source_dir}' does not exist")
            return False, None

        if not os.path.isdir(source_dir):
            print(f"Error: Source path '{source_dir}' is not a directory")
            return False, None

        if not os.access(source_dir, os.R_OK):
            print(f"Error: No read permission for source directory '{source_dir}'")
            return False, None

        config = ImportConfig(
            source_dir=source_dir,
            target_dir=target_dir,
            skip_existing=args.skip_existing,
            overwrite=args.overwrite,
            max_errors=args.max_errors
        )
        self.config = config
        return True, config

    def _get_image_files(self) -> list[str]:
        """Get a list of image files in the source directory."""
        image_files = []
        for root, _, files in os.walk(self.config.source_dir):
            for file in files:
                if os.path.splitext(file)[1].lower() in self.config.allowed_extensions:
                    image_files.append(os.path.join(root, file))
        return image_files

    def run(self) -> ImportStats:
        """Run the import process.
        
        Returns:
            ImportStats: Statistics about the import process
        
        Raises:
            ValueError: If run is called before validate_arguments
        """
        if not hasattr(self, 'config'):
            raise ValueError("Must call validate_arguments before run")
            
        stats = ImportStats()
        
        try:
            for file_path in self._get_image_files():
                if not self.process_file(file_path, self.config, stats):
                    break
                    
            return stats
        except Exception as e:
            print(f"Error during import: {str(e)}")
            raise

    def print_summary(self, stats: ImportStats) -> None:
        """Print import process summary."""
        print(f"\nSummary:")
        print(f"- Total files processed: {stats.processed}")
        print(f"- Successfully imported: {stats.imported}")
        print(f"- Skipped existing: {stats.skipped}")
        print(f"- Errors encountered: {stats.errors}")

    def main(self):
        """Main entry point for the photo importer."""
        parser = argparse.ArgumentParser(description="Import pictures and organize them by date taken.")
        parser.add_argument('--from', dest='source_dir', required=True, help='Path to the source folder')
        parser.add_argument('--to', dest='target_dir', required=True, help='Path to the destination folder')
        parser.add_argument('--skip-existing', action='store_true', help='Skip files that already exist in destination')
        parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files instead of creating unique names')
        parser.add_argument('--max-errors', type=int, default=10, help='Maximum number of errors before aborting (default: 10)')
        
        args = parser.parse_args()
        valid, config = self.validate_arguments(args)
        if not valid:
            return

        stats = self.run()
        self.print_summary(stats)

if __name__ == "__main__":
    PhotoImporter().main()
