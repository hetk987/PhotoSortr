# Photo Sortr 📸

A powerful command-line tool for organizing photos into event folders with intelligent duplicate detection.

## Features

✨ **Interactive Sorting** - Browse photos one-by-one and assign them to event folders with simple keystrokes

🔍 **Duplicate Detection** - Two-level duplicate detection using SHA256 (exact) and perceptual hashing (similar images)

💾 **Resume Sessions** - Progress is automatically saved, allowing you to resume sorting anytime

🗂️ **Dynamic Folders** - Create new event folders on-the-fly as you sort

📊 **Session Statistics** - Detailed logging and summaries of your sorting sessions

🖥️ **Cross-Platform** - Works on macOS, Windows, and Linux

## Installation

### Requirements

-   Python 3.8 or higher
-   macOS, Windows, or Linux

### Setup

1. Clone or download this repository

2. Install dependencies:

```bash
pip install -r requirements.txt
```

The tool requires two libraries for perceptual duplicate detection:

-   `Pillow` - Image processing
-   `imagehash` - Perceptual hashing algorithms

**Note:** The tool will still work without these libraries, but only exact duplicate detection (SHA256) will be available.

## Usage

### Basic Usage

```bash
python main.py /path/to/photos
```

### Advanced Options

```bash
# Don't auto-move duplicates (prompt instead)
python main.py --no-auto-duplicates /path/to/photos

# Adjust duplicate detection sensitivity (default: 5)
# Lower values = stricter matching
python main.py --threshold 3 /path/to/photos

# Show version
python main.py --version

# Show help
python main.py --help
```

### Keyboard Controls

During sorting, use these keys:

| Key   | Action                                          |
| ----- | ----------------------------------------------- |
| `1-9` | Move photo to corresponding event folder        |
| `N`   | Create a new event folder                       |
| `S`   | Skip this photo (leave in place)                |
| `D`   | Delete this photo (with confirmation)           |
| `U`   | Mark as duplicate and move to Duplicates folder |
| `Q`   | Quit and save progress                          |

## How It Works

### Sorting Workflow

1. **Scan** - The tool scans your directory for all image files
2. **Resume** - Loads any previous session progress
3. **Display** - Opens each photo in your system's default viewer
4. **Choose** - You choose where to move the photo
5. **Track** - Progress and actions are logged automatically

### Duplicate Detection

The tool uses a two-level approach:

#### Level 1: SHA256 Hash (Fast)

-   Computes file hash for exact duplicate detection
-   Catches identical files, even with different names
-   Very fast (~300MB/s)

#### Level 2: Perceptual Hash (Accurate)

-   Uses image content analysis to find similar images
-   Detects duplicates even after resizing, cropping, or minor edits
-   Uses hamming distance to measure similarity
-   Configurable threshold (default: 5)

### State Management

All progress is saved in a `.photosorter` directory within your photo folder:

```
/your-photos/
  .photosorter/
    state.json          # Session progress
    cache/
      image_hashes.json # Duplicate detection cache
    sorter.log          # Detailed activity log
```

This allows you to:

-   Resume sorting exactly where you left off
-   Review what was sorted via logs
-   Maintain duplicate detection across sessions

## Architecture & File Interactions

Understanding how the different modules interact will help you add features and fix bugs efficiently.

### System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          main.py                                 │
│  • Parse command-line arguments                                  │
│  • Validate directory                                            │
│  • Create PhotoSorter instance                                   │
│  • Handle top-level errors                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                       sorter.py                                  │
│                   (Main Orchestrator)                            │
│  • PhotoSorter class - coordinates all operations                │
│  • Manages session state and statistics                          │
│  • Implements main sorting loop                                  │
│  • Setup logging infrastructure                                  │
└─────┬────────┬─────────┬──────────┬──────────┬──────────┬───────┘
      │        │         │          │          │          │
      ↓        ↓         ↓          ↓          ↓          ↓
