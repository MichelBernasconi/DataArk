import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from main import run_extraction
from PIL import Image
import ctypes

# Set Taskbar Icon for Windows
try:
    myappid = 'michelbernasconi.dataark.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

class DataArkGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DataArk - Personal Backup System")
        self.geometry("700x650")
        
        # Paths
        self.base_path = os.path.dirname(__file__)
        self.logo_path = os.path.join(self.base_path, "assets", "logo.png")

        # Set Appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Set Window Icon (Consistently)
        try:
            if os.path.exists(self.logo_path):
                img = Image.open(self.logo_path)
                # Generate ICO for Windows title bar if not exists
                self.ico_path = os.path.join(self.base_path, "assets", "logo.ico")
                if not os.path.exists(self.ico_path):
                    img.save(self.ico_path, format='ICO', sizes=[(32, 32), (16, 16)])
                
                # Use iconbitmap for the title bar (Windows native)
                self.after(200, lambda: self.iconbitmap(self.ico_path))
        except Exception as e:
            print(f"Icon error: {e}")

        # UI Elements
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=(30, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Logo
        try:
            if os.path.exists(self.logo_path):
                logo_img = ctk.CTkImage(light_image=Image.open(self.logo_path), 
                                       dark_image=Image.open(self.logo_path), 
                                       size=(70, 70))
                self.logo_label = ctk.CTkLabel(self.header_frame, image=logo_img, text="")
                self.logo_label.grid(row=0, column=0, padx=(0, 20))
        except:
            pass

        # Title and Subtitle
        self.title_text_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_text_frame.grid(row=0, column=1, sticky="w")
        
        self.label_title = ctk.CTkLabel(self.title_text_frame, text="DataArk", font=ctk.CTkFont(size=36, weight="bold"))
        self.label_title.grid(row=0, column=0, sticky="w")
        
        self.label_subtitle = ctk.CTkLabel(self.title_text_frame, text="The ultimate system backup suite for developers", 
                                          font=ctk.CTkFont(size=14), text_color="#5B9BD5")
        self.label_subtitle.grid(row=1, column=0, sticky="w")

        # Checkboxes frame
        self.checkbox_frame = ctk.CTkFrame(self)
        self.checkbox_frame.grid(row=2, column=0, padx=25, pady=20, sticky="nsew")
        self.checkbox_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.section_label = ctk.CTkLabel(self.checkbox_frame, text="SELECT COMPONENTS", font=ctk.CTkFont(size=13, weight="bold"), text_color="gray")
        self.section_label.grid(row=0, column=0, columnspan=3, pady=(15, 10))

        self.check_browsers = ctk.CTkCheckBox(self.checkbox_frame, text="Passwords", font=ctk.CTkFont(size=13))
        self.check_browsers.select()
        self.check_browsers.grid(row=1, column=0, padx=25, pady=15, sticky="w")

        self.check_wifi = ctk.CTkCheckBox(self.checkbox_frame, text="WiFi Profiles", font=ctk.CTkFont(size=13))
        self.check_wifi.select()
        self.check_wifi.grid(row=1, column=1, padx=25, pady=15, sticky="w")

        self.check_system = ctk.CTkCheckBox(self.checkbox_frame, text="System & Hosts", font=ctk.CTkFont(size=13))
        self.check_system.select()
        self.check_system.grid(row=1, column=2, padx=25, pady=15, sticky="w")

        self.check_developer = ctk.CTkCheckBox(self.checkbox_frame, text="Dev (SSH, Git)", font=ctk.CTkFont(size=13))
        self.check_developer.select()
        self.check_developer.grid(row=2, column=0, padx=25, pady=15, sticky="w")

        self.check_bookmarks = ctk.CTkCheckBox(self.checkbox_frame, text="Bookmarks", font=ctk.CTkFont(size=13))
        self.check_bookmarks.select()
        self.check_bookmarks.grid(row=2, column=1, padx=25, pady=15, sticky="w")

        self.check_vscode = ctk.CTkCheckBox(self.checkbox_frame, text="VS Code Ext.", font=ctk.CTkFont(size=13))
        self.check_vscode.select()
        self.check_vscode.grid(row=2, column=2, padx=25, pady=15, sticky="w")

        self.check_tabs = ctk.CTkCheckBox(self.checkbox_frame, text="Open Tabs", font=ctk.CTkFont(size=13))
        self.check_tabs.select()
        self.check_tabs.grid(row=3, column=0, padx=25, pady=(0, 15), sticky="w")

        # Destination path
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.grid(row=3, column=0, padx=25, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)

        self.entry_path = ctk.CTkEntry(self.path_frame, height=35, placeholder_text="Select destination folder...")
        self.entry_path.insert(0, os.getcwd())
        self.entry_path.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="ew")

        self.btn_browse = ctk.CTkButton(self.path_frame, text="BROWSE", width=100, height=35, 
                                      font=ctk.CTkFont(weight="bold"), command=self.browse_folder)
        self.btn_browse.grid(row=0, column=1, padx=(0, 15), pady=15)

        # Progress & Status
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=4, column=0, padx=25, pady=(10, 0), sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=12)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)

        self.label_status = ctk.CTkLabel(self, text="System Ready", font=ctk.CTkFont(size=12))
        self.label_status.grid(row=5, column=0, padx=25, pady=(5, 20))

        # Action buttons frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=6, column=0, padx=25, pady=(0, 30), sticky="ew")
        self.btn_frame.grid_columnconfigure((0, 1), weight=1)

        self.btn_start = ctk.CTkButton(self.btn_frame, text="START EXTRACTION", font=ctk.CTkFont(size=15, weight="bold"), 
                                      height=55, fg_color="#1f538d", hover_color="#14375e", command=self.start_extraction_thread)
        self.btn_start.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.btn_export_ui = ctk.CTkButton(self.btn_frame, text="BROWSER EXPORT HELPER", font=ctk.CTkFont(size=14), 
                                          height=55, fg_color="#3d3d3d", hover_color="#4d4d4d", command=self.open_export_pages)
        self.btn_export_ui.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def open_export_pages(self):
        import webbrowser
        urls = [
            "chrome://password-manager/settings",
            "edge://password-manager/settings",
            "brave://password-manager/settings",
            "opera://settings/passwords",
            "comet://password-manager/settings",
            "about:logins"
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
            "vscode": self.check_vscode.get(),
            "tabs": self.check_tabs.get()
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
            self.update_progress("System Ready", 0)

if __name__ == "__main__":
    app = DataArkGUI()
    app.mainloop()
