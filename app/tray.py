import threading, time, webbrowser, os
from .main import run_server, APP_VERSION

def make_icon():
    from PIL import Image, ImageDraw
    im=Image.new('RGB',(64,64),(7,17,31)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((6,22,58,42),radius=7,fill=(229,36,50)); d.rectangle((12,27,46,37),fill=(255,255,255))
    return im

def start():
    import pystray
    threading.Thread(target=run_server,daemon=True).start(); time.sleep(1.0)
    url='http://127.0.0.1:5055'
    def open_ui(icon=None,item=None): webbrowser.open(url)
    def quit_app(icon,item): icon.stop(); os._exit(0)
    icon=pystray.Icon('RS3D_Status_Bar',make_icon(),f'RS3D Printer Status Bar v{APP_VERSION}',menu=pystray.Menu(
        pystray.MenuItem('Open Dashboard',open_ui,default=True),pystray.MenuItem('Exit',quit_app)))
    open_ui(); icon.run()
if __name__=='__main__': start()
