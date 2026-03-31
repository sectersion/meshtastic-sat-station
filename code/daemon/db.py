import sqlite3
from datetime import datetime, timedelta


def init_db(path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at  TEXT NOT NULL,
            product_id   TEXT NOT NULL,
            station_id   TEXT,
            state        TEXT,
            lat          REAL,
            lon          REAL,
            product_type TEXT NOT NULL,
            raw_text     TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ingested_files (
            filename    TEXT PRIMARY KEY,
            ingested_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS system_state (
            key        TEXT PRIMARY KEY,
            value      TEXT,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_type     ON products(product_type);
        CREATE INDEX IF NOT EXISTS idx_station  ON products(station_id);
        CREATE INDEX IF NOT EXISTS idx_state    ON products(state);
        CREATE INDEX IF NOT EXISTS idx_received ON products(received_at);
    """)
    con.commit()
    return con

def purge_old(con, days=7):
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    con.execute("DELETE FROM products WHERE received_at < ?", (cutoff,))
    con.commit()

def set_state(con, key, value):
    now = datetime.utcnow().isoformat()
    con.execute("""
        INSERT INTO system_state (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
    """, (key, value, now))
    con.commit()

def get_state(con, key):
    row = con.execute("SELECT value FROM system_state WHERE key = ?", (key,)).fetchone()
    if row is None:
        return None
    return row[0]


