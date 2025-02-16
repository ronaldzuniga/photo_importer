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
        First attempts to use exifread, then falls back to exiftool for RAF files.
        """
        date = self.extract_date_with_exifread(file_path)
        if date is None and os.path.splitext(file_path)[1].lower() == '.raf':
            date = self.extract_date_with_exiftool(file_path)
        return date

    def create_destination_directory(self, path: str) -> bool:
        """Create directory and return success status."""
        try:
            os.makedirs(path, exist_ok=True)
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

        action_msg = "Overwriting" if config.overwrite and os.path.exists(dest_path) else "Copied"
        
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

        source_dir = os.path.abspath(args.source)
        if not os.path.exists(source_dir):
            print(f"Error: Source folder '{source_dir}' does not exist.")
            return False, None

        target_dir = os.path.abspath(args.destination)
        if not os.path.exists(target_dir) and not self.create_destination_directory(target_dir):
            return False, None

        return True, ImportConfig(
            source_dir=source_dir,
            target_dir=target_dir,
            skip_existing=args.skip_existing,
            overwrite=args.overwrite,
            max_errors=args.max_errors
        )

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
        parser.add_argument('--from', dest='source', required=True, help='Path to the source folder')
        parser.add_argument('--to', dest='destination', required=True, help='Path to the destination folder')
        parser.add_argument('--skip-existing', action='store_true', help='Skip files that already exist in destination')
        parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files instead of creating unique names')
        parser.add_argument('--max-errors', type=int, default=10, help='Maximum number of errors before aborting (default: 10)')
        
        args = parser.parse_args()
        valid, config = self.validate_arguments(args)
        if not valid:
            return

        stats = ImportStats()
        
        for root, _, files in os.walk(config.source_dir):
            for file in files:
                if os.path.splitext(file)[1].lower() not in config.allowed_extensions:
                    continue
                    
                file_path = os.path.join(root, file)
                if not self.process_file(file_path, config, stats):
                    print(f"\nAborting: Too many errors ({stats.errors})")
                    self.print_summary(stats)
                    return

        self.print_summary(stats)

if __name__ == "__main__":
    PhotoImporter().main()