┌───────────┐ ┌─────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────┐ ┌─────────────┐
│directory_ │ │cli_ui.py│ │os_viewer.py│ │folder_   │ │state_manager │ │duplicate_   │
│scanner.py │ │         │ │            │ │manager.py│ │.py           │ │detector.py  │
│           │ │         │ │            │ │          │ │              │ │             │
│• Scan for │ │• Display│ │• Open      │ │• List    │ │• Load/save   │ │• Compute    │
│  images   │ │  menu   │ │  images    │ │  folders │ │  session     │ │  SHA256     │
│• Filter   │ │• Get    │ │• Close     │ │• Create  │ │  state       │ │  hashes     │
│  by ext   │ │  key-   │ │  viewers   │ │  folders │ │• Track       │ │• Compute    │
│• Skip     │ │  press  │ │• Platform- │ │• Move    │ │  progress    │ │  perceptual │
│  hidden   │ │• Prompt │ │  specific  │ │  photos  │ │• Manage      │ │  hashes     │
│  files    │ │  user   │ │  handling  │ │• Handle  │ │  skipped     │ │• Check for  │
│• Recurse  │ │• Show   │ │  (macOS,   │ │  name    │ │  files       │ │  duplicates │
│  dirs     │ │  summary│ │  Windows,  │ │  conflicts│ │              │ │• HashDatabase│
│           │ │         │ │  Linux)    │ │          │ │              │ │  class      │
└───────────┘ └─────────┘ └────────────┘ └──────────┘ └──────────────┘ └─────────────┘
```

### Detailed Module Interactions

#### 1. **Initialization Phase** (main.py → sorter.py)

```
main.py
  ├─ Parse CLI arguments (directory, threshold, auto-duplicates)
  ├─ Validate directory exists
  └─ Create PhotoSorter instance
       └─ sorter.PhotoSorter.__init__()
            ├─ Initialize session variables
            ├─ Setup logging (creates .photosorter/sorter.log)
            └─ Store configuration
```

#### 2. **Loading Phase** (sorter.py coordinates)

```
sorter.PhotoSorter.run()
  ├─ load_images() → directory_scanner.scan_images()
  │    └─ Returns list of all image paths
  ├─ load_state() → state_manager.load_state()
  │    └─ Returns dict with last_index, counts, skipped_files
  └─ load_hash_database() → duplicate_detector.HashDatabase()
       └─ Loads cached hashes from .photosorter/cache/image_hashes.json
```

#### 3. **Main Sorting Loop** (sorter.py._sorting_loop)

```
For each photo:
  ├─ Check if file exists
  │
  ├─ duplicate_detector.is_duplicate()
  │    ├─ compute_file_hash() - SHA256
  │    ├─ hash_db.get_by_sha256() - Check exact match
  │    └─ If not found:
  │         ├─ compute_perceptual_hash() - phash
  │         └─ hash_db.find_similar_by_phash() - Check similarity
  │
  ├─ If duplicate found:
  │    └─ _handle_duplicate() → folder_manager.move_photo()
  │
  ├─ os_viewer.open_image()
  │    └─ Platform-specific viewer (Preview/Photos/xdg-open)
  │
  ├─ folder_manager.list_event_folders()
  │    └─ Get available destination folders
  │
  ├─ cli_ui.show_menu()
  │    └─ Display options to user
  │
  ├─ cli_ui.get_keypress()
  │    └─ Wait for user input
  │
  ├─ _handle_choice()
  │    ├─ If 1-9: folder_manager.move_photo()
  │    ├─ If N: cli_ui.prompt_new_folder_name()
  │    │         └─ folder_manager.create_event_folder()
  │    │         └─ folder_manager.move_photo()
  │    ├─ If S: Log skip
  │    ├─ If D: cli_ui.prompt_confirmation()
  │    │         └─ Delete file
  │    ├─ If U: _handle_duplicate()
  │    └─ If Q: Exit loop
  │
  ├─ os_viewer.close_image()
  │    └─ Close the viewer window
  │
  ├─ If moved: duplicate_detector.add_to_hash_db()
  │    └─ hash_db.save() - Update cache
  │
  └─ save_state() → state_manager.save_state()
       └─ Write progress to disk
