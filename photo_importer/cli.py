"""Command-line interface for Photo Importer."""

import argparse
import sys
from .importer import PhotoImporter

def main():
    """Entry point for the photo-importer command."""
    parser = argparse.ArgumentParser(
        description="Import and organize photos by their date taken."
    )
    parser.add_argument(
        "--from",
        dest="source_dir",
        required=True,
        help="Source directory containing photos"
    )
    parser.add_argument(
        "--to",
        dest="target_dir",
        required=True,
        help="Target directory for organized photos"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that already exist in the target directory"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in the target directory"
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=10,
        help="Maximum number of errors before aborting (default: 10)"
    )

    args = parser.parse_args()

    if args.skip_existing and args.overwrite:
        print("Error: Cannot use both --skip-existing and --overwrite")
        sys.exit(1)

    importer = PhotoImporter(
        source_dir=args.source_dir,
        target_dir=args.target_dir,
        skip_existing=args.skip_existing,
        overwrite=args.overwrite,
        max_errors=args.max_errors
    )
    
    try:
        stats = importer.run()
        print(f"\nImport completed successfully!")
        print(f"Files processed: {stats.processed}")
        print(f"Files imported: {stats.imported}")
        print(f"Files skipped: {stats.skipped}")
        print(f"Errors encountered: {stats.errors}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
