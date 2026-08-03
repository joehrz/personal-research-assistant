"""Windows desktop shell for the Personal Research Assistant.

Runs the FastAPI backend in a background thread, opens the UI in a native
window (pywebview), and registers a global quick-capture hotkey.

Setup (once):
    cd backend && pip install -e .[desktop]

Run:
    python desktop/main.py

Hotkeys (system-wide, Windows):
    Ctrl+Alt+Space   show the window on the quick-capture screen

Everything is logged to <data_dir>/logs/pra.log — check it after any crash
or hang (set PRA_LOG_LEVEL=DEBUG for maximum detail).
"""

from __future__ import annotations

import logging
import sys
import threading
import time
import urllib.request

HOST = "127.0.0.1"
PORT = 8734
URL = f"http://{HOST}:{PORT}"

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
        # log_config=None -> uvicorn logs flow into our root handlers/file.
        uvicorn.run(app, host=HOST, port=PORT, log_config=None)
    except Exception:
        log.exception("backend thread crashed")


def wait_for_backend(timeout: float = 20.0) -> None:
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


def main() -> None:
    # Build the app first: this configures logging into <data_dir>/logs/pra.log.
    from pra.config import Settings
    from pra.main import create_app

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

    def show_capture() -> None:
        """Bring the window up on the capture screen.

        Runs in its own worker thread and uses a JS hash change instead of a
        full page load — doing heavy window work directly inside the keyboard
        hook thread can deadlock the UI on Windows (app 'stops responding').
        """
        log.info("hotkey fired: showing capture")
        try:
            window.evaluate_js(
                "window.location.hash = '#/?capture=1&t=' + Date.now()"
            )
            log.debug("hotkey: hash set")
            window.show()
            window.restore()
            log.info("hotkey: window shown")
        except Exception:
            log.exception("hotkey handler failed")

    def on_hotkey() -> None:
        # Return from the keyboard hook immediately; do the work elsewhere.
        threading.Thread(target=show_capture, daemon=True, name="hotkey-worker").start()

    def register_hotkey() -> None:
        try:
            import keyboard
        except ImportError:
            log.warning("`keyboard` not installed; global hotkey disabled")
            return
        try:
            keyboard.add_hotkey("ctrl+alt+space", on_hotkey)
            log.info("global quick-capture hotkey registered: Ctrl+Alt+Space")
        except Exception:
            log.exception("could not register global hotkey (try running once as admin)")

    threading.Thread(target=register_hotkey, daemon=True, name="hotkey-setup").start()
    log.info("entering webview main loop")
    webview.start()
    log.info("webview main loop exited — shutting down")


if __name__ == "__main__":
    main()
