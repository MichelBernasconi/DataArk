# 🛡️ DataArk

**DataArk** is a powerful, local-first backup utility designed for developers and power users who are about to format their Windows machines. It extracts "volatile" data that standard backups often miss.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ Features

- **🌐 Browser Credentials**: Support for Chrome, Edge, Brave, Opera, Opera GX, Vivaldi, and Firefox.
- **📑 Open Tabs & Multi-Profile Sessions**: Extracts active tabs across all browser profiles with a searchable HTML dashboard and JSON export.
- **📶 WiFi Profiles**: Extract SSIDs and cleartext passwords for all saved networks.
- **👨‍💻 Developer Kit**: Backup SSH keys (`.ssh`), Git global configuration, and VS Code extensions list.
- **🖥️ System Snapshot**: Save Windows `hosts` file, environment variables, and a list of installed applications.
- **🛡️ Privacy First**: Everything runs locally. No data ever leaves your machine.
- **🎨 Modern UI**: Sleek dark-mode interface built with CustomTkinter.

## 🚀 Installation

1. **Clone the repository**:
   ```powershell
   git clone https://github.com/michelbernasconi/DataArk.git
   cd DataArk
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Run DataArk**:
   ```powershell
   python gui.py
   ```

## ⚠️ Important Note on Browser Passwords
Due to recent security updates in Chromium (v20+ App-Bound Encryption), some passwords may be locked by the OS. DataArk includes an **Export Assistant** button that opens the official browser export pages to help you manually download your CSV backups for these entries.

---

## ☕ Support my work

If DataArk saved you hours of reconfiguration, consider buying me a coffee!

<a href="https://buymeacoffee.com/hoppingdreams" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Created with ❤️ by Michel Bernasconi*
