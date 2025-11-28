"""
Folder Manager Module
Manages event folders and file operations.
"""

import os
import shutil
from typing import List


def list_event_folders(year_dir: str) -> List[str]:
    """
    List all event folders in a directory.
    
    Args:
        year_dir: The directory to search for event folders
        
    Returns:
        List of event folder names (not full paths)
    """
    if not os.path.exists(year_dir):
        return []
    
    if not os.path.isdir(year_dir):
        return []
    
    folders = []
    for item in os.listdir(year_dir):
        item_path = os.path.join(year_dir, item)
        # Skip hidden folders and files
        if item.startswith('.'):
            continue
        if os.path.isdir(item_path):
            folders.append(item)
    
    return folders


def create_event_folder(year_dir: str, name: str) -> str:
    """
    Create a new event folder.
    
    Args:
        year_dir: The directory where the event folder should be created
        name: The name of the event folder
        
    Returns:
        The full path to the created folder
        
    Raises:
        ValueError: If the folder name is invalid
        FileExistsError: If the folder already exists
    """
    if not name or name.strip() == '':
        raise ValueError("Folder name cannot be empty")
    
    # Clean the folder name
    name = name.strip()
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in name:
            raise ValueError(f"Folder name contains invalid character: {char}")
    
    folder_path = os.path.join(year_dir, name)
    
    if os.path.exists(folder_path):
        raise FileExistsError(f"Folder already exists: {name}")
    
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def move_photo(src: str, dest_folder: str) -> str:
    """
    Move a photo to a destination folder.
    
    Args:
        src: Source file path
        dest_folder: Destination folder path
        
    Returns:
        The new path of the moved file
        
    Raises:
        FileNotFoundError: If source file doesn't exist
        ValueError: If destination is not a directory
    """
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source file not found: {src}")
    
    if not os.path.exists(dest_folder):
        raise ValueError(f"Destination folder does not exist: {dest_folder}")
    
    if not os.path.isdir(dest_folder):
        raise ValueError(f"Destination is not a directory: {dest_folder}")
    
    filename = os.path.basename(src)
    dest_path = os.path.join(dest_folder, filename)
    
    # Handle filename conflicts
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            new_filename = f"{base}_{counter}{ext}"
            dest_path = os.path.join(dest_folder, new_filename)
            counter += 1
    
    shutil.move(src, dest_path)
    return dest_path

