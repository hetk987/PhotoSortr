"""
State Manager Module
Handles saving and loading sorting progress state.
"""

import os
import json
from typing import Dict, Any, List


STATE_DIR_NAME = '.photosorter'
STATE_FILE_NAME = 'state.json'


def _get_state_dir(year_dir: str) -> str:
    """Get the state directory path."""
    return os.path.join(year_dir, STATE_DIR_NAME)


def _get_state_file_path(year_dir: str) -> str:
    """Get the full path to the state file."""
    return os.path.join(_get_state_dir(year_dir), STATE_FILE_NAME)


def _ensure_state_dir_exists(year_dir: str) -> None:
    """Ensure the state directory exists."""
    state_dir = _get_state_dir(year_dir)
    os.makedirs(state_dir, exist_ok=True)


def load_state(year_dir: str) -> Dict[str, Any]:
    """
    Load the sorting state from disk.
    
    Args:
        year_dir: The directory being sorted
        
    Returns:
        Dictionary containing state data, or default state if no save exists
    """
    state_file = _get_state_file_path(year_dir)
    
    # Return default state if file doesn't exist
    if not os.path.exists(state_file):
        return {
            'last_index': 0,
            'sorted_count': 0,
            'skipped_count': 0,
            'deleted_count': 0,
            'duplicate_count': 0,
            'skipped_files': [],
            'action_history': []
        }
    
    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
            
        # Ensure all required fields exist
        default_state = {
            'last_index': 0,
            'sorted_count': 0,
            'skipped_count': 0,
            'deleted_count': 0,
            'duplicate_count': 0,
            'skipped_files': [],
            'action_history': []
        }
        
        for key, default_value in default_state.items():
            if key not in state:
                state[key] = default_value
        
        return state
        
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load state file: {e}")
        print("Starting fresh...")
        return {
            'last_index': 0,
            'sorted_count': 0,
            'skipped_count': 0,
            'deleted_count': 0,
            'duplicate_count': 0,
            'skipped_files': []
        }


def save_state(year_dir: str, state: Dict[str, Any]) -> None:
    """
    Save the sorting state to disk.
    
    Args:
        year_dir: The directory being sorted
        state: State dictionary to save
    """
    _ensure_state_dir_exists(year_dir)
    state_file = _get_state_file_path(year_dir)
    
    try:
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save state: {e}")


def update_last_index(state: Dict[str, Any], index: int) -> None:
    """
    Update the last processed index in the state.
    
    Args:
        state: State dictionary to update
        index: The new index value
    """
    state['last_index'] = index


def add_skipped_file(state: Dict[str, Any], filepath: str) -> None:
    """
    Add a file to the skipped files list.
    
    Args:
        state: State dictionary to update
        filepath: Path to the skipped file
    """
    if 'skipped_files' not in state:
        state['skipped_files'] = []
    
    if filepath not in state['skipped_files']:
        state['skipped_files'].append(filepath)

def add_action_to_history(state: Dict[str, Any], action: Dict[str, any]) -> None:
    """
    Add a action to the action history list.
    
    Args:
        state: State dictionary to update
        action: New action information
    """
    if 'action_history' not in state:
        state['action_history'] = []
    
    if action not in state['action_history']:
        state['action_history'].append(action)

def get_last_action(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return last action from action history.
    
    Args:
        state: State dictionary to update
    """
    if 'action_history' not in state:
        state['action_history'] = []
        return None
    
    if state['action_history'] == []:
        return None
    
    return state['action_history'][-1]

def pop_last_action(state: Dict[str, Any]) -> None:
    """
    Deletes last action from action history.
    
    Args:
        state: State dictionary to update
    """
    if 'action_history' not in state:
        state['action_history'] = []
        return None
    
    if state['action_history'] == []:
        return None
    
    state['action_history'].pop(-1)
    
def clear_state(year_dir: str) -> None:
    """
    Clear/delete the state file.
    
    Args:
        year_dir: The directory being sorted
    """
    state_file = _get_state_file_path(year_dir)
    
    if os.path.exists(state_file):
        try:
            os.remove(state_file)
        except IOError as e:
            print(f"Warning: Could not delete state file: {e}")

