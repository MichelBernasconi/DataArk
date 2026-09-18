import os
import json
import sqlite3
import shutil
import ctypes

class FirefoxExtractor:
    def __init__(self):
        self.profiles_path = os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")

    def extract_passwords(self):
        results = []
        if not os.path.exists(self.profiles_path):
            return []

        for profile in os.scandir(self.profiles_path):
            if profile.is_dir():
                logins_path = os.path.join(profile.path, "logins.json")
                if os.path.exists(logins_path):
                    try:
                        with open(logins_path, "r") as f:
                            logins_data = json.load(f)
                        
                        for login in logins_data.get("logins", []):
                            results.append({
                                "browser": f"Firefox ({profile.name})",
                                "url": login.get("hostname"),
                                "user": login.get("encryptedUsername"), # Encrypted
                                "password": "Encrypted (Firefox Master Key required)"
                            })
                    except Exception as e:
                        print(f"Error reading Firefox profile {profile.name}: {e}")
        return results

    def _decompress_mozlz4(self, file_path):
        """Decompresses Mozilla proprietary mozLz40 format without external dependencies."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            if not data.startswith(b'mozLz40\x00'):
                return None
            compressed = data[12:]
            src = memoryview(compressed)
            src_len = len(src)
            src_pos = 0
            dst = bytearray()
            
            while src_pos < src_len:
                token = src[src_pos]
                src_pos += 1
                
                literal_len = token >> 4
                if literal_len == 15:
                    while src_pos < src_len:
                        b = src[src_pos]
                        src_pos += 1
                        literal_len += b
                        if b != 255:
                            break
                
                if src_pos + literal_len > src_len:
                    break
                dst.extend(src[src_pos:src_pos + literal_len])
                src_pos += literal_len
                
                if src_pos >= src_len:
                    break
                    
                offset = src[src_pos] | (src[src_pos + 1] << 8)
                src_pos += 2
                if offset == 0:
                    break
                    
                match_len = (token & 0x0F) + 4
                if (token & 0x0F) == 15:
                    while src_pos < src_len:
                        b = src[src_pos]
                        src_pos += 1
                        match_len += b
                        if b != 255:
                            break
                            
                for _ in range(match_len):
                    dst.append(dst[-offset])
                    
            return bytes(dst)
        except Exception as e:
            print(f"Error decompressing mozLz4 ({file_path}): {e}")
            return None

    def extract_open_tabs(self):
        """Extracts open tabs for all Firefox profiles."""
        results = []
        if not os.path.exists(self.profiles_path):
            return []

        for profile in os.scandir(self.profiles_path):
            if profile.is_dir():
                backup_dir = os.path.join(profile.path, "sessionstore-backups")
                candidates = [
                    os.path.join(backup_dir, "recovery.jsonlz4"),
                    os.path.join(backup_dir, "recovery.baklz4"),
                    os.path.join(backup_dir, "previous.jsonlz4"),
                    os.path.join(profile.path, "sessionstore.jsonlz4"),
                    os.path.join(profile.path, "sessionstore.js")
                ]

                seen_urls = set()
                for c_file in candidates:
                    if not os.path.exists(c_file):
                        continue
                    try:
                        raw_data = None
                        if c_file.endswith(".jsonlz4") or c_file.endswith(".baklz4"):
                            raw_data = self._decompress_mozlz4(c_file)
                        elif c_file.endswith(".js"):
                            with open(c_file, "rb") as f:
                                raw_data = f.read()

                        if raw_data:
                            session = json.loads(raw_data.decode("utf-8", errors="ignore"))
                            for win in session.get("windows", []):
                                for tab in win.get("tabs", []):
                                    entries = tab.get("entries", [])
                                    if entries:
                                        idx = tab.get("index", len(entries)) - 1
                                        if 0 <= idx < len(entries):
                                            entry = entries[idx]
                                            url = entry.get("url", "")
                                            title = entry.get("title", url)
                                            if url.startswith(("http://", "https://", "file://")) and url not in seen_urls:
                                                seen_urls.add(url)
                                                results.append({
                                                    "browser": f"Firefox ({profile.name})",
                                                    "title": title if title else url,
                                                    "url": url
                                                })
                        if results:
                            break # Found active session
                    except Exception as e:
                        print(f"Error parsing Firefox session {c_file}: {e}")

        return results

