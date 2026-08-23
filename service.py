import os
import sys
import threading
from pathlib import Path

import servicemanager
import win32event
import win32service
import win32serviceutil
from waitress import create_server

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app, configured_port, worker
from app.logging_setup import get_file_logger

service_log = get_file_logger("rs3d.service", "service.log")


class RS3DStatusBarService(win32serviceutil.ServiceFramework):
    _svc_name_ = "RS3DPrinterStatusBar"
    _svc_display_name_ = "RS3D Printer Status Bar"
    _svc_description_ = "Keeps the RS3D printer status dashboard and lighting controller running."

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.http_server = None

    def SvcStop(self):
        service_log.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.http_server is not None:
            self.http_server.close()
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        try:
            servicemanager.LogInfoMsg("RS3D Printer Status Bar service starting")
            service_log.info("Service starting: port=%s", configured_port())
            threading.Thread(target=worker, daemon=True).start()
            self.http_server = create_server(app, host="0.0.0.0", port=configured_port(), threads=12)
            self.http_server.run()
        except Exception as exc:
            service_log.exception("Service failed: %s", exc)
            servicemanager.LogErrorMsg(f"RS3D service failed: {exc}")
            raise
        finally:
            service_log.info("Service stopped")


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(RS3DStatusBarService)
