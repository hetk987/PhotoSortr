"""
Duplicate Detector Module
Handles duplicate detection using SHA256 and perceptual hashing.
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional, Tuple

# Optional imports for perceptual hashing
try:
    from PIL import Image
    import imagehash
    PERCEPTUAL_HASH_AVAILABLE = True
except ImportError:
    PERCEPTUAL_HASH_AVAILABLE = False


CACHE_DIR_NAME = '.photosorter/cache'
HASH_DB_FILE_NAME = 'image_hashes.json'


class HashDatabase:
    """Manages the hash database for duplicate detection."""
    
    def __init__(self, root_dir: str):
        """
        Initialize the hash database.
        
        Args:
            root_dir: Root directory for storing the hash database
        """
        self.root_dir = root_dir
        self.cache_dir = os.path.join(root_dir, CACHE_DIR_NAME)
        self.db_file = os.path.join(self.cache_dir, HASH_DB_FILE_NAME)
        self.hashes: Dict[str, Dict[str, Any]] = {}
        self._ensure_cache_dir()
        self.load()
    
    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def load(self) -> None:
        """Load hash database from disk."""
        if not os.path.exists(self.db_file):
            self.hashes = {}
            return
        
        try:
            with open(self.db_file, 'r') as f:
                self.hashes = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load hash database: {e}")
            self.hashes = {}
    
    def save(self) -> None:
        """Save hash database to disk."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.hashes, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save hash database: {e}")
    
    def add_hash(self, filepath: str, sha256: str, phash: Optional[str] = None) -> None:
        """
        Add a hash entry to the database.
        
        Args:
            filepath: Path to the file
            sha256: SHA256 hash of the file
            phash: Perceptual hash (optional)
        """
        # Use relative path for portability
        rel_path = os.path.relpath(filepath, self.root_dir) if filepath.startswith(self.root_dir) else filepath
        
        self.hashes[rel_path] = {
            'sha256': sha256,
            'phash': phash
        }
    
    def get_by_sha256(self, sha256: str) -> Optional[str]:
        """
        Find a file by its SHA256 hash.
        
        Args:
            sha256: SHA256 hash to search for
            
        Returns:
            Filepath if found, None otherwise
        """
        for filepath, data in self.hashes.items():
            if data.get('sha256') == sha256:
                return filepath
        return None
    
    def find_similar_by_phash(self, phash: str, threshold: int = 5) -> Optional[Tuple[str, int]]:
        """
        Find a similar file by perceptual hash.
        
        Args:
            phash: Perceptual hash to compare
            threshold: Maximum hamming distance for a match
            
        Returns:
            Tuple of (filepath, distance) if found, None otherwise
        """
        if not PERCEPTUAL_HASH_AVAILABLE:
            return None
        
        try:
            search_hash = imagehash.hex_to_hash(phash)
        except (ValueError, AttributeError):
            return None
        
        best_match = None
        best_distance = threshold + 1
        
        for filepath, data in self.hashes.items():
            stored_phash = data.get('phash')
            if not stored_phash:
                continue
            
            try:
                stored_hash = imagehash.hex_to_hash(stored_phash)
                distance = search_hash - stored_hash
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = filepath
            except (ValueError, AttributeError):
                continue
        
        if best_match and best_distance <= threshold:
            return (best_match, best_distance)
        
        return None


def compute_file_hash(filepath: str) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Hexadecimal SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(filepath, 'rb') as f:
            # Read in chunks for memory efficiency
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Could not read file for hashing: {e}")


def compute_perceptual_hash(filepath: str) -> Optional[str]:
    """
    Compute perceptual hash of an image.
    
    Args:
        filepath: Path to the image file
        
    Returns:
        Hexadecimal perceptual hash string, or None if not available
    """
    if not PERCEPTUAL_HASH_AVAILABLE:
        return None
    
    try:
        image = Image.open(filepath)
        # Use phash (perceptual hash) - good balance of accuracy and speed
        phash = imagehash.phash(image)
        return str(phash)
    except Exception as e:
        print(f"Warning: Could not compute perceptual hash for {filepath}: {e}")
        return None


def is_duplicate(filepath: str, hash_db: HashDatabase, 
                threshold: int = 5) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if a file is a duplicate.
    
    Args:
        filepath: Path to the file to check
        hash_db: Hash database to check against
        threshold: Perceptual hash distance threshold
        
    Returns:
        Tuple of (is_duplicate, duplicate_type, original_file)
        - is_duplicate: True if duplicate found
        - duplicate_type: 'exact' or 'similar'
        - original_file: Path to the original file if duplicate
    """
    # Compute SHA256 first (fast)
    try:
        sha256 = compute_file_hash(filepath)
    except IOError:
        return (False, None, None)
    
    # Check for exact duplicate
    original = hash_db.get_by_sha256(sha256)
    if original:
        return (True, 'exact', original)
    
    # Check for perceptual duplicate (slower)
    if PERCEPTUAL_HASH_AVAILABLE:
        phash = compute_perceptual_hash(filepath)
        if phash:
            similar_match = hash_db.find_similar_by_phash(phash, threshold)
            if similar_match:
                original_file, distance = similar_match
                return (True, 'similar', original_file)
    
    return (False, None, None)


def add_to_hash_db(filepath: str, hash_db: HashDatabase) -> None:
    """
    Add a file to the hash database.
    
    Args:
        filepath: Path to the file
        hash_db: Hash database to add to
    """
    try:
        sha256 = compute_file_hash(filepath)
        phash = compute_perceptual_hash(filepath) if PERCEPTUAL_HASH_AVAILABLE else None
        hash_db.add_hash(filepath, sha256, phash)
        hash_db.save()
    except Exception as e:
        print(f"Warning: Could not add file to hash database: {e}")

