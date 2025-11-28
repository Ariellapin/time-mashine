# HistorySaver (Time Machine)

HistorySaver is a Windows application that allows you to protect your files by creating backups. If a protected file is deleted, you can easily restore it to its original location.

## Features

- **Protect Individual Files**: Select specific files to back up and monitor.
- **Protect Folders**: Recursively protect all files within a selected directory.
- **Progress Tracking**: Visual progress bar with cancellation support for large folder operations.
- **Restore**: One-click restoration of deleted files from the secure vault.
- **Status Monitoring**: View the status of all protected files (Protected vs. Missing).

## Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:Ariellapin/time-mashine.git
   ```
2. Navigate to the directory:
   ```bash
   cd time-mashine
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. **Protect File**: Click the button and choose a file to start tracking it.
2. **Protect Folder**: Click the button and choose a folder. All files inside will be backed up.
3. **Restore File**: If a file is deleted (Status: MISSING), select it and click "Restore File".
4. **Remove Protection**: Select a file and click "Remove Protection" to stop tracking it.

## Technologies

- Python 3
- Tkinter (GUI)
- SQLite (Database)
