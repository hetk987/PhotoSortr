"""
Main Sorter Module
Orchestrates the photo sorting workflow.
"""

import os
import logging
import shutil
from typing import List, Optional
from datetime import datetime

import directory_scanner
import os_viewer
import folder_manager
import cli_ui
import state_manager
import duplicate_detector


def setup_logging(root_dir: str) -> logging.Logger:
    """
    Setup logging for the photo sorter.
    
    Args:
        root_dir: Root directory for log file
        
    Returns:
        Configured logger instance
    """
    log_dir = os.path.join(root_dir, '.photosorter')
    os.makedirs(log_dir, exist_ok=True)
        
    log_file = os.path.join(log_dir, 'sorter.log')
    
    # Create logger
    logger = logging.getLogger('photosorter')
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger


class PhotoSorter:
    """Main photo sorting orchestrator."""
    
    def __init__(self, root_dir: str, auto_move_duplicates: bool = True, 
                 duplicate_threshold: int = 5):
        """
        Initialize the photo sorter.
        
        Args:
            root_dir: Root directory containing photos to sort
            auto_move_duplicates: Automatically move duplicates without prompting
            duplicate_threshold: Perceptual hash distance threshold for duplicates
        """
        self.root_dir = os.path.abspath(root_dir)
        self.trash_dir = os.path.join(self.root_dir, '.trash')
        self.images: List[str] = []
        self.current_index: int = 0
        self.sorted_count: int = 0
        self.skipped_count: int = 0
        self.deleted_count: int = 0
        self.duplicate_count: int = 0
        self.state: dict = {}
        self.auto_move_duplicates: bool = auto_move_duplicates
        self.duplicate_threshold: int = duplicate_threshold
        self.hash_db: Optional[duplicate_detector.HashDatabase] = None
        self.logger = setup_logging(root_dir)
        self.session_start = datetime.now()
        
    def load_images(self) -> None:
        """Load all images from the root directory."""
        print("Scanning for images...")
        self.logger.info(f"Starting scan of directory: {self.root_dir}")
        self.images = directory_scanner.scan_images(self.root_dir)
        print(f"Found {len(self.images)} images.\n")
        self.logger.info(f"Found {len(self.images)} images")
        
        if len(self.images) == 0:
            print("No images found to sort.")
            return
    
    def load_state(self) -> None:
        """Load saved state from previous sessions."""
        self.state = state_manager.load_state(self.root_dir)
        self.current_index = self.state.get('last_index', 0)
        self.sorted_count = self.state.get('sorted_count', 0)
        self.skipped_count = self.state.get('skipped_count', 0)
        self.deleted_count = self.state.get('deleted_count', 0)
        self.duplicate_count = self.state.get('duplicate_count', 0)
        
        if self.current_index > 0:
            print(f"Resuming from photo {self.current_index + 1}...")
            print(f"Previous session stats: {self.sorted_count} sorted, "
                  f"{self.skipped_count} skipped, {self.deleted_count} deleted\n")
    
    def load_hash_database(self) -> None:
        """Load the hash database for duplicate detection."""
        print("Loading hash database...")
        self.hash_db = duplicate_detector.HashDatabase(self.root_dir)
        print(f"Loaded {len(self.hash_db.hashes)} cached hashes.\n")
    
    def save_state(self) -> None:
        """Save current state to disk."""
        self.state['last_index'] = self.current_index
        self.state['sorted_count'] = self.sorted_count
        self.state['skipped_count'] = self.skipped_count
        self.state['deleted_count'] = self.deleted_count
        self.state['duplicate_count'] = self.duplicate_count
        state_manager.save_state(self.root_dir, self.state)
    
    def run(self) -> None:
        """Run the main sorting loop."""
        self.logger.info("="*60)
        self.logger.info(f"Photo Sorter session started at {self.session_start}")
        self.logger.info("="*60)
        
        self.load_images()
        
        if len(self.images) == 0:
            return
        
        self.load_state()
        self.load_hash_database()
        
        # Check for existing trash from previous session
        os.makedirs(self.trash_dir, exist_ok=True)
        if os.path.exists(self.trash_dir):
            try:
                files = os.listdir(self.trash_dir)
                if files:
                    print(f"\n⚠️  Found {len(files)} file(s) in trash from previous session")
                    response = input("Empty trash from previous session? (y/n): ").strip().lower()
                    if response == 'y':
                        self._empty_trash()
                        print("Trash cleared.\n")
                    else:
                        print("Trash will be emptied when this session ends.\n")
            except Exception as e:
                self.logger.warning(f"Error checking trash on startup: {e}")
        
        try:
            self._sorting_loop()
        except KeyboardInterrupt:
            print("\n\nSorting interrupted by user.")
            self.logger.warning("Session interrupted by user (Ctrl+C)")
            self.save_state()
        except Exception as e:
            self.logger.error(f"Fatal error during sorting: {e}", exc_info=True)
            raise
        finally:
            self._empty_trash()
            self._print_summary()
            self._log_summary()
    
    def _sorting_loop(self) -> None:
        """Main loop for sorting photos."""
        while self.current_index < len(self.images):
            photo_path = self.images[self.current_index]
            
            # Check if file still exists (might have been moved/deleted)
            if not os.path.exists(photo_path):
                self.logger.warning(f"File no longer exists: {photo_path}")
                self.current_index += 1
                continue
            
            # Check for duplicates
            try:
                is_dup, dup_type, original_file = duplicate_detector.is_duplicate(
                    photo_path, self.hash_db, self.duplicate_threshold)
                
                if is_dup:
                    if self.auto_move_duplicates:
                        self._handle_duplicate(photo_path, dup_type, original_file)
                        self.duplicate_count += 1
                        self.current_index += 1
                        self.save_state()
                        continue
                    else:
                        print(f"\n{'='*60}")
                        print(f"DUPLICATE DETECTED ({dup_type})")
                        print(f"Original: {original_file}")
                        print(f"{'='*60}\n")
            except Exception as e:
                self.logger.error(f"Error checking for duplicates on {photo_path}: {e}")
                # Continue with normal flow
            
            # Open image in viewer
            try:
                os_viewer.open_image(photo_path)
            except FileNotFoundError:
                self.logger.error(f"File not found when trying to open: {photo_path}")
                print(f"\nError: File not found")
                print("Skipping to next image...")
                self.current_index += 1
                continue
            except Exception as e:
                self.logger.error(f"Error opening image {photo_path}: {e}")
                print(f"\nError opening image: {e}")
                print("Skipping to next image...")
                self.current_index += 1
                continue
            
            # Get event folders
            event_folders = folder_manager.list_event_folders(self.root_dir)
            
            # Show menu and get user choice
            cli_ui.show_menu(event_folders, self.current_index, 
                           len(self.images), photo_path, 
                           show_duplicate_option=True)
            
            try:
                choice = cli_ui.get_keypress()
                action_result = self._handle_choice(choice, photo_path, event_folders)
                
                # Close the viewer after action (except for retry)
                if action_result != 'retry':
                    os_viewer.close_image()
                
                if action_result == 'quit':
                    self.save_state()
                    break
                elif action_result == 'moved':
                    # Add to hash database after successful move
                    duplicate_detector.add_to_hash_db(photo_path, self.hash_db)
                    self.sorted_count += 1
                    self.current_index += 1
                    self.save_state()
                elif action_result == 'skipped':
                    self.skipped_count += 1
                    state_manager.add_skipped_file(self.state, photo_path)
                    self.current_index += 1
                    self.save_state()
                elif action_result == 'deleted':
                    self.deleted_count += 1
                    self.current_index += 1
                    self.save_state()
                elif action_result == 'duplicate':
                    self._handle_duplicate(photo_path, 'manual', None)
                    self.duplicate_count += 1
                    self.current_index += 1
                    self.save_state()
                elif action_result == 'retry':
                    # Stay on same image
                    continue
                    
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"\nError processing choice: {e}")
                print("Press any key to continue...")
                cli_ui.get_keypress()
    
    def _handle_choice(self, choice: str, photo_path: str, 
                       event_folders: List[str]) -> str:
        """
        Handle user's menu choice.
        
        Args:
            choice: The user's keypress choice
            photo_path: Path to current photo
            event_folders: List of available event folders
            
        Returns:
            Action result: 'moved', 'skipped', 'deleted', 'quit', or 'retry'
        """
        # Handle numeric choices (move to folder)
        if choice.isdigit():
            folder_index = int(choice) - 1
            if 0 <= folder_index < len(event_folders):
                folder_name = event_folders[folder_index]
                dest_folder = os.path.join(self.root_dir, folder_name)
                try:
                    new_path = folder_manager.move_photo(photo_path, dest_folder)
                    action = {
                        'action': 'moved',
                        'old_path': photo_path,
                        'new_path': new_path
                    }
                    state_manager.add_action_to_history(self.state, action)
                    print(f"\nMoved to: {folder_name}")
                    self.logger.info(f"MOVED: {os.path.basename(photo_path)} -> {folder_name}")
                    return 'moved'
                except Exception as e:
                    print(f"\nError moving photo: {e}")
                    self.logger.error(f"Error moving {photo_path} to {folder_name}: {e}")
                    print("Press any key to continue...")
                    cli_ui.get_keypress()
                    return 'retry'
            else:
                print("\nInvalid folder number. Press any key to retry...")
                cli_ui.get_keypress()
                return 'retry'
        
        # Create new folder
        elif choice == 'N':
            folder_name = cli_ui.prompt_new_folder_name()
            if folder_name:
                try:
                    dest_folder = folder_manager.create_event_folder(
                        self.root_dir, folder_name)
                    new_path = folder_manager.move_photo(photo_path, dest_folder)
                    action = {
                        'action': 'moved',
                        'old_path': photo_path,
                        'new_path': new_path
                    }
                    state_manager.add_action_to_history(self.state, action)
                    print(f"\nCreated folder '{folder_name}' and moved photo.")
                    self.logger.info(f"CREATED FOLDER: {folder_name}")
                    self.logger.info(f"MOVED: {os.path.basename(photo_path)} -> {folder_name}")
                    return 'moved'
                except Exception as e:
                    print(f"\nError: {e}")
                    self.logger.error(f"Error creating folder '{folder_name}' or moving photo: {e}")
                    print("Press any key to continue...")
                    cli_ui.get_keypress()
                    return 'retry'
            else:
                return 'retry'
        
        # Skip
        elif choice == 'S':
            print("\nSkipped.")
            self.logger.info(f"SKIPPED: {os.path.basename(photo_path)}")
            return 'skipped'
        
        # Mark as duplicate
        elif choice == 'U':
            return 'duplicate'
        
        # Delete
        elif choice == 'D':
            if cli_ui.prompt_confirmation("Are you sure you want to delete this photo?"):
                try:
                    self._move_to_trash(photo_path)
                    # Store the full path to the file in trash
                    filename = os.path.basename(photo_path)
                    trash_file_path = os.path.join(self.trash_dir, filename)
                    action = {
                        'action': 'deleted',
                        'old_path': photo_path,
                        'new_path': trash_file_path
                    }
                    state_manager.add_action_to_history(self.state, action)
                    print("\nPhoto deleted.")
                    self.logger.warning(f"DELETED: {photo_path}")
                    return 'deleted'
                except Exception as e:
                    print(f"\nError deleting photo: {e}")
                    self.logger.error(f"Error deleting {photo_path}: {e}")
                    print("Press any key to continue...")
                    cli_ui.get_keypress()
                    return 'retry'
            else:
                print("\nDeletion cancelled.")
                return 'retry'
            
        # Undo last action
        elif choice == 'Z':
            print("\nUndoing last action...")
            self._undo_last_action()
            print("\nLast action undone.")
            self.logger.info("UNDO: Last action undone")
            return 'retry'
        
        # Quit
        elif choice == 'Q':
            print("\nQuitting...")
            return 'quit'
        
        # Invalid choice
        else:
            print("\nInvalid choice. Press any key to retry...")
            cli_ui.get_keypress()
            return 'retry'
    
    def _handle_duplicate(self, photo_path: str, dup_type: str, 
                         original_file: Optional[str]) -> None:
        """
        Handle a duplicate photo by moving it to Duplicates folder.
        
        Args:
            photo_path: Path to the duplicate photo
            dup_type: Type of duplicate ('exact', 'similar', or 'manual')
            original_file: Path to original file (if known)
        """
        duplicates_folder = os.path.join(self.root_dir, 'Duplicates')
        
        # Create duplicates folder if it doesn't exist
        if not os.path.exists(duplicates_folder):
            os.makedirs(duplicates_folder, exist_ok=True)
        
        try:
            new_path = folder_manager.move_photo(photo_path, duplicates_folder)
            print(f"\nMoved to Duplicates folder ({dup_type})")
            if original_file:
                print(f"Original: {os.path.basename(original_file)}")
                self.logger.info(f"DUPLICATE ({dup_type}): {os.path.basename(photo_path)} -> Duplicates (original: {os.path.basename(original_file)})")
            else:
                self.logger.info(f"DUPLICATE ({dup_type}): {os.path.basename(photo_path)} -> Duplicates")
        except Exception as e:
            print(f"\nError moving duplicate: {e}")
            self.logger.error(f"Error moving duplicate {photo_path}: {e}")
            
    def _move_to_trash(self, photo_path: str) -> None:
        """Move a photo to the trash directory."""
        try:
            shutil.move(photo_path, self.trash_dir)
            print(f"\nMoved to trash: {photo_path}")
            self.logger.info(f"MOVED TO TRASH: {photo_path}")
        except Exception as e:
            print(f"\nError moving to trash: {e}")
            self.logger.error(f"Error moving {photo_path} to trash: {e}")
    
    def _empty_trash(self) -> None:
        """Permanently delete all files in the trash directory."""
        if not os.path.exists(self.trash_dir):
            return
        
        # Count files in trash
        try:
            files = os.listdir(self.trash_dir)
            file_count = len(files)
            
            if file_count == 0:
                return
            
            # Inform user
            print(f"\n🗑️  Permanently deleting {file_count} photo(s) from trash...")
            self.logger.info(f"Emptying trash: {file_count} files")
            
            # Delete the entire trash directory
            shutil.rmtree(self.trash_dir)
            
            # Recreate empty trash directory
            os.makedirs(self.trash_dir, exist_ok=True)
            
            print("✓ Trash emptied")
            self.logger.info("Trash emptied successfully")
            
        except Exception as e:
            print(f"⚠️  Error emptying trash: {e}")
            self.logger.error(f"Failed to empty trash: {e}")
    
    def _undo_last_action(self) -> None:
        """Undo the last action."""
        # Check if there are any actions to undo
        if not self.state.get('action_history') or len(self.state['action_history']) == 0:
            print("\nNo actions to undo.")
            self.logger.info("Undo attempted but no actions in history")
            return
        
        last_action = state_manager.get_last_action(self.state)
        
        try:
            if last_action['action'] == 'moved':
                # For moved files, new_path is the full path to the file in the destination folder
                # old_path is the original location
                if os.path.exists(last_action['new_path']):
                    shutil.move(last_action['new_path'], last_action['old_path'])
                    self.sorted_count -= 1
                    self.current_index -= 1  # Go back to the previous photo
                    state_manager.pop_last_action(self.state)
                    self.save_state()
                    print(f"\nUndone: Restored {os.path.basename(last_action['old_path'])} to original location")
                    self.logger.info(f"UNDO MOVE: {last_action['new_path']} -> {last_action['old_path']}")
                else:
                    print(f"\nCannot undo: File not found at {last_action['new_path']}")
                    self.logger.warning(f"UNDO FAILED: File not found at {last_action['new_path']}")
                    
            elif last_action['action'] == 'deleted':
                # For deleted files, new_path is the full path to the file in trash
                # old_path is the original location
                if os.path.exists(last_action['new_path']):
                    shutil.move(last_action['new_path'], last_action['old_path'])
                    self.deleted_count -= 1
                    self.current_index -= 1  # Go back to the previous photo
                    state_manager.pop_last_action(self.state)
                    self.save_state()
                    print(f"\nUndone: Restored {os.path.basename(last_action['old_path'])} from trash")
                    self.logger.info(f"UNDO DELETE: {last_action['new_path']} -> {last_action['old_path']}")
                else:
                    print(f"\nCannot undo: File not found in trash")
                    self.logger.warning(f"UNDO FAILED: File not found at {last_action['new_path']}")
                    
        except Exception as e:
            print(f"\nError undoing action: {e}")
            self.logger.error(f"UNDO FAILED: {e}")
        
    def _print_summary(self) -> None:
        """Print summary of the sorting session."""
        cli_ui.print_summary(self.sorted_count, self.skipped_count, 
                           self.deleted_count, self.duplicate_count)
    
    def _log_summary(self) -> None:
        """Log session summary."""
        session_end = datetime.now()
        duration = session_end - self.session_start
        
        self.logger.info("="*60)
        self.logger.info("Session Summary:")
        self.logger.info(f"  Duration: {duration}")
        self.logger.info(f"  Photos sorted: {self.sorted_count}")
        self.logger.info(f"  Photos skipped: {self.skipped_count}")
        self.logger.info(f"  Photos deleted: {self.deleted_count}")
        self.logger.info(f"  Duplicates found: {self.duplicate_count}")
        self.logger.info(f"Session ended at {session_end}")
        self.logger.info("="*60)

