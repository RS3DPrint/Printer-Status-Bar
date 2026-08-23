import json, ssl, threading, time
import paho.mqtt.client as mqtt
from .base import PrinterConnector, PrinterStatus

class BambuConnector(PrinterConnector):
    """Read-only LAN MQTT connector for Bambu printers.

    Requires printer IP, serial number and LAN access code. The exact LAN/Developer
    mode requirements vary by printer/firmware, so this connector only reads status.
    """
    def __init__(self, config):
        self.host = config.get("host", "")
        self.serial = config.get("serial", "")
        self.access_code = config.get("access_code", "")
        self.timeout = float(config.get("timeout", 4.0))
        self._lock = threading.Lock()
        self._last = {}
        self._connected = threading.Event()
        self._client = None
        self._start_client()

    def _start_client(self):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
        client.username_pw_set("bblp", self.access_code)
        client.tls_set(cert_reqs=ssl.CERT_NONE)
        client.tls_insecure_set(True)

        def on_connect(c, userdata, flags, reason_code, properties=None):
            if int(reason_code) == 0:
                self._connected.set()
                c.subscribe(f"device/{self.serial}/report")
                payload = json.dumps({"pushing": {"sequence_id": "1", "command": "pushall"}})
                c.publish(f"device/{self.serial}/request", payload)

        def on_message(c, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode("utf-8", "replace"))
                p = payload.get("print", {})
                if p:
                    with self._lock:
                        self._last.update(p)
            except Exception:
                pass

        client.on_connect = on_connect
        client.on_message = on_message
        client.connect_async(self.host, 8883, keepalive=30)
        client.loop_start()
        self._client = client

    def read_status(self):
        self._connected.wait(timeout=self.timeout)
        with self._lock:
            p = dict(self._last)
        if not p:
            return PrinterStatus(state="offline", detail="No Bambu LAN status received")
        raw = str(p.get("gcode_state", "")).upper()
        state = {
            "RUNNING": "printing", "PAUSE": "paused", "FINISH": "complete",
            "FAILED": "error", "IDLE": "idle", "PREPARE": "preparing"
        }.get(raw, raw.lower() or "unknown")
        return PrinterStatus(
            state=state,
            progress=int(p.get("mc_percent", 0) or 0),
            remaining_minutes=int(p.get("mc_remaining_time", 0) or 0),
            job_name=p.get("subtask_name") or p.get("gcode_file") or "",
            detail=f"Nozzle {p.get('nozzle_temper', '?')}°C | Bed {p.get('bed_temper', '?')}°C"
        )
