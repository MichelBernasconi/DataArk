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

    # 7. Open Browser Tabs (Multi-Session & Multi-Profile)
    if options.get("tabs"):
        current_step += 1
        if progress_callback: progress_callback("Extracting open tabs from all sessions...", (current_step / total_steps))
        tabs_data = []

        # Chromium browsers
        for name, path in BROWSERS.items():
            extractor = ChromiumExtractor(name, path)
            tabs_data.extend(extractor.extract_open_tabs())

        # Firefox
        ff_extractor = FirefoxExtractor()
        tabs_data.extend(ff_extractor.extract_open_tabs())

        # Save JSON
        with open(os.path.join(export_dir, "open_tabs.json"), "w", encoding="utf-8") as f:
            json.dump(tabs_data, f, indent=4)

        # Save TXT
        with open(os.path.join(export_dir, "open_tabs.txt"), "w", encoding="utf-8") as f:
            if tabs_data:
                f.write(tabulate(tabs_data, headers="keys"))
            else:
                f.write("No open tabs found in sessions.")

        # Save HTML Dashboard
        generate_tabs_html(tabs_data, os.path.join(export_dir, "open_tabs.html"))

    if progress_callback: progress_callback("Export completed!", 1.0)
    return export_dir

def generate_tabs_html(tabs_data, output_file):
    """Generates a modern, searchable dark-mode HTML dashboard of all open tabs grouped by profile."""
    # Group tabs by browser/profile
    grouped = {}
    for item in tabs_data:
        b_name = item.get("browser", "Other")
        if b_name not in grouped:
            grouped[b_name] = []
        grouped[b_name].append(item)

    import html
    total_tabs = len(tabs_data)
    total_profiles = len(grouped)

    cards_html = ""
    for idx, (profile_name, items) in enumerate(grouped.items()):
        items_html = ""
        urls_list = []
        for it in items:
            t = html.escape(it.get("title", "") or it.get("url", ""))
            u = html.escape(it.get("url", ""))
            raw_u = it.get("url", "").replace('"', '&quot;')
            urls_list.append(raw_u)
            items_html += f"""
            <li class="tab-item">
                <a href="{u}" target="_blank" rel="noopener noreferrer" class="tab-link">
                    <span class="tab-title">{t}</span>
                    <span class="tab-url">{u}</span>
                </a>
            </li>"""

        json_urls = json.dumps(urls_list)
        cards_html += f"""
        <div class="profile-card" data-profile="{html.escape(profile_name)}">
            <div class="card-header">
                <div>
                    <h2>{html.escape(profile_name)}</h2>
                    <span class="badge">{len(items)} tabs</span>
                </div>
                <div class="card-actions">
                    <button class="btn btn-secondary" onclick='copyUrls({json_urls})'>📋 Copy URLs</button>
                    <button class="btn btn-primary" onclick='openAll({json_urls})'>🚀 Open All</button>
                </div>
            </div>
            <ul class="tab-list">
                {items_html}
            </ul>
        </div>"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataArk - Open Tabs Backup</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --badge-bg: #0369a1;
            --badge-text: #e0f2fe;
            --item-hover: #2d3d54;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            padding: 30px 20px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 30px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 15px;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 20px;
        }}
        .header-title h1 {{
            font-size: 28px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .header-title p {{
            color: var(--text-muted);
            font-size: 14px;
            margin-top: 4px;
        }}
        .stats {{
            display: flex;
            gap: 12px;
        }}
        .stat-badge {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
        }}
        .search-bar {{
            margin-bottom: 25px;
        }}
        .search-input {{
            width: 100%;
            padding: 12px 18px;
            font-size: 15px;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            color: var(--text-main);
            outline: none;
            transition: border-color 0.2s;
        }}
        .search-input:focus {{
            border-color: var(--accent);
        }}
        .profile-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            margin-bottom: 24px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background: rgba(15, 23, 42, 0.6);
            border-bottom: 1px solid var(--card-border);
        }}
        .card-header h2 {{
            font-size: 18px;
            font-weight: 600;
            display: inline-block;
            margin-right: 10px;
        }}
        .badge {{
            background: var(--badge-bg);
            color: var(--badge-text);
            font-size: 12px;
            font-weight: 600;
            padding: 3px 9px;
            border-radius: 12px;
            vertical-align: middle;
        }}
        .card-actions {{
            display: flex;
            gap: 8px;
        }}
        .btn {{
            cursor: pointer;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            border: none;
            transition: all 0.2s;
        }}
        .btn-primary {{
            background: var(--accent);
            color: #ffffff;
        }}
        .btn-primary:hover {{
            background: var(--accent-hover);
        }}
        .btn-secondary {{
            background: #334155;
            color: #cbd5e1;
        }}
        .btn-secondary:hover {{
            background: #475569;
        }}
        .tab-list {{
            list-style: none;
            max-height: 400px;
            overflow-y: auto;
        }}
        .tab-item {{
            border-bottom: 1px solid rgba(51, 65, 85, 0.4);
        }}
        .tab-item:last-child {{
            border-bottom: none;
        }}
        .tab-link {{
            display: flex;
            flex-direction: column;
            padding: 12px 20px;
            text-decoration: none;
            color: inherit;
            transition: background 0.15s;
        }}
        .tab-link:hover {{
            background: var(--item-hover);
        }}
        .tab-title {{
            font-size: 14px;
            font-weight: 500;
            color: #e2e8f0;
            margin-bottom: 2px;
            word-break: break-word;
        }}
        .tab-url {{
            font-size: 12px;
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>🛡️ DataArk - Open Tabs</h1>
                <p>Saved browser sessions and tabs from all active profiles</p>
            </div>
            <div class="stats">
                <div class="stat-badge">📂 {total_profiles} Profiles</div>
                <div class="stat-badge">📑 {total_tabs} Total Tabs</div>
            </div>
        </header>

        <div class="search-bar">
            <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search open tabs by title or URL..." onkeyup="filterTabs()">
        </div>

        <div id="cardsContainer">
            {cards_html if cards_html else '<p style="color: gray; text-align: center; padding: 40px;">No open tabs detected.</p>'}
        </div>
    </div>

    <script>
        function openAll(urls) {{
            if (!confirm(`Are you sure you want to open all ${{urls.length}} tabs in this profile?`)) return;
            urls.forEach(u => window.open(u, '_blank'));
        }}

        function copyUrls(urls) {{
            const text = urls.join('\\n');
            navigator.clipboard.writeText(text).then(() => {{
                alert(`Copied ${{urls.length}} URLs to clipboard!`);
            }}).catch(err => {{
                prompt('Copy the URLs:', text);
            }});
        }}

        function filterTabs() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.profile-card');
            
            cards.forEach(card => {{
                const items = card.querySelectorAll('.tab-item');
                let visibleInCard = 0;
                items.forEach(item => {{
                    const title = item.querySelector('.tab-title').textContent.toLowerCase();
                    const url = item.querySelector('.tab-url').textContent.toLowerCase();
                    if (title.includes(query) || url.includes(query)) {{
                        item.style.display = '';
                        visibleInCard++;
                    }} else {{
                        item.style.display = 'none';
                    }}
                }});
                card.style.display = visibleInCard > 0 || query === '' ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    # Default CLI behavior
    print("--- DataArk CLI ---")
    run_extraction({"browsers": True, "wifi": True, "system": True, "tabs": True}, ".")

