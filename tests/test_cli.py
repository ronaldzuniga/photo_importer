import pytest
from photo_importer.cli import parse_args, main
import sys
from unittest.mock import patch

def test_parse_args_valid():
    """Test parsing valid command line arguments."""
    test_args = ['--from', '/source', '--to', '/target']
    with patch.object(sys, 'argv', ['photo-importer'] + test_args):
        args = parse_args()
        assert args.source_dir == '/source'
        assert args.target_dir == '/target'
        assert not args.skip_existing
        assert not args.overwrite
        assert args.max_errors == 10

def test_parse_args_with_options():
    """Test parsing command line arguments with optional flags."""
    test_args = [
        '--from', '/source',
        '--to', '/target',
        '--skip-existing',
        '--max-errors', '5'
    ]
    with patch.object(sys, 'argv', ['photo-importer'] + test_args):
        args = parse_args()
        assert args.source_dir == '/source'
        assert args.target_dir == '/target'
        assert args.skip_existing
        assert not args.overwrite
        assert args.max_errors == 5

def test_parse_args_missing_required():
    """Test that missing required arguments raises an error."""
    test_args = ['--from', '/source']  # Missing --to
    with patch.object(sys, 'argv', ['photo-importer'] + test_args):
        with pytest.raises(SystemExit):
            parse_args()

def test_main_success(tmp_path):
    """Test successful execution of main function."""
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()
    
    test_args = [
        '--from', str(source_dir),
        '--to', str(target_dir)
    ]
    
    with patch.object(sys, 'argv', ['photo-importer'] + test_args):
        assert main() == 0

def test_main_invalid_source():
    """Test main function with invalid source directory."""
    test_args = [
        '--from', '/nonexistent/source',
        '--to', '/target'
    ]
    
    with patch.object(sys, 'argv', ['photo-importer'] + test_args):
        assert main() == 1
