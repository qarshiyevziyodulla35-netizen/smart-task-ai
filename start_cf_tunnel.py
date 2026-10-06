import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import re
import json
import time
import subprocess
import urllib.request

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from backend import database

def update_telegram_menu(public_url):
    token = database.get_setting("telegram_bot_token", "")
    if not token:
        print("[CF] Telegram bot token topilmadi.")
        return
    try:
        payload = {
            "menu_button": {
                "type": "web_app",
                "text": "📱 Ilova",
                "web_app": {
                    "url": public_url
                }
            }
        }
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/setChatMenuButton",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            if res_data.get("ok"):
                print(f"[CF] Telegram bot menyu tugmasi '📱 Ilova' yangilandi: {public_url}")
            else:
                print(f"[CF] Telegram API javobi: {res_data}")
    except Exception as e:
        print(f"[CF] Telegram menyu tugmasini yangilashda xato: {e}")

def main():
    port = 8000
    exe_path = os.path.join(CURRENT_DIR, "cloudflared.exe")
    if not os.path.exists(exe_path):
        print(f"Xato: {exe_path} topilmadi!")
        return

    cmd = [exe_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]
    print(f"[CF] Cloudflare Tunnel ishga tushirilmoqda...")
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )

    url_found = False
    url_pattern = re.compile(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com")

    for line in iter(proc.stdout.readline, ''):
        line_clean = line.strip()
        if "trycloudflare.com" in line_clean:
            print(f"[CF] {line_clean}")
        match = url_pattern.search(line_clean)
        if match and not url_found:
            url_found = True
            cf_url = match.group(0)
            print("\n" + "=" * 65)
            print(f"[CF] CLOUDFLARE TUNNEL TAYYOR!")
            print(f"[CF] URL: {cf_url}")
            print("=" * 65 + "\n")
            database.set_setting("web_app_url", cf_url)
            update_telegram_menu(cf_url)
            
    proc.wait()

if __name__ == "__main__":
    main()
