import os
import shutil
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

from .main import configured_port, APP_VERSION

def dashboard_url():
    return f"http://127.0.0.1:{configured_port()}"


def _edge_candidates():
    roots = [os.environ.get("PROGRAMFILES(X86)"), os.environ.get("PROGRAMFILES"), os.environ.get("LOCALAPPDATA")]
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
    roots = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")]
    rels = [Path("Google/Chrome/Application/chrome.exe"), Path("Google/Chrome Beta/Application/chrome.exe")]
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
    url = dashboard_url()
    for exe in list(_edge_candidates()) + list(_chrome_candidates()):
        try:
            return subprocess.Popen([exe, f"--app={url}", "--start-maximized", "--disable-features=TranslateUI"])
        except OSError:
            continue
    webbrowser.open(url)
    return None


def start():
    print(f"RS3D Printer Status Bar v{APP_VERSION}")
    print(f"Desktop UI: {dashboard_url()}")
    app_process = _open_app_window()
    if app_process is not None:
        app_process.wait()


if __name__ == "__main__":
    start()

