import requests
from .base import PrinterConnector, PrinterStatus

class MoonrakerConnector(PrinterConnector):
    def __init__(self, config):
        self.host = config.get("host", "").rstrip("/")
        if self.host and not self.host.startswith(("http://", "https://")):
            self.host = "http://" + self.host
        self.timeout = float(config.get("timeout", 2.5))

    @staticmethod
    def _map_state(raw):
        raw = (raw or "").lower()
        return {
            "printing": "printing",
            "paused": "paused",
            "complete": "complete",
            "cancelled": "cancelled",
            "error": "error",
            "standby": "idle",
        }.get(raw, raw or "unknown")

    def read_status(self):
        url = self.host + "/printer/objects/query?print_stats&virtual_sdcard&webhooks"
        r = requests.get(url, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()["result"]["status"]
        stats = data.get("print_stats", {})
        vsd = data.get("virtual_sdcard", {})
        webhooks = data.get("webhooks", {})
        progress = int(round(float(vsd.get("progress", 0)) * 100))
        info = stats.get("info") or {}
        remaining = None
        total = info.get("total_layer")
        current = info.get("current_layer")
        detail = webhooks.get("state_message", "")
        return PrinterStatus(
            state=self._map_state(stats.get("state")),
            progress=max(0, min(100, progress)),
            remaining_minutes=remaining,
            job_name=stats.get("filename", ""),
            detail=detail or (f"Layer {current}/{total}" if current and total else "")
        )
