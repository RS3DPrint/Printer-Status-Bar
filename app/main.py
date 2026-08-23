import json, threading, time, requests, socket, ipaddress, re
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from waitress import serve
from .storage import (init_db, rows, get_row, add_printer, update_printer, add_bar, update_bar,
                      delete_row, update_bar_assignment, get_settings, set_settings)
from .connectors.simulator import SimulatorConnector
from .connectors.moonraker import MoonrakerConnector
from .connectors.bambu import BambuConnector
from .logging_setup import LOG_DIR, get_file_logger

app = Flask(__name__)
APP_VERSION = "0.3.9"
ROOT_DIR = Path(__file__).resolve().parent.parent
BOM_PATH = ROOT_DIR / "data" / "bom.json"
init_db()
status_cache, bar_cache, connectors = {}, {}, {}
manual_overrides = {}
bar_idle_since = {}
bar_log_state = {}
program_log = get_file_logger("rs3d.application", "application.log")
lightbar_log = get_file_logger("rs3d.lightbars", "lightbars.log")
program_log.info("Application initialized: version=%s log_directory=%s", APP_VERSION, LOG_DIR)

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

def controller_type(bar):
    value=bar.get("controller_type") or "adafruit_feather_s3"
    return value if value in ("athom_ls3p_wled_la","adafruit_feather_s3") else "adafruit_feather_s3"