```

#### 4. **Cleanup Phase** (sorter.py)

```
Finally:
  ├─ _print_summary() → cli_ui.print_summary()
  │    └─ Display counts to user
  └─ _log_summary()
       └─ Write session summary to log file
```

### Module Responsibilities

| Module | Purpose | Key Classes/Functions | Dependencies |
|--------|---------|----------------------|--------------|
| `main.py` | Entry point | `main()` | `sorter` |
| `sorter.py` | Orchestration | `PhotoSorter`, `setup_logging()` | All other modules |
| `directory_scanner.py` | File discovery | `scan_images()`, `is_image()` | None (stdlib only) |
| `os_viewer.py` | Image viewing | `open_image()`, `close_image()` | None (stdlib only) |
| `folder_manager.py` | File operations | `list_event_folders()`, `create_event_folder()`, `move_photo()` | None (stdlib only) |
| `state_manager.py` | Progress persistence | `load_state()`, `save_state()` | None (stdlib only) |
| `duplicate_detector.py` | Duplicate detection | `HashDatabase`, `is_duplicate()`, `compute_file_hash()`, `compute_perceptual_hash()` | `PIL`, `imagehash` (optional) |
| `cli_ui.py` | User interface | `show_menu()`, `get_keypress()`, `prompt_*()` | None (stdlib only) |

### Data Flow

#### Session State (`state.json`)

```python
{
  "last_index": 42,           # Current position in image list
  "sorted_count": 35,         # Photos moved to folders
  "skipped_count": 5,         # Photos skipped
  "deleted_count": 2,         # Photos deleted
  "duplicate_count": 3,       # Duplicates found
  "skipped_files": [...]      # List of skipped file paths
}
```

Flows: `state_manager` ← → `sorter` (read/write throughout session)

#### Hash Database (`image_hashes.json`)

```python
{
  "Event1/photo1.jpg": {
    "sha256": "abc123...",    # Exact duplicate detection
    "phash": "f8f8c3c3..."    # Similar image detection
  },
  ...
}
```

Flows: `duplicate_detector.HashDatabase` ← → `sorter` (checked for each photo)

### Where to Add Features

| Feature Type | Primary File(s) | Secondary Files |
|-------------|-----------------|-----------------|
| **New duplicate detection algorithm** | `duplicate_detector.py` | Update `sorter.py` to use it |
| **Different file formats** | `directory_scanner.py` | Add to `SUPPORTED_EXTENSIONS` |
| **EXIF-based sorting** | Create `exif_reader.py` | Call from `sorter.py` before showing menu |
| **Undo functionality** | `state_manager.py`, `sorter.py` | Track moves in state, add reverse operations |
| **Batch operations** | `sorter.py`, `cli_ui.py` | Add multi-select mode in UI |
| **GUI interface** | Create `gui_app.py` | Use `sorter.PhotoSorter` as backend |
| **Cloud sync** | Create `cloud_sync.py` | Integrate with `folder_manager.py` |
| **Different viewer** | `os_viewer.py` | Modify `open_image()` function |
| **Keyboard shortcuts** | `cli_ui.py` | Add to `get_keypress()` handling |
| **Statistics/reports** | `sorter.py` | Add tracking, create report in `_print_summary()` |

### Where to Fix Bugs

| Bug Type | Files to Check | What to Look For |
|----------|---------------|------------------|
| **Photos not found** | `directory_scanner.py` | Extension filtering, path handling |
| **Viewer not opening** | `os_viewer.py` | Platform detection, subprocess calls |
| **Wrong folder moved to** | `folder_manager.py`, `sorter.py` | Index mapping, folder list order |
| **Lost progress** | `state_manager.py` | JSON serialization, file permissions |
| **False duplicate matches** | `duplicate_detector.py` | Threshold values, hash comparison logic |
| **UI display issues** | `cli_ui.py` | Terminal codes, menu formatting |
| **Files not moving** | `folder_manager.py` | Permission checks, shutil.move errors |
| **Logging not working** | `sorter.py` (`setup_logging`) | File handler setup, directory permissions |

### Adding a New Module

If you need to add a new module (e.g., `exif_reader.py`):

1. **Create the module** with clear, focused functionality
2. **Import in sorter.py** at the top
3. **Call from appropriate place** in sorting loop or initialization
4. **Update state if needed** to persist new data
5. **Add UI elements** in `cli_ui.py` if user interaction needed
6. **Update logging** to track new operations
7. **Document in README** (this section!)

### Testing Strategy

-   **Unit testing**: Each module can be tested independently (they have minimal dependencies)
-   **Integration testing**: Test `sorter.py` with mock data
-   **Manual testing**: Use a small test directory with known duplicates

## Examples

### Sort wedding photos

```bash
python main.py ~/Pictures/Wedding_2024
```

### Sort with strict duplicate detection

```bash
python main.py --threshold 2 ~/Pictures/Vacation
```

### Manual duplicate review

```bash
python main.py --no-auto-duplicates ~/Photos
```

## File Organization

After sorting, your photos will be organized like this:

```
/your-photos/
  Event_Folder_1/
    IMG_001.jpg
    IMG_002.jpg
  Event_Folder_2/
    IMG_010.jpg
  Duplicates/
    IMG_003.jpg
  .photosorter/
    state.json
    cache/
    sorter.log
  IMG_020.jpg  # Unsorted/skipped photos remain
