import json, threading, time, requests
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from waitress import serve
from .storage import init_db, rows, add_printer, add_bar, delete_row, update_bar_assignment
from .connectors.simulator import SimulatorConnector
from .connectors.moonraker import MoonrakerConnector
from .connectors.bambu import BambuConnector

app = Flask(__name__)
APP_VERSION = "0.1.1"
ROOT_DIR = Path(__file__).resolve().parent.parent
BOM_PATH = ROOT_DIR / "data" / "bom.json"
init_db()
status_cache = {}
bar_cache = {}
connectors = {}

CONNECTOR_TYPES = {
    "simulator": SimulatorConnector,
    "klipper": MoonrakerConnector,
    "bambu": BambuConnector,
}

STATE_COLORS = {
    "idle": "#2b6cff", "preparing": "#8b5cf6", "printing": "#22c55e",
    "paused": "#f59e0b", "complete": "#00d4ff", "error": "#ef4444",
    "cancelled": "#ef4444", "offline": "#64748b", "unknown": "#64748b"
}

def get_connector(printer):
    pid = printer["id"]
    key = (printer["kind"], printer["config"])
    existing = connectors.get(pid)
    if existing and existing[0] == key:
        return existing[1]
    cfg = json.loads(printer["config"] or "{}")
    cls = CONNECTOR_TYPES[printer["kind"]]
    obj = cls(cfg)
    connectors[pid] = (key, obj)
    return obj

def push_bar(bar, status):
    payload = {
        "state": status.get("state", "unknown"),
        "progress": int(status.get("progress", 0)),
        "color": STATE_COLORS.get(status.get("state"), "#64748b"),
        "brightness": 96,
        "effect": "progress" if status.get("state") == "printing" else "solid"
    }
    host = bar["host"].rstrip("/")
    if host.startswith("sim://"):
        bar_cache[bar["id"]] = {"online": True, "last": time.time(), "payload": payload, "battery": 78}
        return
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    try:
        r = requests.post(host + "/api/status", json=payload, timeout=1.5)
        r.raise_for_status()
        health = requests.get(host + "/api/info", timeout=1.2).json()
        bar_cache[bar["id"]] = {"online": True, "last": time.time(), "payload": payload, **health}
    except Exception as e:
        bar_cache[bar["id"]] = {"online": False, "last": time.time(), "error": str(e), "payload": payload}

def worker():
    while True:
        printers = rows("printers")
        bars = rows("bars")
        by_id = {p["id"]: p for p in printers}
        for p in printers:
            if not p["enabled"]: continue
            try:
                s = get_connector(p).read_status().to_dict()
            except Exception as e:
                s = {"state":"offline","progress":0,"remaining_minutes":None,"job_name":"","detail":str(e)}
            s["updated"] = time.time()
            status_cache[p["id"]] = s
        for b in bars:
            if b["enabled"] and b["printer_id"] in by_id:
                push_bar(b, status_cache.get(b["printer_id"], {"state":"offline","progress":0}))
        time.sleep(2)

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/bom")
def bom():
    with BOM_PATH.open("r", encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.get("/api/snapshot")
def snapshot():
    printers = rows("printers")
    for p in printers:
        p["config"] = json.loads(p["config"] or "{}")
        if p["kind"] == "bambu" and p["config"].get("access_code"):
            p["config"]["access_code"] = "********"
        p["status"] = status_cache.get(p["id"], {"state":"unknown","progress":0})
    bars = rows("bars")
    for b in bars:
        b["status"] = bar_cache.get(b["id"], {"online": False})
    return jsonify({"printers": printers, "bars": bars, "state_colors": STATE_COLORS, "app_version": APP_VERSION})

@app.post("/api/printers")
def create_printer():
    d = request.get_json(force=True)
    kind = d.get("kind", "simulator")
    if kind not in CONNECTOR_TYPES:
        return jsonify({"error":"Unsupported printer type"}), 400
    pid = add_printer(d.get("name") or "Printer", kind, d.get("config") or {})
    return jsonify({"id": pid})

@app.delete("/api/printers/<int:pid>")
def rm_printer(pid):
    delete_row("printers", pid); connectors.pop(pid, None)
    return jsonify({"ok": True})

@app.post("/api/bars")
def create_bar():
    d = request.get_json(force=True)
    bid = add_bar(d.get("name") or "Status Bar", d.get("host") or "sim://bar", d.get("printer_id"))
    return jsonify({"id": bid})

@app.delete("/api/bars/<int:bid>")
def rm_bar(bid):
    delete_row("bars", bid); bar_cache.pop(bid, None)
    return jsonify({"ok": True})

@app.post("/api/bars/<int:bid>/assign")
def assign_bar(bid):
    d = request.get_json(force=True)
    update_bar_assignment(bid, d.get("printer_id"))
    return jsonify({"ok": True})

@app.post("/api/bars/<int:bid>/test")
def test_bar(bid):
    bar = next((x for x in rows("bars") if x["id"] == bid), None)
    if not bar: return jsonify({"error":"Not found"}),404
    d = request.get_json(silent=True) or {}
    test = {"state":"test","progress":int(d.get("progress",50)),"color":d.get("color","#ff1744"),"brightness":int(d.get("brightness",100)),"effect":d.get("effect","progress")}
    host = bar["host"].rstrip("/")
    if host.startswith("sim://"):
        bar_cache[bid] = {"online":True,"last":time.time(),"payload":test,"battery":78}
        return jsonify({"ok":True})
    if not host.startswith(("http://","https://")): host = "http://"+host
    r = requests.post(host+"/api/status", json=test, timeout=2)
    return jsonify({"ok": r.ok, "status_code": r.status_code})

@app.post("/api/bars/<int:bid>/firmware")
def firmware(bid):
    bar = next((x for x in rows("bars") if x["id"] == bid), None)
    if not bar: return jsonify({"error":"Not found"}),404
    f = request.files.get("firmware")
    if not f: return jsonify({"error":"firmware file required"}),400
    host = bar["host"].rstrip("/")
    if not host.startswith(("http://","https://")): host = "http://"+host
    r = requests.post(host+"/api/firmware", data=f.read(), headers={"Content-Type":"application/octet-stream"}, timeout=60)
    return jsonify({"ok":r.ok,"response":r.text[:500]}), (200 if r.ok else 502)

if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    print("RS3D Printer Status Bar Controller: http://127.0.0.1:5055")
    serve(app, host="0.0.0.0", port=5055, threads=8)
