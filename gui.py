import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from main import run_extraction

# Appearance settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DataArkGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DataArk - Personal Backup System")
        self.geometry("600x450")

        # UI Elements
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # Title
        self.label_title = ctk.CTkLabel(self, text="DataArk", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.label_subtitle = ctk.CTkLabel(self, text="Select information to extract and destination", font=ctk.CTkFont(size=14))
        self.label_subtitle.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Checkboxes frame
        self.checkbox_frame = ctk.CTkFrame(self)
        self.checkbox_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.checkbox_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.check_browsers = ctk.CTkCheckBox(self.checkbox_frame, text="Passwords")
        self.check_browsers.select()
        self.check_browsers.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        self.check_wifi = ctk.CTkCheckBox(self.checkbox_frame, text="WiFi Profiles")
        self.check_wifi.select()
        self.check_wifi.grid(row=0, column=1, padx=20, pady=10, sticky="w")

        self.check_system = ctk.CTkCheckBox(self.checkbox_frame, text="System & Hosts")
        self.check_system.select()
        self.check_system.grid(row=0, column=2, padx=20, pady=10, sticky="w")

        self.check_developer = ctk.CTkCheckBox(self.checkbox_frame, text="Dev (SSH, Git)")
        self.check_developer.select()
        self.check_developer.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.check_bookmarks = ctk.CTkCheckBox(self.checkbox_frame, text="Bookmarks")
        self.check_bookmarks.select()
        self.check_bookmarks.grid(row=1, column=1, padx=20, pady=10, sticky="w")

        self.check_vscode = ctk.CTkCheckBox(self.checkbox_frame, text="VS Code Ext.")
        self.check_vscode.select()
        self.check_vscode.grid(row=1, column=2, padx=20, pady=10, sticky="w")

        # Destination path
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)

        self.entry_path = ctk.CTkEntry(self.path_frame, placeholder_text="Select destination folder...")
        self.entry_path.insert(0, os.getcwd())
        self.entry_path.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")

        self.btn_browse = ctk.CTkButton(self.path_frame, text="Browse", width=80, command=self.browse_folder)
        self.btn_browse.grid(row=0, column=1, padx=(5, 10), pady=10)

        # Progress
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)

        self.label_status = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=12))
        self.label_status.grid(row=5, column=0, padx=20, pady=0)

        # Action buttons frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.btn_start = ctk.CTkButton(self.btn_frame, text="START EXTRACTION", font=ctk.CTkFont(size=16, weight="bold"), 
                                      height=45, command=self.start_extraction_thread)
        self.btn_start.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_export_ui = ctk.CTkButton(self.btn_frame, text="OPEN EXPORT PAGES (v20)", font=ctk.CTkFont(size=14), 
                                          height=45, fg_color="gray30", hover_color="gray40", command=self.open_export_pages)
        self.btn_export_ui.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def open_export_pages(self):
        import webbrowser
        urls = [
            "chrome://password-manager/settings",
            "edge://password-manager/settings",
            "brave://password-manager/settings",
            "opera://settings/passwords",
            "comet://password-manager/settings", # Comet
            "about:logins" # Firefox
        ]
        messagebox.showinfo("Export Assistant", "Opening password settings for all browsers.\n\nIMPORTANT: If you have multiple profiles (e.g., Lavoro, Private), make sure to switch profile in each browser window and click 'Export' for each one.")
        for url in urls:
            webbrowser.open(url)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, folder)

    def update_progress(self, status, percentage):
        self.label_status.configure(text=status)
        self.progress_bar.set(percentage)
        self.update_idletasks()

    def start_extraction_thread(self):
        options = {
            "browsers": self.check_browsers.get(),
            "wifi": self.check_wifi.get(),
            "system": self.check_system.get(),
            "developer": self.check_developer.get(),
            "bookmarks": self.check_bookmarks.get(),
            "vscode": self.check_vscode.get()
        }
        
        if not any(options.values()):
            messagebox.showwarning("Warning", "Please select at least one option.")
            return

        dest_path = self.entry_path.get()
        if not os.path.exists(dest_path):
            messagebox.showerror("Error", "Selected destination folder does not exist.")
            return

        self.btn_start.configure(state="disabled", text="RUNNING...")
        self.progress_bar.set(0)
        
        # Run in thread to not block GUI
        thread = threading.Thread(target=self.run_process, args=(options, dest_path))
        thread.start()

    def run_process(self, options, dest_path):
        try:
            export_dir = run_extraction(options, dest_path, self.update_progress)
            messagebox.showinfo("Success", f"Extraction completed successfully!\n\nFolder: {export_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.btn_start.configure(state="normal", text="START EXTRACTION")
            self.update_progress("Ready", 0)

if __name__ == "__main__":
    app = DataArkGUI()
    app.mainloop()
