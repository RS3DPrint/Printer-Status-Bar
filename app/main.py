import json, threading, time, requests, socket, ipaddress
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from waitress import serve
from .storage import (init_db, rows, get_row, add_printer, update_printer, add_bar, update_bar,
                      delete_row, update_bar_assignment, get_settings, set_settings)
from .connectors.simulator import SimulatorConnector
from .connectors.moonraker import MoonrakerConnector
from .connectors.bambu import BambuConnector

app = Flask(__name__)
APP_VERSION = "0.2.1"
ROOT_DIR = Path(__file__).resolve().parent.parent
BOM_PATH = ROOT_DIR / "data" / "bom.json"
init_db()
status_cache, bar_cache, connectors = {}, {}, {}
manual_overrides = {}
bar_idle_since = {}

CONNECTOR_TYPES = {"simulator": SimulatorConnector, "klipper": MoonrakerConnector, "bambu": BambuConnector}
CONNECTOR_LABELS = {"simulator":"Simulator", "klipper":"Klipper / Moonraker", "bambu":"Bambu Lab LAN"}
DEFAULT_COLORS = {
    "idle":"#2563eb", "preparing":"#8b5cf6", "printing":"#22c55e", "paused":"#f59e0b",
    "complete":"#06b6d4", "error":"#ef4444", "cancelled":"#ef4444", "offline":"#64748b", "unknown":"#64748b"
}

def state_colors():
    s=get_settings(); out=dict(DEFAULT_COLORS)
    for k in list(out):
        if s.get("color_"+k): out[k]=s["color_"+k]
    return out

def get_connector(printer):
    pid=printer["id"]; key=(printer["kind"],printer["config"])
    existing=connectors.get(pid)
    if existing and existing[0]==key: return existing[1]
    cfg=json.loads(printer["config"] or "{}")
    obj=CONNECTOR_TYPES[printer["kind"]](cfg); connectors[pid]=(key,obj); return obj

def normalize_host(host):
    host=(host or "").rstrip("/")
    return host if host.startswith(("http://","https://","sim://")) else "http://"+host

def build_payload(bar,status):
    colors=state_colors(); state=status.get("state","unknown")
    override=manual_overrides.get(bar["id"])
    if override and override.get("until",0)>time.time(): return override["payload"]
    settings=get_settings()
    brightness=int(bar.get("brightness") or settings.get("default_brightness",96))
    if state == "idle":
        since=bar_idle_since.setdefault(bar["id"], time.time())
        try: dim_after=float(settings.get("idle_dim_minutes","10"))*60
        except: dim_after=600
        if dim_after >= 0 and time.time()-since >= dim_after:
            brightness=int(settings.get("idle_brightness","20"))
    else:
        bar_idle_since.pop(bar["id"],None)
    effect=bar.get("effect") or ("progress" if state=="printing" else "solid")
    return {"state":state,"progress":int(status.get("progress",0) or 0),"color":colors.get(state,"#64748b"),
            "brightness":brightness,"effect":effect,"led_count":int(bar.get("led_count") or 40)}

def push_bar(bar,status):
    payload=build_payload(bar,status); host=normalize_host(bar["host"])
    if host.startswith("sim://"):
        old=bar_cache.get(bar["id"],{})
        bar_cache[bar["id"]]={"online":True,"last":time.time(),"payload":payload,"battery":old.get("battery",78),
                              "firmware":"SIM-0.2.1","rssi":-42,"ip":"simulated","uptime":int(time.time()%100000),"led_count":bar.get("led_count",40)}
        return
    try:
        r=requests.post(host+"/api/status",json=payload,timeout=1.6); r.raise_for_status()
        health=requests.get(host+"/api/info",timeout=1.3).json()
        bar_cache[bar["id"]]={"online":True,"last":time.time(),"payload":payload,**health}
    except Exception as e:
        prev=bar_cache.get(bar["id"],{})
        bar_cache[bar["id"]]={"online":False,"last":time.time(),"error":str(e),"payload":payload,
                              "firmware":prev.get("firmware"),"battery":prev.get("battery"),"rssi":prev.get("rssi")}

