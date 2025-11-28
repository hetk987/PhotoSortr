"""
OS Viewer Module
Opens images in the default OS viewer in a cross-platform way.
"""

import os
import platform
import subprocess
import time
from typing import Optional


# Global variable to track the last opened image process/path
_last_process: Optional[subprocess.Popen] = None
_last_image_path: Optional[str] = None


def open_image(path: str) -> None:
    """
    Open an image file in the default OS viewer.
    Closes any previously opened image first.
    
    Args:
        path: Absolute path to the image file
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
        RuntimeError: If unable to open the image
    """
    global _last_process, _last_image_path
    
    # Close previous image if any
    close_image()
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image file not found: {path}")
    
    system = platform.system()
    
    try:
        if system == 'Darwin':  # macOS
            # Open with Preview using -a flag for consistency
            # -g flag opens in background without stealing focus
            proc = subprocess.Popen(['open', '-g', '-a', 'Preview', path], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
            _last_process = proc
            _last_image_path = path
            # Give Preview a moment to open
            time.sleep(0.3)
            
        elif system == 'Windows':
            os.startfile(path)
            _last_image_path = path
            
        elif system == 'Linux':
            proc = subprocess.Popen(['xdg-open', path],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
            _last_process = proc
            _last_image_path = path
        else:
            raise RuntimeError(f"Unsupported operating system: {system}")
    except Exception as e:
        raise RuntimeError(f"Failed to open image: {e}")


def close_image() -> None:
    """
    Close the currently open image viewer window.
    Uses platform-specific methods to close the preview.
    """
    global _last_process, _last_image_path
    
    if _last_image_path is None:
        return
    
    system = platform.system()
    
    try:
        if system == 'Darwin':  # macOS
            # Use AppleScript to close the frontmost Preview window
            applescript = '''
                tell application "Preview"
                    if (count of windows) > 0 then
                        close front window
                    end if
                end tell
            '''
            subprocess.run(['osascript', '-e', applescript],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         timeout=2)
            
        elif system == 'Windows':
            # On Windows, we can try to use taskkill to close the default viewer
            # This is less precise but should work for most cases
            try:
                # Try to close Windows Photo Viewer or Photos app
                subprocess.run(['taskkill', '/F', '/IM', 'Microsoft.Photos.exe'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             timeout=2)
            except:
                pass
                
        elif system == 'Linux':
            # On Linux, terminate the process if we have it
            if _last_process and _last_process.poll() is None:
                _last_process.terminate()
                try:
                    _last_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    _last_process.kill()
    except Exception:
        # Silently fail if we can't close - not critical
        pass
    finally:
        _last_process = None
        _last_image_path = None

