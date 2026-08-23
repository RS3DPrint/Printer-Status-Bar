import json, sqlite3, os
DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rs3d_status.db")

def _conn():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def _columns(c, table):
    return {r[1] for r in c.execute(f"PRAGMA table_info({table})")}

def _add_column(c, table, definition):
    name = definition.split()[0]
    if name not in _columns(c, table):
        c.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")

def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS printers(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, kind TEXT NOT NULL,
            config TEXT NOT NULL DEFAULT '{}', enabled INTEGER NOT NULL DEFAULT 1)""")
        c.execute("""CREATE TABLE IF NOT EXISTS bars(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, host TEXT NOT NULL,
            printer_id INTEGER, enabled INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE SET NULL)""")
        for definition in [
            "brightness INTEGER NOT NULL DEFAULT 96",
            "effect TEXT NOT NULL DEFAULT 'progress'",
            "led_count INTEGER NOT NULL DEFAULT 40",
            "profile TEXT NOT NULL DEFAULT 'default'",
            "notes TEXT NOT NULL DEFAULT ''",
        ]:
            _add_column(c, "bars", definition)
        c.execute("""CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
        defaults = {
            "poll_interval":"2", "default_brightness":"96", "auto_open_browser":"1",
            "idle_dim_minutes":"10", "idle_brightness":"20", "app_name":"RS3D Printer Status Bar"
        }
        for k,v in defaults.items():
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k,v))

def rows(table):
    if table not in ("printers","bars"):
        raise ValueError("bad table")
    with _conn() as c:
        return [dict(r) for r in c.execute(f"SELECT * FROM {table} ORDER BY id")]

def get_row(table, row_id):
    if table not in ("printers","bars"):
        raise ValueError("bad table")
    with _conn() as c:
        r = c.execute(f"SELECT * FROM {table} WHERE id=?", (row_id,)).fetchone()
        return dict(r) if r else None

def add_printer(name, kind, config):
    with _conn() as c:
        cur = c.execute("INSERT INTO printers(name,kind,config) VALUES(?,?,?)", (name, kind, json.dumps(config)))
        return cur.lastrowid

def update_printer(row_id, name=None, kind=None, config=None, enabled=None):
    fields=[]; vals=[]
    for k,v in (("name",name),("kind",kind),("config",json.dumps(config) if config is not None else None),("enabled",enabled)):
        if v is not None: fields.append(f"{k}=?"); vals.append(v)
    if fields:
        with _conn() as c: c.execute(f"UPDATE printers SET {','.join(fields)} WHERE id=?", (*vals,row_id))

def add_bar(name, host, printer_id=None):
    with _conn() as c:
        cur = c.execute("INSERT INTO bars(name,host,printer_id) VALUES(?,?,?)", (name, host, printer_id))
        return cur.lastrowid

def update_bar(row_id, **kwargs):
    allowed={"name","host","printer_id","enabled","brightness","effect","led_count","profile","notes"}
    fields=[]; vals=[]
    for k,v in kwargs.items():
        if k in allowed and v is not None: fields.append(f"{k}=?"); vals.append(v)
    if fields:
        with _conn() as c: c.execute(f"UPDATE bars SET {','.join(fields)} WHERE id=?", (*vals,row_id))

def delete_row(table, row_id):
    if table not in ("printers", "bars"): raise ValueError("bad table")
    with _conn() as c: c.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))

def update_bar_assignment(bar_id, printer_id):
    update_bar(bar_id, printer_id=printer_id)

def get_settings():
    with _conn() as c: return {r["key"]:r["value"] for r in c.execute("SELECT key,value FROM settings")}

def set_settings(data):
    with _conn() as c:
        for k,v in data.items():
            c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(k),str(v)))