def worker():
    while True:
        try:
            printers=rows("printers"); bars=rows("bars"); by_id={p["id"]:p for p in printers}
            for p in printers:
                if not p["enabled"]: continue
                try: s=get_connector(p).read_status().to_dict()
                except Exception as e: s={"state":"offline","progress":0,"remaining_minutes":None,"job_name":"","detail":str(e)}
                s["updated"]=time.time(); status_cache[p["id"]]=s
            for b in bars:
                if b["enabled"]:
                    st=status_cache.get(b["printer_id"],{"state":"idle","progress":0}) if b["printer_id"] in by_id else {"state":"idle","progress":0}
                    push_bar(b,st)
        except Exception as e:
            print("worker error:",e)
        try: interval=max(.5,float(get_settings().get("poll_interval","2")))
        except: interval=2
        time.sleep(interval)

def sanitized_printer(p):
    p=dict(p); p["config"]=json.loads(p["config"] or "{}")
    if p["kind"]=="bambu" and p["config"].get("access_code"): p["config"]["access_code"]="********"
    p["status"]=status_cache.get(p["id"],{"state":"unknown","progress":0}); return p

def summary_counts(printers,bars):
    states=[p.get("status",{}).get("state","unknown") for p in printers]
    return {"printers":len(printers),"printing":states.count("printing"),"paused":states.count("paused"),
            "errors":sum(x in ("error","offline") for x in states),"bars":len(bars),
            "bars_online":sum(1 for b in bars if b.get("status",{}).get("online"))}

@app.get("/")
def index(): return render_template("index.html")
@app.get("/api/bom")
def bom(): return jsonify(json.loads(BOM_PATH.read_text(encoding="utf-8")))
@app.get("/api/settings")
def settings_get(): return jsonify({"settings":get_settings(),"colors":state_colors(),"app_version":APP_VERSION})
@app.post("/api/settings")
def settings_post():
    d=request.get_json(force=True); payload=d.get("settings",d)
    set_settings(payload); return jsonify({"ok":True,"settings":get_settings(),"colors":state_colors()})

@app.get("/api/snapshot")
def snapshot():
    printers=[sanitized_printer(p) for p in rows("printers")]
    bars=rows("bars")
    for b in bars: b["status"]=bar_cache.get(b["id"],{"online":False})
    return jsonify({"printers":printers,"bars":bars,"state_colors":state_colors(),"app_version":APP_VERSION,
                    "connector_types":CONNECTOR_LABELS,"summary":summary_counts(printers,bars)})

@app.post("/api/printers")
def create_printer():
    d=request.get_json(force=True); kind=d.get("kind","simulator")
    if kind not in CONNECTOR_TYPES: return jsonify({"error":"Unsupported printer type"}),400
    return jsonify({"id":add_printer(d.get("name") or "Printer",kind,d.get("config") or {})})
@app.put("/api/printers/<int:pid>")
def edit_printer(pid):
    d=request.get_json(force=True); current=get_row("printers",pid)
    if not current: return jsonify({"error":"Not found"}),404
    kind=d.get("kind",current["kind"])
    if kind not in CONNECTOR_TYPES: return jsonify({"error":"Unsupported printer type"}),400
    cfg=d.get("config")
    if cfg and cfg.get("access_code")=="********": cfg=json.loads(current["config"] or "{}")
    update_printer(pid,d.get("name"),kind,cfg,d.get("enabled")); connectors.pop(pid,None); return jsonify({"ok":True})
@app.delete("/api/printers/<int:pid>")
def rm_printer(pid): delete_row("printers",pid); connectors.pop(pid,None); return jsonify({"ok":True})
@app.post("/api/printers/<int:pid>/test")
def test_printer(pid):
    p=get_row("printers",pid)
    if not p:return jsonify({"error":"Not found"}),404
    try: return jsonify({"ok":True,"status":get_connector(p).read_status().to_dict()})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),502

@app.post("/api/bars")
def create_bar():
    d=request.get_json(force=True); bid=add_bar(d.get("name") or "Status Bar",d.get("host") or "sim://bar",d.get("printer_id"))
    update_bar(bid,brightness=d.get("brightness",96),effect=d.get("effect","progress"),led_count=d.get("led_count",40),notes=d.get("notes",""))
    return jsonify({"id":bid})
