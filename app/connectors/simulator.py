import time
from .base import PrinterConnector, PrinterStatus

class SimulatorConnector(PrinterConnector):
    def __init__(self, config):
        self.config = config
        self.started = time.time()

    def read_status(self):
        cycle = int((time.time() - self.started) / 2)
        progress = cycle % 101
        return PrinterStatus(
            state="printing" if progress < 100 else "complete",
            progress=progress,
            remaining_minutes=max(0, 100-progress),
            job_name="RS3D Demo Print",
            detail="Simulator"
        )
