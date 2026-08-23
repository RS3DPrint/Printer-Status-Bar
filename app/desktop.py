import os
import shutil
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

from .main import run_server, APP_VERSION

URL = "http://127.0.0.1:5055"


def _edge_candidates():
    roots = [
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("PROGRAMFILES"),
        os.environ.get("LOCALAPPDATA"),
    ]
    rels = [
        Path("Microsoft/Edge/Application/msedge.exe"),
        Path("Microsoft/Edge Beta/Application/msedge.exe"),
        Path("Microsoft/Edge Dev/Application/msedge.exe"),
    ]
    for root in roots:
        if not root:
            continue
        for rel in rels:
            p = Path(root) / rel
            if p.exists():
                yield str(p)
    found = shutil.which("msedge")
    if found:
        yield found


def _chrome_candidates():
    roots = [
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("LOCALAPPDATA"),
    ]
    rels = [
        Path("Google/Chrome/Application/chrome.exe"),
        Path("Google/Chrome Beta/Application/chrome.exe"),
    ]
    for root in roots:
        if not root:
            continue
        for rel in rels:
            p = Path(root) / rel
            if p.exists():
                yield str(p)
    found = shutil.which("chrome")
    if found:
        yield found


def _open_app_window():
    for exe in list(_edge_candidates()) + list(_chrome_candidates()):
        try:
            return subprocess.Popen([
                exe,
                f"--app={URL}",
                "--start-maximized",
                "--disable-features=TranslateUI",
            ])
        except OSError:
            continue
    webbrowser.open(URL)
    return None


def start():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1.25)

    print(f"RS3D Printer Status Bar v{APP_VERSION}")
    print(f"Desktop UI: {URL}")
    app_process = _open_app_window()

    try:
        if app_process is not None:
            while app_process.poll() is None and server_thread.is_alive():
                time.sleep(0.5)
        else:
            while server_thread.is_alive():
                time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    start()
