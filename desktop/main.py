"""Windows desktop shell for the Personal Research Assistant.

Runs the FastAPI backend in a background thread, opens the UI in a native
window (pywebview), and registers a global quick-capture hotkey.

Setup (once):
    cd backend && pip install -e .[desktop]

Run:
    python desktop/main.py

Hotkeys (system-wide, Windows):
    Ctrl+Alt+Space   show the window on the quick-capture screen
"""

from __future__ import annotations

import sys
import threading
import time
import urllib.request

HOST = "127.0.0.1"
PORT = 8734
URL = f"http://{HOST}:{PORT}"
CAPTURE_URL = f"{URL}/#/?capture=1"


def start_backend() -> None:
    import uvicorn

    from pra.main import create_app

    app = create_app()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


def wait_for_backend(timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{URL}/api/health", timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Backend failed to start")


def main() -> None:
    try:
        import webview
    except ImportError:
        sys.exit("pywebview is not installed. Run: cd backend && pip install -e .[desktop]")

    threading.Thread(target=start_backend, daemon=True).start()
    wait_for_backend()

    window = webview.create_window(
        "Research Assistant",
        URL,
        width=1280,
        height=840,
        min_size=(900, 600),
        background_color="#0b0e14",
    )

    def show_capture() -> None:
        window.load_url(CAPTURE_URL)
        window.show()
        window.restore()
        window.on_top = True
        window.on_top = False

    def register_hotkey() -> None:
        try:
            import keyboard
        except ImportError:
            print("`keyboard` not installed; global hotkey disabled.")
            return
        try:
            keyboard.add_hotkey("ctrl+alt+space", show_capture)
            print("Global quick-capture hotkey: Ctrl+Alt+Space")
        except Exception as exc:  # hotkeys can fail without admin rights
            print(f"Could not register global hotkey: {exc}")

    threading.Thread(target=register_hotkey, daemon=True).start()
    webview.start()


if __name__ == "__main__":
    main()
