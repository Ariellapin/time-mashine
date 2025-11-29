import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import database
import file_manager
import threading
import sys
import pystray
from PIL import Image, ImageDraw
import winreg

# --- Constants ---
APP_NAME = "FileGuardian"
STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, title="Processing"):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.label = ttk.Label(self, text="Preparing...")
        self.label.pack(pady=10)
        
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=250, mode='determinate')
        self.progress.pack(pady=10)
        
        self.cancel_btn = ttk.Button(self, text="Cancel", command=self.cancel)
        self.cancel_btn.pack(pady=10)
        
        self.cancelled = False
        
        # Center the dialog
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def update_progress(self, value, maximum, message):
        self.progress['maximum'] = maximum
        self.progress['value'] = value
        self.label.config(text=message)

    def cancel(self):
        self.cancelled = True
        self.label.config(text="Cancelling...")
        self.cancel_btn.config(state=tk.DISABLED)

    def close(self):
        self.destroy()

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("400x300")
        self.parent = parent
        
        # Run on Startup
        self.startup_var = tk.BooleanVar(value=self.check_startup())
        chk_startup = ttk.Checkbutton(self, text="Run on Startup", variable=self.startup_var, command=self.toggle_startup)
        chk_startup.pack(pady=10, padx=10, anchor=tk.W)
        
        # Monitored Folders
        lbl_folders = ttk.Label(self, text="Monitored Folders:")
        lbl_folders.pack(pady=(10, 0), padx=10, anchor=tk.W)
        
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        btn_add = ttk.Button(btn_frame, text="Add Folder", command=self.add_folder)
        btn_add.pack(side=tk.LEFT, padx=5)
        
        btn_remove = ttk.Button(btn_frame, text="Remove Folder", command=self.remove_folder)
        btn_remove.pack(side=tk.LEFT, padx=5)
        
        self.load_folders()

    def check_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def toggle_startup(self):
        if self.startup_var.get():
            # Add to registry
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
                exe_path = sys.executable
                # If running as script, use python + script path. If frozen (exe), use executable.
                if getattr(sys, 'frozen', False):
                     cmd = f'"{sys.executable}"'
                else:
                     # Assuming running main.py
                     cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
                
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                winreg.CloseKey(key)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to enable startup: {e}")
                self.startup_var.set(False)
        else:
            # Remove from registry
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, APP_NAME)
                winreg.CloseKey(key)
            except WindowsError:
                pass # Key doesn't exist

    def load_folders(self):
        self.listbox.delete(0, tk.END)
        folders = database.get_monitored_folders()
        for f in folders:
            self.listbox.insert(tk.END, f)

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            database.add_monitored_folder(folder)
            self.load_folders()

    def remove_folder(self):
        selection = self.listbox.curselection()
        if selection:
            folder = self.listbox.get(selection[0])
            database.remove_monitored_folder(folder)
            self.load_folders()

class FileGuardianApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("800x600")
        
        # Handle Close -> Minimize to Tray
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Initialize Database
        database.init_db()

        # UI Components
        self.create_widgets()
        
        # Load Data
        self.refresh_file_list()
        
        # System Tray
        self.setup_tray()
        
        # Auto-Scan on Startup
        self.run_auto_scan()

    def create_widgets(self):
        # Toolbar
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_protect = ttk.Button(toolbar, text="Protect File", command=self.protect_file)
        btn_protect.pack(side=tk.LEFT, padx=5)

        btn_protect_folder = ttk.Button(toolbar, text="Protect Folder", command=self.protect_folder)
        btn_protect_folder.pack(side=tk.LEFT, padx=5)

        btn_restore = ttk.Button(toolbar, text="Restore File", command=self.restore_file)
        btn_restore.pack(side=tk.LEFT, padx=5)

        btn_remove = ttk.Button(toolbar, text="Remove Protection", command=self.remove_protection)
        btn_remove.pack(side=tk.LEFT, padx=5)

        btn_refresh = ttk.Button(toolbar, text="Refresh Status", command=self.refresh_file_list)
        btn_refresh.pack(side=tk.LEFT, padx=5)
        
        # Spacer
        ttk.Label(toolbar, text="").pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        btn_settings = ttk.Button(toolbar, text="Settings", command=self.open_settings)
        btn_settings.pack(side=tk.RIGHT, padx=5)

        # File List (Treeview)
        columns = ("id", "original_path", "status", "backup_time")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("original_path", text="Original Path")
        self.tree.heading("status", text="Status")
        self.tree.heading("backup_time", text="Protected At")

        self.tree.column("id", width=50)
        self.tree.column("original_path", width=400)
        self.tree.column("status", width=100)
        self.tree.column("backup_time", width=150)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_icon(self):
        # Create a simple icon programmatically since generation failed
        image = Image.new('RGB', (64, 64), color = (73, 109, 137))
        d = ImageDraw.Draw(image)
        d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
        return image

    def setup_tray(self):
        image = self.create_icon()
        menu = pystray.Menu(
            pystray.MenuItem("Open FileGuardian", self.show_window),
            pystray.MenuItem("Exit", self.quit_app)
        )
        self.icon = pystray.Icon("FileGuardian", image, "FileGuardian", menu)
        
        # Run tray icon in separate thread
        threading.Thread(target=self.icon.run, daemon=True).start()

    def hide_window(self):
        self.root.withdraw()
        
    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        self.root.lift()

    def quit_app(self, icon=None, item=None):
        self.icon.stop()
        self.root.quit()

    def open_settings(self):
        SettingsDialog(self.root)

    def run_auto_scan(self):
        # Run in background thread
        def scan():
            folders = database.get_monitored_folders()
            total_new = 0
            for folder in folders:
                if os.path.exists(folder):
                    total_new += file_manager.scan_and_protect(folder)
            
            if total_new > 0:
                self.root.after(0, lambda: messagebox.showinfo("Auto-Scan", f"Protected {total_new} new files."))
                self.root.after(0, self.refresh_file_list)

        threading.Thread(target=scan, daemon=True).start()

    def protect_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            try:
                res = file_manager.protect_file(filepath)
                if res:
                    self.refresh_file_list()
                    messagebox.showinfo("Success", f"File protected: {filepath}")
                else:
                    messagebox.showinfo("Info", "File is already protected.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def protect_folder(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return

        dialog = ProgressDialog(self.root, title="Protecting Folder")
        
        def run_protection():
            files_to_protect = []
            # 1. Collect files
            for root, dirs, files in os.walk(folder_path):
                if dialog.cancelled:
                    break
                for file in files:
                    files_to_protect.append(os.path.join(root, file))
            
            total_files = len(files_to_protect)
            processed = 0
            success_count = 0
            
            # 2. Protect files
            for filepath in files_to_protect:
                if dialog.cancelled:
                    break
                
                try:
                    # Update UI from main thread
                    self.root.after(0, dialog.update_progress, processed, total_files, f"Protecting {processed}/{total_files}")
                    
                    if file_manager.protect_file(filepath):
                        success_count += 1
                except Exception as e:
                    print(f"Failed to protect {filepath}: {e}")
                
                processed += 1
            
            # Close dialog and show result
            self.root.after(0, dialog.close)
            self.root.after(0, lambda: self.finish_protection(success_count, folder_path, dialog.cancelled))

        threading.Thread(target=run_protection, daemon=True).start()

    def finish_protection(self, count, folder_path, cancelled):
        self.refresh_file_list()
        if cancelled:
            messagebox.showinfo("Cancelled", f"Operation cancelled. Protected {count} new files.")
        else:
            messagebox.showinfo("Success", f"Protected {count} new files in {folder_path}")

    def restore_file(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a file to restore.")
            return

        item = self.tree.item(selected_item)
        file_id = item['values'][0]
        
        record = database.get_file_by_id(file_id)
        if record:
            original_path = record[1]
            backup_path = record[2]
            
            try:
                file_manager.restore_file(original_path, backup_path)
                self.refresh_file_list()
                messagebox.showinfo("Success", f"File restored: {original_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def remove_protection(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a file to remove.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to stop protecting this file?"):
            item = self.tree.item(selected_item)
            file_id = item['values'][0]
            database.remove_file(file_id)
            self.refresh_file_list()

    def refresh_file_list(self):
        # Clear current list
        for item in self.tree.get_children():
            self.tree.delete(item)

        files = database.get_all_files()
        for f in files:
            file_id, original_path, backup_path, timestamp = f
            
            # Check status
            if file_manager.check_file_status(original_path):
                status = "Protected"
            else:
                status = "MISSING"

            self.tree.insert("", tk.END, values=(file_id, original_path, status, timestamp))

if __name__ == "__main__":
    root = tk.Tk()
    app = FileGuardianApp(root)
    root.mainloop()
