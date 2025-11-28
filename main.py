#!/usr/bin/env python3
"""
Photo Sorter - CLI Photo Organization Tool
Main entry point for the application.
"""

import sys
import argparse
import os

import sorter


def main():
    """Main entry point for the photo sorter CLI."""
    parser = argparse.ArgumentParser(
        description='Sort photos into event folders interactively with duplicate detection.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/photos
  %(prog)s ~/Pictures/2021
  %(prog)s --threshold 3 --no-auto-duplicates ~/Photos
  
Keyboard shortcuts:
  1-9  : Move to event folder
  N    : Create new event folder
  S    : Skip photo
  D    : Delete photo
  U    : Mark as duplicate
  Q    : Quit and save progress

Duplicate Detection:
  The tool uses two-level duplicate detection:
  - SHA256 hash for exact duplicates (fast)
  - Perceptual hash for similar images (requires Pillow and imagehash)
  
  Duplicates are automatically moved to a 'Duplicates' folder unless
  --no-auto-duplicates is specified.
        """
    )
    
    parser.add_argument(
        'directory',
        help='Directory containing photos to sort'
    )
    
    parser.add_argument(
        '--no-auto-duplicates',
        action='store_true',
        help='Prompt before moving duplicates instead of auto-moving'
    )
    
    parser.add_argument(
        '--threshold',
        type=int,
        default=5,
        help='Perceptual hash distance threshold for duplicate detection (default: 5, lower = stricter)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Photo Sorter 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.exists(args.directory):
        print(f"Error: Directory does not exist: {args.directory}", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(args.directory):
        print(f"Error: Path is not a directory: {args.directory}", file=sys.stderr)
        sys.exit(1)
    
    # Check if perceptual hashing is available
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        print("Warning: Pillow and/or imagehash not installed.")
        print("Only exact duplicate detection (SHA256) will be available.")
        print("Install with: pip install pillow imagehash\n")
    
    # Create and run sorter
    photo_sorter = sorter.PhotoSorter(
        args.directory,
        auto_move_duplicates=not args.no_auto_duplicates,
        duplicate_threshold=args.threshold
    )
    
    try:
        photo_sorter.run()
    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

