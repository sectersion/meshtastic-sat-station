import re
from db import init_db, purge_old
from datetime import datetime
from pathlib import Path


STATION_COORDS = {
    "KAUS": (30.18, -97.68, "TX"),
    "KDFW": (32.90, -97.04, "TX"),
    "KIAH": (29.98, -95.34, "TX"),
    "KSAT": (29.53, -98.47, "TX"),
    "KHOU": (29.64, -95.27, "TX"),
    "KDAL": (32.85, -96.85, "TX"),
    "KSGR": (29.62, -95.65, "TX"),
    "KAMA": (35.22, -101.71, "TX"),
    "KELP": (31.81, -106.38, "TX"),
    "KCRP": (27.77, -97.51, "TX"),
}

PRODUCT_TYPES = {
    "SA": "metar",
    "ZF": "zone_forecast",
    "WW": "watch",
    "WS": "warning",
    "TO": "tornado",
    "SV": "severe",
    "FF": "flash_flood",
}

test_metar = """SAUS70 KAWN 201755
METAR KAUS 201753Z 18012KT 10SM FEW040 28/18 A2992
RMK AO2 SLP132 T02780178"""

test_forecast = """ZFTX 201730
TXZ192-211000-
CENTRAL TEXAS
TODAY: MOSTLY SUNNY. HIGH NEAR 31."""

test_warning = """WWUS30 KWNS 201800
WW 412
SEVERE THUNDERSTORM WATCH 412 REMAINS VALID UNTIL 200Z
FOR PARTS OF NORTH AND CENTRAL TEXAS"""

def parse_product(text) -> dict:
    #get product type
    lines = text.strip().splitlines()
    first_line = lines[0]
    first_word = first_line.split()[0]
    prefix = first_word[:2].upper()
    product_type = PRODUCT_TYPES.get(prefix, "other")

    body = '\n'.join(lines[1:])

    #get station id
    station_match = re.search(r'\bK[A-Z]{3}\b', body[:200])
    if station_match:
        station_id = station_match.group(0)
    else:
        station_id = None

    #get state
    state_match = re.search(r'\b([A-Z]{2})Z\d{3}\b', body[:500])
    if state_match:
        state = state_match.group(1)
    else:
        state = None

    #return parsed data
    return {
        "product_id":   first_word,
        "station_id":   station_id,
        "state":        state,
        "lat":          None,
        "lon":          None,
        "product_type": product_type,
    }


def already_ingested(con, filename):
    row = con.execute("SELECT 1 FROM ingested_files WHERE filename = ?", (filename,)).fetchone()
    if row is None:
        return False
    return True


def mark_ingested(con, filename):
    con.execute("INSERT INTO ingested_files (filename, ingested_at) VALUES (?, ?)", (filename, datetime.utcnow().isoformat()))

def ingest_new(con, emwin_path):
    path = Path(emwin_path)
    if not path.exists():
        print(f"Warning: EMWIN path not found: {emwin_path}")
        return

    for filepath in path.glob("**/*.txt"):
        filename = str(filepath)
        if already_ingested(con, filename):
            continue   # skip to next file
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
            meta = parse_product(text)
            if meta["station_id"] in STATION_COORDS:
               meta["lat"], meta["lon"], meta["state"] = STATION_COORDS[meta["station_id"]]
            con.execute("""
                INSERT INTO products
                    (received_at, product_id, station_id, state, lat, lon, product_type, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                meta["product_id"],
                meta["station_id"],
                meta["state"],
                meta["lat"],
                meta["lon"],
                meta["product_type"],
                text[:4000],
            ))
            mark_ingested(con, filename)
        except Exception as e:
            print(f"Failed to ingest {filepath}: {e}")

    con.commit()
    purge_old(con)
    




if __name__ == "__main__":
    from db import init_db
    con = init_db("test.db")

    # first run — should ingest all 3 files
    print("--- first run ---")
    ingest_new(con, "mock_emwin")

    rows = con.execute("SELECT product_id, product_type, station_id FROM products").fetchall()
    for row in rows:
        print(row[0], row[1], row[2])

    # second run — should skip all 3 files (already ingested)
    print("--- second run (should skip everything) ---")
    ingest_new(con, "mock_emwin")

    rows = con.execute("SELECT COUNT(*) FROM products").fetchone()
    print(f"Total rows in products: {rows[0]}")  # should still be 3, not 6

    # test missing path
    print("--- missing path ---")
    ingest_new(con, "does_not_exist")

    con.close()