@app.put("/api/bars/<int:bid>")
def edit_bar(bid):
    if not get_row("bars",bid): return jsonify({"error":"Not found"}),404
    d=request.get_json(force=True); update_bar(bid,**d); return jsonify({"ok":True})
@app.delete("/api/bars/<int:bid>")
def rm_bar(bid): delete_row("bars",bid); bar_cache.pop(bid,None); manual_overrides.pop(bid,None); return jsonify({"ok":True})
@app.post("/api/bars/<int:bid>/assign")
def assign_bar(bid): update_bar_assignment(bid,(request.get_json(force=True)).get("printer_id")); return jsonify({"ok":True})
@app.get("/api/bars/<int:bid>/info")
def bar_info(bid):
    b=get_row("bars",bid)
    if not b:return jsonify({"error":"Not found"}),404
    return jsonify({"bar":b,"status":bar_cache.get(bid,{"online":False})})
@app.post("/api/bars/<int:bid>/test")
def test_bar(bid):
    bar=get_row("bars",bid)
    if not bar:return jsonify({"error":"Not found"}),404
    d=request.get_json(silent=True) or {}; payload={"state":"test","progress":int(d.get("progress",50)),
        "color":d.get("color","#ff1744"),"brightness":int(d.get("brightness",bar.get("brightness",96))),"effect":d.get("effect","progress")}
    manual_overrides[bid]={"until":time.time()+int(d.get("seconds",8)),"payload":payload}; push_bar(bar,{"state":"idle","progress":0})
    return jsonify({"ok":bar_cache.get(bid,{}).get("online",False),"status":bar_cache.get(bid,{})})
@app.post("/api/bars/<int:bid>/clear-test")
def clear_test(bid): manual_overrides.pop(bid,None); return jsonify({"ok":True})
@app.post("/api/bars/<int:bid>/reboot")
def reboot_bar(bid):
    b=get_row("bars",bid)
    if not b:return jsonify({"error":"Not found"}),404
    h=normalize_host(b["host"])
    if h.startswith("sim://"):return jsonify({"ok":True})
    try:r=requests.post(h+"/api/reboot",timeout=2);return jsonify({"ok":r.ok})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),502
@app.post("/api/bars/<int:bid>/firmware")
def firmware(bid):
    bar=get_row("bars",bid)
    if not bar:return jsonify({"error":"Not found"}),404
    f=request.files.get("firmware")
    if not f:return jsonify({"error":"firmware file required"}),400
    host=normalize_host(bar["host"])
    if host.startswith("sim://"):return jsonify({"ok":True,"response":"simulated firmware update"})
    try:
        r=requests.post(host+"/api/firmware",data=f.read(),headers={"Content-Type":"application/octet-stream"},timeout=90)
        return jsonify({"ok":r.ok,"response":r.text[:500]}),(200 if r.ok else 502)
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),502

@app.post("/api/discover")
def discover():
    d=request.get_json(silent=True) or {}; subnet=d.get("subnet","")
    if not subnet:
        try:
            ip=socket.gethostbyname(socket.gethostname()); subnet=str(ipaddress.ip_network(ip+"/24",strict=False))
        except: return jsonify({"error":"Could not determine local subnet"}),400
    try: net=ipaddress.ip_network(subnet,strict=False)
    except Exception as e:return jsonify({"error":str(e)}),400
    hosts=list(net.hosts())[:254]; found=[]; lock=threading.Lock()
    def probe(ip):
        h="http://"+str(ip)
        try:
            r=requests.get(h+"/api/info",timeout=.18)
            if r.ok:
                j=r.json()
                if "firmware" in j or "RS3D" in str(j):
                    with lock: found.append({"host":str(ip),**j})
        except: pass
    ts=[threading.Thread(target=probe,args=(ip,)) for ip in hosts]
    for t in ts:t.start()
    for t in ts:t.join(.25)
    return jsonify({"subnet":str(net),"bars":found})

def run_server(host="0.0.0.0",port=5055):
    threading.Thread(target=worker,daemon=True).start(); print(f"RS3D Printer Status Bar v{APP_VERSION}: http://127.0.0.1:{port}")
    serve(app,host=host,port=port,threads=12)

if __name__=="__main__": run_server()
