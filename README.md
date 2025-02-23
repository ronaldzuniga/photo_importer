# Photo Importer

A robust Python utility for organizing photos by their date taken, leveraging EXIF metadata. Perfect for importing and organizing photos from SD cards, cameras, phones, or any external storage device into a structured photo library. This tool helps you maintain a clean and organized photo collection by automatically sorting photos into a year/month/day directory structure.

## Features

- 📅 Organizes photos by date taken using EXIF metadata
- 📁 Creates a hierarchical directory structure (YYYY/MM/DD)
- 🔄 Handles duplicate files with options to skip or overwrite
- 📸 Supports multiple image formats (JPG, JPEG, RAF)
- 🔍 Case-insensitive file extension handling
- ⚠️ Robust error handling with configurable error limits
- 🔒 Safe file operations with detailed progress reporting
- 💾 Direct import from SD cards and external media

## Requirements

- Python 3.9 or higher
- ExifRead 3.0.0
- Pillow 10.2.0
- exiftool (for RAF files)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ronaldzuniga/photo_importer.git
   cd photo_importer
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies and the package:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. For RAF file support, install exiftool:
   - macOS: `brew install exiftool`
   - Linux: `sudo apt-get install exiftool`
   - Windows: Download from [ExifTool website](https://exiftool.org)

## Usage

After installation, you can run the application in two ways:

### 1. Using the installed command

```bash
photo-importer --from SOURCE_DIR --to DESTINATION_DIR [options]
```

### 2. Using Python module directly

```bash
python -m photo_importer.cli --from SOURCE_DIR --to DESTINATION_DIR [options]
```

### Options

- `--from`: Source directory containing photos (required)
- `--to`: Destination directory for the organized photos (required)
- `--skip-existing`: Skip files that already exist in the destination
- `--overwrite`: Overwrite existing files instead of creating unique names
- `--max-errors`: Maximum number of errors before aborting (default: 10)

### Examples

1. Import from SD card (macOS):
   ```bash
   photo-importer --from /Volumes/SD_CARD/DCIM --to ~/Pictures/Photo_Library
   ```

2. Import from SD card (Windows):
   ```bash
   photo-importer --from E:/DCIM --to C:/Users/YourName/Pictures/Photo_Library
   ```

3. Skip existing files:
   ```bash
   photo-importer --from ~/Pictures/Camera --to ~/Pictures/Organized --skip-existing
   ```

4. Using Python module directly with custom error limit:
   ```bash
   python -m photo_importer.cli --from ~/Pictures/Camera --to ~/Pictures/Organized --max-errors 5
   ```

5. Overwrite existing files:
   ```bash
   photo-importer --from ~/Pictures/Camera --to ~/Pictures/Organized --overwrite
   ```

## Directory Structure

The tool organizes photos into the following structure:
```
destination_directory/
├── 2024/
│   ├── 01/
│   │   ├── 01/
│   │   │   ├── photo1.jpg
│   │   │   └── photo2.jpg
│   │   └── 02/
│   │       └── photo3.jpg
│   └── 02/
│       └── 15/
│           └── photo4.jpg
└── 2025/
    └── 01/
        └── 30/
            └── photo5.jpg
```

## Common Use Cases

### Importing from Cameras and SD Cards

The Photo Importer is particularly useful for photographers who need to regularly import and organize photos from their cameras. It supports various scenarios:

1. **Direct Camera Import**: Connect your camera via USB and import directly from the mounted device
2. **SD Card Import**: Use any SD card reader to import from memory cards
3. **Batch Organization**: Process multiple memory cards in sequence
4. **Incremental Import**: Use `--skip-existing` to only import new photos when reprocessing the same card

### Tips for External Media

- Always ensure your SD card or external device is properly mounted before starting the import
- Use `--skip-existing` when doing incremental imports from the same card
- Consider using `--max-errors` with a lower value when working with potentially unreliable media
- Wait for the import to complete before ejecting the media

## Development

### Running Tests

The project includes a comprehensive test suite that covers:
- Core photo importing functionality
- RAF file handling with exiftool
- Error conditions and edge cases
- Command-line argument validation
- File permission handling
- Duplicate file handling

To run the tests:
```bash
python -m pytest tests/test_importer.py -v
```

To run tests with coverage report:
```bash
python -m pytest --cov=photo_importer tests/ --cov-report=term-missing
```

Current test coverage:
- Overall: 60%
- Core importer module: 71%
- Full CLI testing coming soon

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite and ensure all tests pass
5. Ensure your changes maintain or improve the current test coverage
6. Submit a pull request

## Error Handling

The tool includes robust error handling for:

- Invalid source/destination directories
- Missing or corrupt EXIF data
- File access permissions
- Duplicate files
- RAF file processing errors
- Maximum error threshold (configurable)
- Directory creation failures
- Invalid file formats

The tool will:
1. Log all errors with descriptive messages
2. Continue processing after non-critical errors
3. Stop when max_errors threshold is reached
4. Maintain a count of processed, skipped, and failed files

## License

[MIT License](LICENSE)

## Author

Ronald Zúñiga

## Acknowledgments

- ExifRead for EXIF metadata extraction
- Phil Harvey's ExifTool for RAF file support
- Pillow (PIL) for image handling