```

## Supported Image Formats

-   JPEG/JPG
-   PNG
-   HEIC (iOS photos)
-   TIFF/TIF
-   GIF
-   BMP
-   WebP
-   RAW formats (CR2, NEF, ARW, DNG)

## Logging

Detailed logs are saved to `.photosorter/sorter.log` containing:

-   All file moves and folder creations
-   Duplicate detections with match types
-   Deletions (with full paths for recovery)
-   Errors and warnings
-   Session summaries with timestamps

## Tips

1. **Start Small** - Try sorting a small folder first to get familiar with the workflow

2. **Review Duplicates** - Use `--no-auto-duplicates` if you want to manually review each duplicate

3. **Adjust Threshold** - If too many false positives, increase the threshold; if missing duplicates, decrease it

4. **Check Logs** - Review `.photosorter/sorter.log` to see exactly what was done

5. **Backup First** - Always have a backup of important photos before sorting

## Troubleshooting

### Images won't open

-   Ensure your system has a default image viewer configured
-   Check file permissions on the photo directory

### Perceptual hashing not working

-   Install required libraries: `pip install pillow imagehash`
-   The tool will notify you if libraries are missing

### Can't resume session

-   Check if `.photosorter/state.json` exists
-   If corrupted, delete it to start fresh (progress will be lost)

### Permission errors

-   Ensure you have read/write permissions on the photo directory
-   On macOS/Linux, avoid system directories without proper permissions

## Development

### Project Structure

```
photosorter/
  main.py                 # Entry point
  sorter.py              # Main orchestration
  directory_scanner.py   # File discovery
  os_viewer.py           # Image viewer
  folder_manager.py      # Folder operations
  state_manager.py       # Progress persistence
  duplicate_detector.py  # Duplicate detection
  cli_ui.py             # User interface
```

### Running Tests

The tool is designed for interactive use. Test with a small sample directory:

```bash
mkdir test_photos
# Add some test images
python main.py test_photos
```

## License

This project is open source and available for personal and commercial use.

## Contributing

Contributions are welcome! Areas for improvement:

-   EXIF-based auto-grouping
-   Batch operations
-   Undo functionality
-   Cloud sync integration
-   GUI interface

## Version History

### 1.0.0 (Current)

-   Initial release
-   Interactive photo sorting
-   Duplicate detection (SHA256 + perceptual)
-   State persistence
-   Cross-platform support
-   Comprehensive logging

## Support

For issues, questions, or suggestions, please open an issue on the project repository.

---

**Happy Sorting! 📸✨**
