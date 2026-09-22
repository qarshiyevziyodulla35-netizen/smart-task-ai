import os
import sys
import webbrowser
import time
import socket
import threading

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0

def find_available_port(start_port=8000):
    port = start_port
    while port < start_port + 50:
        if is_port_available(port):
            return port
        port += 1
    return start_port

def open_browser(url):
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Brauzerni avtomatik ochishda xatolik: {e}")

def main():
    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"
    
    print("=" * 60)
    print("   🚀 SMARTTASK AI - VAQT VA VAZIFALAR BOSHQARUVI TIZIMI   ")
    print("=" * 60)
    print(f"Platforma manzili: {url}")
    print("Dasturni to'xtatish uchun: Ctrl + C bosing")
    print("=" * 60)

    # Brauzerni alohida oqimda ochish
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    import uvicorn
    from backend.main import app
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    main()
