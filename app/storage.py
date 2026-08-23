import json, sqlite3, os
DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rs3d_status.db")

def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS printers(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, kind TEXT NOT NULL,
            config TEXT NOT NULL DEFAULT '{}', enabled INTEGER NOT NULL DEFAULT 1)""")
        c.execute("""CREATE TABLE IF NOT EXISTS bars(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, host TEXT NOT NULL,
            printer_id INTEGER, enabled INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(printer_id) REFERENCES printers(id))""")

def rows(table):
    with _conn() as c:
        return [dict(r) for r in c.execute(f"SELECT * FROM {table} ORDER BY id")]

def add_printer(name, kind, config):
    with _conn() as c:
        cur = c.execute("INSERT INTO printers(name,kind,config) VALUES(?,?,?)", (name, kind, json.dumps(config)))
        return cur.lastrowid

def add_bar(name, host, printer_id=None):
    with _conn() as c:
        cur = c.execute("INSERT INTO bars(name,host,printer_id) VALUES(?,?,?)", (name, host, printer_id))
        return cur.lastrowid

def delete_row(table, row_id):
    if table not in ("printers", "bars"):
        raise ValueError("bad table")
    with _conn() as c:
        c.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))

def update_bar_assignment(bar_id, printer_id):
    with _conn() as c:
        c.execute("UPDATE bars SET printer_id=? WHERE id=?", (printer_id, bar_id))
