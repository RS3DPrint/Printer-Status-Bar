import threading, time, webbrowser
from .main import run_server, APP_VERSION

def start():
    t=threading.Thread(target=run_server,daemon=True); t.start(); time.sleep(1.2)
    url='http://127.0.0.1:5055'
    try:
        import webview
        webview.create_window(f'RS3D Printer Status Bar v{APP_VERSION}',url,width=1380,height=900,min_size=(980,650))
        webview.start()
    except Exception:
        webbrowser.open(url)
        try:
            while t.is_alive(): time.sleep(1)
        except KeyboardInterrupt: pass
if __name__=='__main__': start()