def wled_payload(payload):
    color=(payload.get("color") or "#64748b").lstrip("#")[:6].upper()
    count=max(1,int(payload.get("led_count") or 40)); progress=max(0,min(100,int(payload.get("progress") or 0)))
    effect=payload.get("effect") or "solid"; state=payload.get("state") or "unknown"
    effects={"solid":0,"pulse":2,"chase":28,"rainbow":9}
    if effect=="progress" or state in ("printing","test"):
        lit=max(0,min(count,(progress*count+99)//100))
        pixels=[0,lit,color,lit,count,"000000"] if lit<count else [0,count,color]
        segment={"id":0,"start":0,"stop":count,"fx":0,"i":pixels}
    else:
        segment={"id":0,"start":0,"stop":count,"fx":effects.get(effect,0),"col":[[int(color[0:2],16),int(color[2:4],16),int(color[4:6],16)]]}
    return {"on":True,"bri":max(1,min(255,int(payload.get("brightness") or 96))),"seg":[segment]}

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
                              "firmware":"SIM-0.2.2","rssi":-42,"ip":"simulated","uptime":int(time.time()%100000),"led_count":bar.get("led_count",40)}
        _log_bar_status(bar, True, payload)
        return
    try:
        if controller_type(bar)=="athom_ls3p_wled_la":
            r=requests.post(host+"/json/state",json=wled_payload(payload),timeout=2.0); r.raise_for_status()
            info=requests.get(host+"/json/info",timeout=1.5).json(); wifi=info.get("wifi") or {}; leds=info.get("leds") or {}
            health={"name":info.get("name") or "Athom LS3P-WLED-LA","firmware":"WLED "+str(info.get("ver") or "?"),
                    "rssi":wifi.get("rssi"),"ip":info.get("ip") or bar["host"],"led_count":leds.get("count") or bar.get("led_count",40),
                    "chip":info.get("arch") or "ESP32-C3","controller_type":"athom_ls3p_wled_la"}
        else:
            r=requests.post(host+"/api/status",json=payload,timeout=1.6); r.raise_for_status()
            health=requests.get(host+"/api/info",timeout=1.3).json(); health["controller_type"]="adafruit_feather_s3"
        bar_cache[bar["id"]]={"online":True,"last":time.time(),"payload":payload,**health}
        _log_bar_status(bar, True, payload)
    except Exception as e:
        prev=bar_cache.get(bar["id"],{})
        bar_cache[bar["id"]]={"online":False,"last":time.time(),"error":str(e),"payload":payload,
                              "firmware":prev.get("firmware"),"battery":prev.get("battery"),"rssi":prev.get("rssi")}
        _log_bar_status(bar, False, payload, str(e))

def _log_bar_status(bar, online, payload, error=""):
    progress_bucket=int(payload.get("progress",0) or 0)//5
    signature=(online,payload.get("state"),progress_bucket,payload.get("effect"),error if not online else "")
    if bar_log_state.get(bar["id"])==signature:return
    bar_log_state[bar["id"]]=signature
    profile=controller_type(bar); host=bar.get("host")
    if online:
        lightbar_log.info("Light bar online: id=%s name=%s host=%s profile=%s state=%s progress=%s%% effect=%s",
                          bar["id"],bar.get("name"),host,profile,payload.get("state"),payload.get("progress"),payload.get("effect"))
    else:
        lightbar_log.warning("Light bar communication failed: id=%s name=%s host=%s profile=%s error=%s",
                             bar["id"],bar.get("name"),host,profile,error)

def worker():
    while True:
        try:
            printers=rows("printers"); bars=rows("bars"); by_id={p["id"]:p for p in printers}
            for p in printers:
                if not p["enabled"]: continue
                try: s=get_connector(p).read_status().to_dict()
                except Exception as e:
                    program_log.warning("Printer poll failed: id=%s name=%s kind=%s error=%s",p["id"],p["name"],p["kind"],e)
                    s={"state":"offline","progress":0,"remaining_minutes":None,"job_name":"","detail":str(e)}
                s["updated"]=time.time(); status_cache[p["id"]]=s
            for b in bars:
                if b["enabled"]:
                    st=status_cache.get(b["printer_id"],{"state":"idle","progress":0}) if b["printer_id"] in by_id else {"state":"idle","progress":0}
                    push_bar(b,st)
        except Exception as e:
            program_log.exception("Background worker failed: %s",e)
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
    old_port=int(get_settings().get("server_port","5055"))
    if "server_port" in payload:
        try: port=int(payload["server_port"])
        except (TypeError,ValueError): return jsonify({"error":"Port must be a number from 1024 to 65535"}),400
        if not 1024 <= port <= 65535: return jsonify({"error":"Port must be from 1024 to 65535"}),400
        payload["server_port"]=str(port)
    set_settings(payload); new_port=int(get_settings().get("server_port","5055"))
    program_log.info("Settings updated; service_port=%s restart_required=%s",new_port,new_port!=old_port)
    return jsonify({"ok":True,"settings":get_settings(),"colors":state_colors(),"restart_required":new_port!=old_port,
                    "message":("Restart the RS3D service to use port %d"%new_port) if new_port!=old_port else "Settings saved"})

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
    update_bar(bid,brightness=d.get("brightness",96),effect=d.get("effect","progress"),led_count=d.get("led_count",40),controller_type=d.get("controller_type","adafruit_feather_s3"),notes=d.get("notes",""))
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
    try:
        r=requests.post(h+("/json/state" if controller_type(b)=="athom_ls3p_wled_la" else "/api/reboot"),json=({"rb":True} if controller_type(b)=="athom_ls3p_wled_la" else None),timeout=2)
        return jsonify({"ok":r.ok})
    except Exception as e:return jsonify({"ok":False,"error":str(e)}),502
@app.post("/api/bars/<int:bid>/firmware")
def firmware(bid):
    bar=get_row("bars",bid)
    if not bar:return jsonify({"error":"Not found"}),404
    f=request.files.get("firmware")
    if not f:return jsonify({"error":"firmware file required"}),400
    if controller_type(bar)=="athom_ls3p_wled_la":
        return jsonify({"error":"Update Athom through its WLED web interface using an ESP32-C3 WLED image. Feather firmware is incompatible."}),400
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


def _local_subnet(cidr=""):
    if cidr:
        return ipaddress.ip_network(cidr, strict=False)
    # Use a UDP connect to select the active LAN interface without sending traffic.
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8",80)); ip=sock.getsockname()[0]
    finally:
        sock.close()
    return ipaddress.ip_network(ip+"/24",strict=False)

def _discover_bambu(net, timeout=2.8):
    """Listen and actively search for Bambu SSDP, then fall back to LAN service probing."""
    group="239.255.255.250"; ports=(1990,2021); found={}; lock=threading.Lock()

    def record(data,addr,source):
        text=data.decode("utf-8","ignore"); headers={}
        for line in text.replace("\r","").split("\n")[1:]:
            if ":" in line:
                key,value=line.split(":",1); headers[key.strip().lower()]=value.strip()
        model=headers.get("devmodel.bambu.com") or headers.get("devmodel")
        if not model and "bambu" not in text.lower():return
        serial=headers.get("devsn.bambu.com") or headers.get("serialnumber") or headers.get("usn","")
        serial=re.sub(r"^uuid:","",serial,flags=re.I).split("::")[0]
        ip=addr[0]
        item={"kind":"bambu","manufacturer":"Bambu Lab","host":ip,"serial":serial,
              "model":model or "Bambu Printer",
              "name":headers.get("devname.bambu.com") or headers.get("friendlyname") or model or "Bambu Printer",
              "source":source}
        with lock: found[ip]=item

    def listen(port):
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
        try:
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            sock.bind(("",port))
            membership=socket.inet_aton(group)+socket.inet_aton("0.0.0.0")
            sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,membership)
            sock.settimeout(.25); end=time.time()+timeout
            while time.time()<end:
                try: data,addr=sock.recvfrom(8192); record(data,addr,"SSDP announcement")
                except socket.timeout:continue
                except OSError:break
        except OSError as exc:
            program_log.info("Bambu passive SSDP listener unavailable: udp_port=%s error=%s",port,exc)
        finally:sock.close()

    listeners=[threading.Thread(target=listen,args=(port,),daemon=True,name=f"bambu-ssdp-{port}") for port in ports]
    for thread in listeners:thread.start()

    # Some firmware answers ssdp:all while other releases primarily announce; send both common targets.
    for port in ports:
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
        try:
            sock.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_TTL,2); sock.settimeout(.35)
            for target in ("ssdp:all","urn:bambulab-com:device:3dprinter:1"):
                msg=(f"M-SEARCH * HTTP/1.1\r\nHOST: {group}:{port}\r\nMAN: \"ssdp:discover\"\r\n"
                     f"MX: 2\r\nST: {target}\r\n\r\n").encode()
                sock.sendto(msg,(group,port))
            end=time.time()+timeout
            while time.time()<end:
                try:data,addr=sock.recvfrom(8192); record(data,addr,"SSDP reply")
                except socket.timeout:continue
                except OSError:break
        except OSError as exc:
            program_log.info("Bambu active SSDP search failed: udp_port=%s error=%s",port,exc)
        finally:sock.close()
    for thread in listeners:thread.join(.2)

    # Multicast is frequently filtered by Wi-Fi isolation/firewalls. Bambu LAN MQTT uses TLS port 8883;
    # FTPS port 990 provides a second signal and avoids labeling an ordinary MQTT broker as a printer.
    def probe(ip):
        host=str(ip)
        if host in found:return
        try:
            with socket.create_connection((host,8883),timeout=.16):pass
        except OSError:return
        try:
            with socket.create_connection((host,990),timeout=.12):pass
        except OSError:return
        with lock:
            found.setdefault(host,{"kind":"bambu","manufacturer":"Bambu Lab","host":host,"serial":"",
                                   "model":"Bambu Printer","name":"Bambu Lab Printer","source":"LAN services 8883/990"})
    probes=[threading.Thread(target=probe,args=(ip,),daemon=True,name="bambu-lan-probe") for ip in list(net.hosts())[:254]]
    for thread in probes:thread.start()
    for thread in probes:thread.join(.35)
    results=list(found.values())
    program_log.info("Bambu discovery completed: subnet=%s found=%s details=%s",net,len(results),
                     [(item.get("host"),item.get("model"),item.get("source")) for item in results])
    return results

