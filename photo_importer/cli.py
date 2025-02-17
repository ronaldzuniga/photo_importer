"""Command-line interface for Photo Importer."""

import argparse
import sys
from .importer import PhotoImporter

def parse_args(args=None):
    """Parse command line arguments.
    
    Args:
        args: List of arguments to parse. Defaults to sys.argv[1:].
        
    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
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

    return parser.parse_args(args)

def main():
    """Entry point for the photo-importer command.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    args = parse_args()

    if args.skip_existing and args.overwrite:
        print("Error: Cannot use both --skip-existing and --overwrite")
        return 1

    importer = PhotoImporter()
    valid, config = importer.validate_arguments(args)
    
    if not valid:
        return 1
        
    try:
        stats = importer.run()
        print(f"\nImport completed:")
        print(f"  Processed: {stats.processed}")
        print(f"  Imported: {stats.imported}")
        print(f"  Skipped: {stats.skipped}")
        print(f"  Errors: {stats.errors}")
        
        return 0 if stats.errors < config.max_errors else 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
