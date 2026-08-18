"""Windows desktop shell for the Personal Research Assistant.

Runs the FastAPI backend in a background thread, opens the UI in a native
window (pywebview), lives in the system tray, and registers global hotkeys.

Setup (once):
    cd backend && pip install -e .[desktop]

Run:
    python desktop/main.py

Hotkeys (system-wide, Windows):
    Ctrl+Alt+Space   show the window on the quick-capture screen
    Ctrl+Alt+S       Windows snip overlay -> screenshot straight into the inbox

Closing the window hides it to the tray (hotkeys keep working); use the tray
icon's Quit to exit. Everything is logged to <data_dir>/logs/pra.log.
"""

from __future__ import annotations

import io
import logging
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8734
URL = f"http://{HOST}:{PORT}"
ICON_PATH = Path(__file__).resolve().parents[1] / "frontend" / "public" / "pwa-192.png"

log = logging.getLogger("desktop")


def excepthook(exc_type, exc, tb):
    log.critical("UNCAUGHT EXCEPTION", exc_info=(exc_type, exc, tb))


def thread_excepthook(args):
    log.critical(
        "UNCAUGHT EXCEPTION in thread %r",
        getattr(args.thread, "name", "?"),
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def start_backend(app) -> None:
    import uvicorn

    log.info("backend thread: starting uvicorn on %s:%s", HOST, PORT)
    try:
        uvicorn.run(app, host=HOST, port=PORT, log_config=None)
    except Exception:
        log.exception("backend thread crashed")


def wait_for_backend(timeout: float = 20.0) -> None:
    import urllib.request

    log.info("waiting for backend to answer /api/health ...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{URL}/api/health", timeout=1):
                log.info("backend is up")
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("Backend failed to start — see the log for the reason")


# ---- snip-to-inbox ---------------------------------------------------------

def _clipboard_png() -> bytes | None:
    """Return the clipboard image as PNG bytes, or None."""
    from PIL import Image, ImageGrab

    grabbed = ImageGrab.grabclipboard()
    if isinstance(grabbed, list):  # copied files -> open the first image
        for path in grabbed:
            try:
                grabbed = Image.open(path)
                break
            except OSError:
                continue
        else:
            return None
    if grabbed is None or not hasattr(grabbed, "save"):
        return None
    buf = io.BytesIO()
    grabbed.save(buf, "PNG")
    return buf.getvalue()


def snip_to_inbox() -> None:
    """Trigger the Windows snip overlay; when a snip lands on the clipboard,
    upload it and file it as an inbox note."""
    try:
        import httpx
        import keyboard
    except ImportError:
        log.warning("snip: keyboard/httpx not available")
        return
    try:
        before = _clipboard_png()
    except Exception:
        before = None
    log.info("snip: opening Windows snip overlay")
    keyboard.send("windows+shift+s")

    deadline = time.time() + 90  # user may take a while to draw the region
    while time.time() < deadline:
        time.sleep(0.6)
        try:
            data = _clipboard_png()
        except Exception:
            continue
        if data is None or data == before:
            continue
        try:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            upload = httpx.post(
                f"{URL}/api/assets",
                files={"file": (f"snip-{stamp.replace(':', '')}.png", data, "image/png")},
                timeout=30,
            )
            upload.raise_for_status()
            markdown = upload.json()["markdown"]
            httpx.post(
                f"{URL}/api/notes",
                json={"title": f"Snip {stamp}", "content": markdown,
                      "kind": "snippet", "inbox": True},
                timeout=30,
            ).raise_for_status()
            log.info("snip: saved to inbox (%d bytes)", len(data))
        except Exception:
            log.exception("snip: saving failed")
        return
    log.info("snip: no screenshot appeared on the clipboard (timed out)")


def main() -> None:
    # Build the app first: this configures logging into <data_dir>/logs/pra.log.
    from pra.config import Settings
    from pra.main import create_app
    from pra.services import backup as backup_service

    settings = Settings.from_env()
    app = create_app(settings)

    sys.excepthook = excepthook
    threading.excepthook = thread_excepthook
    log.info("desktop shell starting (python %s)", sys.version.split()[0])

    try:
        import webview
        log.info("pywebview %s loaded", getattr(webview, "__version__", "?"))
    except ImportError:
        log.critical("pywebview is not installed")
        sys.exit("pywebview is not installed. Run: cd backend && pip install -e .[desktop]")

    threading.Thread(target=start_backend, args=(app,), daemon=True, name="backend").start()
    wait_for_backend()

    window = webview.create_window(
        "Research Assistant",
        URL,
        width=1280,
        height=840,
        min_size=(900, 600),
        background_color="#0b0e14",
    )
    log.info("window created")

    def show_window() -> None:
        try:
            window.show()
            window.restore()
        except Exception:
            log.exception("show_window failed")

    def show_capture() -> None:
        """Runs in a worker thread — never inside the keyboard hook thread,
        which can deadlock the UI on Windows."""
        log.info("hotkey fired: showing capture")
        try:
            window.evaluate_js("window.location.hash = '#/?capture=1&t=' + Date.now()")
            show_window()
            log.info("hotkey: window shown")
        except Exception:
            log.exception("hotkey handler failed")

    def on_capture_hotkey() -> None:
        threading.Thread(target=show_capture, daemon=True, name="hotkey-capture").start()

    def on_snip_hotkey() -> None:
        threading.Thread(target=snip_to_inbox, daemon=True, name="hotkey-snip").start()

    # ---- system tray -------------------------------------------------------

    tray_icon = None

    def make_tray():
        try:
            import pystray
            from PIL import Image
        except ImportError:
            log.warning("pystray/Pillow not installed; tray disabled "
                        "(reinstall: pip install -e .[desktop])")
            return None
        try:
            image = (Image.open(ICON_PATH) if ICON_PATH.exists()
                     else Image.new("RGB", (64, 64), (99, 102, 241)))

            def tray_backup():
                result = backup_service.run_backup(settings)
                log.info("tray backup: %s", result["message"])

            def tray_quit(icon):
                log.info("quit from tray")
                icon.stop()
                try:
                    window.destroy()
                except Exception:
                    log.exception("window destroy failed")

            icon = pystray.Icon(
                "research-assistant", image, "Research Assistant",
                menu=pystray.Menu(
                    pystray.MenuItem("Open", lambda: show_window(), default=True),
                    pystray.MenuItem("Quick capture\tCtrl+Alt+Space", lambda: on_capture_hotkey()),
                    pystray.MenuItem("Snip to inbox\tCtrl+Alt+S", lambda: on_snip_hotkey()),
                    pystray.MenuItem("Back up vault now", lambda: tray_backup()),
                    pystray.MenuItem("Quit", tray_quit),
                ),
            )
            threading.Thread(target=icon.run, daemon=True, name="tray").start()
            log.info("tray icon running")
            return icon
        except Exception:
            log.exception("tray setup failed")
            return None

    tray_icon = make_tray()

    if tray_icon is not None:
        # Close button hides to tray instead of quitting (Quit lives in the tray).
        def on_closing():
            log.info("window close -> hiding to tray")
            try:
                window.hide()
            except Exception:
                log.exception("hide failed")
            return False  # cancel the real close

        window.events.closing += on_closing

    def register_hotkeys() -> None:
        try:
            import keyboard
        except ImportError:
            log.warning("`keyboard` not installed; global hotkeys disabled")
            return
        try:
            keyboard.add_hotkey("ctrl+alt+space", on_capture_hotkey)
            keyboard.add_hotkey("ctrl+alt+s", on_snip_hotkey)
            log.info("global hotkeys registered: Ctrl+Alt+Space (capture), Ctrl+Alt+S (snip)")
        except Exception:
            log.exception("could not register global hotkeys (try running once as admin)")

    threading.Thread(target=register_hotkeys, daemon=True, name="hotkey-setup").start()
    log.info("entering webview main loop")
    webview.start()
    if tray_icon is not None:
        tray_icon.stop()
    log.info("webview main loop exited — shutting down")


if __name__ == "__main__":
    main()