def _discover_moonraker(net):
    found=[]; lock=threading.Lock(); sem=threading.Semaphore(48)
    def probe(ip):
        with sem:
            host=str(ip); base=f"http://{host}:7125"
            try:
                r=requests.get(base+"/server/info",timeout=.32)
                if not r.ok:return
                j=r.json(); result=j.get('result',j)
                if not isinstance(result,dict) or ('klippy_state' not in result and 'components' not in result):return
                name='Klipper / Moonraker Printer'; manufacturer='Klipper'
                hostname=''
                try:
                    sr=requests.get(base+"/machine/system_info",timeout=.28)
                    if sr.ok:
                        sj=sr.json().get('result',sr.json())
                        si=sj.get('system_info',sj) if isinstance(sj,dict) else {}
                        hostname=str(si.get('hostname') or '')
                except Exception: pass
                low=hostname.lower()
                if any(x in low for x in ('creality','ender','k1','k2','cr-')):
                    manufacturer='Creality'; name=hostname or 'Creality / Klipper Printer'
                elif hostname: name=hostname
                with lock: found.append({"kind":"klipper","manufacturer":manufacturer,"host":host,
                                         "port":7125,"name":name,"hostname":hostname,
                                         "state":result.get('klippy_state','unknown'),"source":"Moonraker"})
            except Exception: pass
    threads=[threading.Thread(target=probe,args=(ip,),daemon=True) for ip in list(net.hosts())[:254]]
    for t in threads:t.start()
    for t in threads:t.join(.8)
    return found

@app.post("/api/discover-printers")
def discover_printers():
    d=request.get_json(silent=True) or {}
    try: net=_local_subnet(d.get('subnet',''))
    except Exception as e:return jsonify({"error":str(e)}),400
    bambu=[]; klipper=[]
    # Run both discovery methods concurrently to keep the UI responsive.
    program_log.info("Printer discovery started: subnet=%s",net)
    def bscan():
        try:bambu.extend(_discover_bambu(net))
        except Exception as exc:program_log.exception("Bambu discovery failed: %s",exc)
    def kscan(): klipper.extend(_discover_moonraker(net))
    tb=threading.Thread(target=bscan); tk=threading.Thread(target=kscan)
    tb.start(); tk.start(); tb.join(7); tk.join(4)
    merged=[]; seen=set()
    for item in bambu+klipper:
        key=(item.get('kind'),item.get('host'))
        if key not in seen: seen.add(key); merged.append(item)
    merged.sort(key=lambda x:(x.get('manufacturer',''),x.get('host','')))
    program_log.info("Printer discovery finished: subnet=%s total=%s bambu=%s klipper=%s",net,len(merged),len(bambu),len(klipper))
    return jsonify({"subnet":str(net),"printers":merged,"count":len(merged)})

def configured_port():
    try: return max(1024,min(65535,int(get_settings().get("server_port","5055"))))
    except (TypeError,ValueError): return 5055

def run_server(host="0.0.0.0",port=None):
    port=port or configured_port()
    program_log.info("Web server starting: host=%s port=%s version=%s",host,port,APP_VERSION)
    threading.Thread(target=worker,daemon=True).start(); print(f"RS3D Printer Status Bar v{APP_VERSION}: http://127.0.0.1:{port}")
    serve(app,host=host,port=port,threads=12)

if __name__=="__main__": run_server()
