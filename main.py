import os
import json
from datetime import datetime
from extractors.chromium import ChromiumExtractor, BROWSERS
from extractors.firefox import FirefoxExtractor
from extractors.system_info import SystemExtractor
from tabulate import tabulate

def run_extraction(options, output_path, progress_callback=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = os.path.join(output_path, f"dataark_export_{timestamp}")
    os.makedirs(export_dir, exist_ok=True)
    
    total_steps = sum(options.values())
    current_step = 0

    # 1. Browser Passwords
    if options.get("browsers"):
        current_step += 1
        if progress_callback: progress_callback("Extracting passwords...", (current_step / total_steps))
        passwords = []
        # Chromium browsers
        for name, path in BROWSERS.items():
            extractor = ChromiumExtractor(name, path)
            passwords.extend(extractor.extract_passwords())
        
        # Firefox
        ff_extractor = FirefoxExtractor()
        passwords.extend(ff_extractor.extract_passwords())
        
        with open(os.path.join(export_dir, "passwords.json"), "w", encoding="utf-8") as f:
            json.dump(passwords, f, indent=4)
        with open(os.path.join(export_dir, "passwords.txt"), "w", encoding="utf-8") as f:
            f.write(tabulate(passwords, headers="keys") if passwords else "No passwords found.")

    # 2. WiFi
    if options.get("wifi"):
        current_step += 1
        if progress_callback: progress_callback("Extracting WiFi...", (current_step / total_steps))
        sys_extractor = SystemExtractor()
        wifi_data = sys_extractor.extract_wifi_passwords()
        
        with open(os.path.join(export_dir, "wifi_profiles.json"), "w", encoding="utf-8") as f:
            json.dump(wifi_data, f, indent=4)
        with open(os.path.join(export_dir, "wifi_profiles.txt"), "w", encoding="utf-8") as f:
            f.write(tabulate(wifi_data, headers="keys") if wifi_data else "No WiFi profiles found.")

    # 3. System Info (Apps, Env, Hosts)
    if options.get("system"):
        current_step += 1
        if progress_callback: progress_callback("Capturing system info...", (current_step / total_steps))
        sys_extractor = SystemExtractor()
        sys_data = {
            "env": sys_extractor.extract_env_vars(),
            "apps": sys_extractor.extract_installed_apps()
        }
        sys_extractor.extract_hosts_file(export_dir) # Copy hosts file
        
        with open(os.path.join(export_dir, "system_info.json"), "w", encoding="utf-8") as f:
            json.dump(sys_data, f, indent=4)
        with open(os.path.join(export_dir, "system_info.txt"), "w", encoding="utf-8") as f:
            f.write("--- INSTALLED APPS ---\n")
            f.write(tabulate(sys_data["apps"], headers="keys"))

    # 4. Developer Data (SSH, Git)
    if options.get("developer"):
        current_step += 1
        if progress_callback: progress_callback("Capturing developer data...", (current_step / total_steps))
        sys_extractor = SystemExtractor()
        sys_extractor.extract_ssh_keys(export_dir)
        sys_extractor.extract_git_config(export_dir)

    # 5. Bookmarks
    if options.get("bookmarks"):
        current_step += 1
        if progress_callback: progress_callback("Backing up bookmarks...", (current_step / total_steps))
        for name, path in BROWSERS.items():
            extractor = ChromiumExtractor(name, path)
            extractor.extract_bookmarks(export_dir)

    # 6. VS Code Extensions
    if options.get("vscode"):
        current_step += 1
        if progress_callback: progress_callback("Listing VS Code extensions...", (current_step / total_steps))
        sys_extractor = SystemExtractor()
        extensions = sys_extractor.extract_vscode_extensions()
        with open(os.path.join(export_dir, "vscode_extensions.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(extensions))

    if progress_callback: progress_callback("Export completed!", 1.0)
    return export_dir

if __name__ == "__main__":
    # Default CLI behavior
    print("--- DataArk CLI ---")
    run_extraction({"browsers": True, "wifi": True, "system": True}, ".")
