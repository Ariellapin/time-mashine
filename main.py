import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import database
import file_manager

import threading

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

class HistorySaverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HistorySaver")
        self.root.geometry("800x600")

        # Initialize Database
        database.init_db()

        # UI Components
        self.create_widgets()
        
        # Load Data
        self.refresh_file_list()

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

        # File List (Treeview)
        columns = ("id", "original_path", "status", "backup_time")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("original_path", text="Original Path")
        self.tree.heading("status", text="Status")
        self.tree.heading("backup_time", text="Last Backup")

        self.tree.column("id", width=50)
        self.tree.column("original_path", width=400)
        self.tree.column("status", width=100)
        self.tree.column("backup_time", width=150)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def protect_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            try:
                file_manager.protect_file(filepath)
                self.refresh_file_list()
                messagebox.showinfo("Success", f"File protected: {filepath}")
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
                    
                    file_manager.protect_file(filepath)
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
            messagebox.showinfo("Cancelled", f"Operation cancelled. Protected {count} files.")
        else:
            messagebox.showinfo("Success", f"Protected {count} files in {folder_path}")

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
    app = HistorySaverApp(root)
    root.mainloop()
