"""
Directory Scanner Module
Recursively scans directories for image files.
"""

import os
from typing import List


SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.heic', '.webp', 
    '.tiff', '.tif', '.gif', '.bmp', '.raw', 
    '.cr2', '.nef', '.arw', '.dng'
}


def is_image(filename: str) -> bool:
    """
    Check if a file is a supported image format.
    
    Args:
        filename: The name of the file to check
        
    Returns:
        True if the file extension is supported, False otherwise
    """
    _, ext = os.path.splitext(filename)
    return ext.lower() in SUPPORTED_EXTENSIONS


def scan_images(root_dir: str) -> List[str]:
    """
    Recursively scan a directory for all image files.
    
    Args:
        root_dir: The root directory to scan
        
    Returns:
        A sorted list of absolute paths to all image files found
        
    Raises:
        ValueError: If directory doesn't exist or is not a directory
        PermissionError: If directory cannot be accessed
    """
    if not os.path.exists(root_dir):
        raise ValueError(f"Directory does not exist: {root_dir}")
    
    if not os.path.isdir(root_dir):
        raise ValueError(f"Path is not a directory: {root_dir}")
    
    image_files = []
    errors = []
    
    try:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Skip hidden directories and the .photosorter directory
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            
            for filename in filenames:
                # Skip hidden files
                if filename.startswith('.'):
                    continue
                    
                if is_image(filename):
                    full_path = os.path.join(dirpath, filename)
                    try:
                        # Verify file is accessible
                        if os.path.isfile(full_path):
                            image_files.append(full_path)
                    except (OSError, PermissionError) as e:
                        errors.append(f"Cannot access {full_path}: {e}")
    except PermissionError as e:
        raise PermissionError(f"Cannot access directory {root_dir}: {e}")
    
    # Report errors if any
    if errors:
        print(f"Warning: {len(errors)} files could not be accessed")
    
    # Sort for consistent ordering
    image_files.sort()
    
    return image_files

