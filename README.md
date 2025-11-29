# FileGuardian
(Formerly HistorySaver)

FileGuardian is a Windows application that protects your files from accidental deletion instantly and with near-zero storage cost.

## How It Works (The "Magic")

FileGuardian uses **NTFS Hard Links** to protect your files.
- **Instant Protection**: It creates a second reference to your file in a secure Vault.
- **Zero Storage Cost**: Since it's just a reference (pointer) to the same data on disk, it takes up almost no extra space.
- **Instant Restore**: If you delete the original file, the data is still safe in the Vault. You can restore it instantly.

> **Note**: Because Hard Links point to the *same data*, if you **modify** the content of the file, the protected version changes too. This tool protects against **deletion**, not unwanted edits.

> **Why does the Vault folder look so big?**
> Windows Explorer reports the full size of the file for *every* link. If you protect a 1GB file, Explorer will say the Vault is also 1GB. **Do not worry!** This is an illusion. Both files point to the same data, so you are using 1GB of disk space total, not 2GB. You can verify this by checking your "Free Space" before and after protection.

## Features

- **Protect Individual Files**: Select specific files to safeguard.
- **Protect Folders**: Recursively protect all files within a directory.
- **Auto-Scan**: Configure folders to be automatically scanned and protected on startup.
- **System Tray**: Runs quietly in the background. Minimize to tray to keep your taskbar clean.
- **Run on Startup**: Option to automatically launch when Windows starts.
- **Restore**: One-click restoration of deleted files.

## Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:Ariellapin/time-mashine.git
   ```
2. Navigate to the directory:
   ```bash
   cd time-mashine
   ```
3. Install dependencies:
   ```bash
   pip install pystray Pillow
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. **Protect File**: Click the button and choose a file.
2. **Protect Folder**: Click the button and choose a folder.
3. **Settings**:
   - **Run on Startup**: Toggle to start app with Windows.
   - **Monitored Folders**: Add folders here. Every time the app starts, it will find new files in these folders and protect them automatically.
4. **Restore File**: If a file is deleted (Status: MISSING), select it and click "Restore File".

## Limitations

- **Same Drive Only**: You can only protect files that are on the same drive (partition) as the FileGuardian vault.
- **Modification**: Does not protect against file content changes, only deletion.
- **Physical Failure**: Does not protect against hard drive failure.

## Technologies

- Python 3
- Tkinter (GUI)
- SQLite (Database)
- Pystray (System Tray)
- WinReg (Windows Registry Integration)
