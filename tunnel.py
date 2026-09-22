import os
import sys
import time
import json
import threading
import urllib.request
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend import database


def find_smart_task_port():
    for port in [8001, 8000, 8002, 8003, 8080]:
        try:
            url = f"http://127.0.0.1:{port}"
            req = urllib.request.Request(url, headers={"User-Agent": "SmartTaskPortCheck"})
            with urllib.request.urlopen(req, timeout=1.5) as res:
                content = res.read().decode("utf-8", errors="ignore")
                if "SmartTask AI" in content:
                    return port
        except Exception:
            continue
    return 8001


def update_telegram_menu_button(public_url):
    token = database.get_setting("telegram_bot_token", "")
    if not token:
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
                print("✅ Telegram botidagi '📱 Ilova' menyu tugmasi avtomatik SmartTask AI ga sozlandi!")
    except Exception as e:
        print(f"Telegram menyu tugmasini yangilashda eslatma: {e}")


def watch_ngrok_tunnel(target_port):
    time.sleep(2.5)
    for _ in range(20):
        try:
            req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels")
            with urllib.request.urlopen(req, timeout=2) as res:
                data = json.loads(res.read().decode("utf-8"))
                tunnels = data.get("tunnels", [])
                for t in tunnels:
                    pub_url = t.get("public_url", "")
                    if pub_url.startswith("https://"):
                        database.set_setting("web_app_url", pub_url)
                        print("\n" + "=" * 65)
                        print(f"🎉 TUNNEL TAYYOR VA ULANGAN!")
                        print(f"🌐 Ommaviy havola: {pub_url}")
                        print(f"📌 Yo'naltirilgan port: {target_port} (SmartTask AI)")
                        print("=" * 65)
                        update_telegram_menu_button(pub_url)
                        return
        except Exception:
            pass
        time.sleep(1.5)


def main():
    print("=" * 65)
    print("   🚀 SMARTTASK AI - TELEGRAM MINI APP TUNNELI   ")
    print("=" * 65)

    port = find_smart_task_port()
    print(f"🔍 SmartTask AI tizimi aniqlandi: http://127.0.0.1:{port}")
    if port != 8000:
        print(f"ℹ️ (Eslatma: Port 8000 boshqa loyiha bilan band bo'lgani uchun, SmartTask AI {port}-portda ishlamoqda)")

    threading.Thread(target=watch_ngrok_tunnel, args=(port,), daemon=True).start()

    print(f"⚡ ngrok http {port} ishga tushirilmoqda...\n")
    try:
        subprocess.run(["ngrok", "http", str(port)])
    except KeyboardInterrupt:
        print("\nTunnel to'xtatildi.")
    except Exception as e:
        print(f"Xatolik: {e}")


if __name__ == "__main__":
    main()
