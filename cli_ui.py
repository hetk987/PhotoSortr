"""
CLI UI Module
Handles terminal user interface and input.
"""

import sys
import tty
import termios
from typing import List, Optional


def get_keypress() -> str:
    """
    Get a single keypress from the user without requiring Enter.
    
    Returns:
        The character pressed (uppercase)
    """
    # Save terminal settings
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        # Set terminal to raw mode
        tty.setraw(fd)
        # Read single character
        char = sys.stdin.read(1)
        
        # Handle Ctrl+C
        if char == '\x03':
            raise KeyboardInterrupt
            
        return char.upper()
    finally:
        # Restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def show_menu(event_folders: List[str], current_index: int, total: int, 
              photo_path: str, show_duplicate_option: bool = False) -> None:
    """
    Display the interactive menu to the user.
    
    Args:
        event_folders: List of available event folder names
        current_index: Current photo index (0-based)
        total: Total number of photos
        photo_path: Path to the current photo
        show_duplicate_option: Whether to show the duplicate marking option
    """
    # Clear screen
    print("\033[2J\033[H", end='')
    
    # Show progress with percentage
    percentage = int((current_index / total) * 100) if total > 0 else 0
    progress_bar_width = 40
    filled = int((current_index / total) * progress_bar_width) if total > 0 else 0
    bar = '█' * filled + '░' * (progress_bar_width - filled)
    
    print(f"\n{'='*60}")
    print(f"  Photo Sorter - [{current_index + 1}/{total}] ({percentage}%)")
    print(f"  {bar}")
    print(f"{'='*60}\n")
    
    # Show current photo
    import os
    filename = os.path.basename(photo_path)
    print(f"Current Photo: {filename}")
    print(f"Full Path: {photo_path}\n")
    
    # Show event folders
    if event_folders:
        print("Event Folders:")
        for i, folder in enumerate(event_folders[:9], 1):  # Limit to 9 folders
            print(f"  {i}) {folder}")
        print()
    
    # Show options
    print("Actions:")
    if event_folders:
        print("  [1-9] Move to event folder")
    print("  [N]   Create new event folder")
    print("  [S]   Skip this photo")
    print("  [D]   Delete this photo")
    print("  [Z]   Undo last action")
    if show_duplicate_option:
        print("  [U]   Mark as duplicate")
    print("  [Q]   Quit and save progress")
    print()
    
    print("Choose action: ", end='', flush=True)


def prompt_new_folder_name() -> Optional[str]:
    """
    Prompt user for a new folder name.
    
    Returns:
        The folder name entered by user, or None if cancelled
    """
    print("\n\nEnter new folder name (or press Enter to cancel): ", end='', flush=True)
    name = input().strip()
    
    if not name:
        return None
    
    return name


def prompt_confirmation(message: str) -> bool:
    """
    Ask user for yes/no confirmation.
    
    Args:
        message: The confirmation message to display
        
    Returns:
        True if user confirmed (Y), False otherwise
    """
    print(f"\n{message} (Y/N): ", end='', flush=True)
    
    # Get keypress
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1).upper()
        print(char)  # Echo the character
        return char == 'Y'
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def print_summary(sorted_count: int, skipped_count: int, deleted_count: int, 
                  duplicate_count: int = 0) -> None:
    """
    Print a summary of the sorting session.
    
    Args:
        sorted_count: Number of photos sorted into folders
        skipped_count: Number of photos skipped
        deleted_count: Number of photos deleted
        duplicate_count: Number of duplicates found/moved
    """
    print("\n" + "="*60)
    print("  Sorting Session Summary")
    print("="*60)
    print(f"  Photos sorted:    {sorted_count}")
    print(f"  Photos skipped:   {skipped_count}")
    print(f"  Photos deleted:   {deleted_count}")
    if duplicate_count > 0:
        print(f"  Duplicates found: {duplicate_count}")
    print("="*60 + "\n")

