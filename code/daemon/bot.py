import time
from pubsub import pub
try:
    import meshtastic.serial_interface
    MESHTASTIC_AVAILABLE = True
except ImportError:
    MESHTASTIC_AVAILABLE = False
import re


SERIAL_PORT  = "/dev/ttyUSB0"
MAX_RESPONSE = 195  # max safe Meshtastic message length in bytes


def truncate(text: str) -> str:
    """Truncate response to fit Meshtastic packet size."""
    if len(text.encode("utf-8")) <= MAX_RESPONSE:
        return text
    while len(text.encode("utf-8")) > MAX_RESPONSE - 3:
        text = text[:-1]
    return text + "..."


def help_command() -> str:
    return "Cmds: !wx <lat> <lon> [days] | !fc <station> | !warn <state> | !help"


def wx_command(con, args) -> str:
    if len(args) < 2:
        return "Usage: !wx <lat> <lon> [days 1-7]"
    try:
        lat  = float(args[0])
        lon  = float(args[1])
        days = int(args[2]) if len(args) > 2 else 1
        days = max(1, min(days, 7))
    except ValueError:
        return "Invalid coordinates. Usage: !wx <lat> <lon> [days]"

    from datetime import datetime, timedelta
    cutoff  = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    rows    = con.execute("""
        SELECT station_id, lat, lon, raw_text
        FROM products
        WHERE product_type = 'metar'
          AND lat IS NOT NULL
          AND received_at > ?
        ORDER BY received_at DESC
    """, (cutoff,)).fetchall()

    if not rows:
        return "No recent observations available."

    # find nearest station by simple distance
    nearest = min(rows, key=lambda r: (r[1] - lat)**2 + (r[2] - lon)**2)
    dist_km = (((nearest[1] - lat)**2 + (nearest[2] - lon)**2) ** 0.5) * 111

    # parse key fields from raw METAR text
    import re
    obs     = ""
    for line in nearest[3].splitlines():
        if "METAR" in line or re.match(r'K[A-Z]{3}\s+\d{6}Z', line.strip()):
            import re
            temp = re.search(r'(\d{2})/\d{2}', line)
            wind = re.search(r'(\d{3})(\d{2})KT', line)
            sky  = re.search(r'(CLR|SKC|FEW|SCT|BKN|OVC)\d*', line)
            parts = []
            if temp:
                parts.append(f"{temp.group(1)}C")
            if wind:
                parts.append(f"Wind {wind.group(1)}@{wind.group(2)}kt")
            if sky:
                parts.append(sky.group(1))
            obs = " ".join(parts) if parts else line[:60]
            break

    result = f"{nearest[0]} ({dist_km:.0f}km): {obs}"

    if days > 1:
        from datetime import datetime, timedelta
        cutoff2  = (datetime.utcnow() - timedelta(hours=12)).isoformat()
        forecast = con.execute("""
            SELECT raw_text FROM products
            WHERE product_type = 'zone_forecast'
              AND state = (
                  SELECT state FROM products
                  WHERE station_id = ? LIMIT 1
              )
              AND received_at > ?
            ORDER BY received_at DESC LIMIT 1
        """, (nearest[0], cutoff2)).fetchone()

        if forecast:
            for line in forecast[0].splitlines():
                if any(kw in line for kw in ["TODAY","TONIGHT","TOMORROW"]):
                    result += f" | {line.strip()[:80]}"
                    break

    return truncate(result)


def fc_command(con, args) -> str:
    if not args:
        return "Usage: !fc <station>  e.g. !fc KAUS or !fc AUS"

    station = args[0].upper().strip()
    if len(station) == 3:
        station = "K" + station

    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(hours=12)).isoformat()

    state_row = con.execute("""
        SELECT state FROM products
        WHERE station_id = ? AND state IS NOT NULL
        ORDER BY received_at DESC LIMIT 1
    """, (station,)).fetchone()

    if not state_row:
        return f"No data for {station}."

    row = con.execute("""
        SELECT raw_text FROM products
        WHERE product_type = 'zone_forecast'
          AND state = ?
          AND received_at > ?
        ORDER BY received_at DESC LIMIT 1
    """, (state_row[0], cutoff)).fetchone()

    if not row:
        return f"No forecast for {station}."

    result = f"{station}: "
    count  = 0
    for line in row[0].splitlines():
        line = line.strip()
        if any(kw in line for kw in ["TODAY","TONIGHT","TOMORROW","THIS "]):
            result += line[:80] + " "
            count  += 1
            if count >= 2:
                break

    return truncate(result) if count else f"No forecast periods found for {station}."


def warn_command(con, args) -> str:
    if not args:
        return "Usage: !warn <state>  e.g. !warn TX"

    state = args[0].upper().strip()
    if len(state) != 2:
        return "Provide a 2-letter state code. e.g. !warn TX"

    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    rows   = con.execute("""
        SELECT product_type, raw_text FROM products
        WHERE state = ?
          AND product_type IN ('warning','watch','tornado','severe','flash_flood')
          AND received_at > ?
        ORDER BY received_at DESC LIMIT 3
    """, (state, cutoff)).fetchall()

    if not rows:
        return f"No active warnings for {state}."

    summaries = []
    for row in rows:
        for line in row[1].splitlines():
            line = line.strip()
            if len(line) > 10 and not line.isdigit() and not re.match(r'^[A-Z]{4}\d+', line):
                    summaries.append(f"[{row[0][:4].upper()}] {line[:50]}")
                    break

    return truncate(f"{state}: " + " | ".join(summaries))


def unrecognized_command() -> str:
    return "Unknown command. Try !help"


def parse_command(con, message: str) -> str:
    parts = message.strip().split()
    if not parts:
        return ""
    if not parts[0].startswith("!"):
        return ""

    command = parts[0].lower()
    args    = parts[1:]

    if command == "!help":
        return help_command()
    elif command == "!wx":
        return wx_command(con, args)
    elif command == "!fc":
        return fc_command(con, args)
    elif command == "!warn":
        return warn_command(con, args)
    else:
        return unrecognized_command()


def run_bot(con):
    """Connect to RAK4631 and listen for mesh messages."""
    if not MESHTASTIC_AVAILABLE:
        print("Meshtastic not available — run on Pi with RAK connected")
        return

    print(f"Connecting to {SERIAL_PORT}...")
    interface = meshtastic.serial_interface.SerialInterface(SERIAL_PORT)
    print("Connected. Listening for mesh messages...")

    def on_receive(packet, interface):
        try:
            if "decoded" not in packet:
                return
            if "text" not in packet["decoded"]:
                return
            message = packet["decoded"]["text"].strip()
            sender  = packet["from"]
            if not message.startswith("!"):
                return
            print(f"[{sender}] {message}")
            response = parse_command(con, message)
            if response:
                print(f"→ {response}")
                interface.sendText(response, destinationId=sender)
        except Exception as e:
            print(f"Error handling message: {e}")

    pub.subscribe(on_receive, "meshtastic.receive.text")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        interface.close()


if __name__ == "__main__":
    from db import init_db
    from ingest import ingest_new

    con = init_db("test.db")
    ingest_new(con, "mock_emwin")

    # test parse_command without hardware
    print(parse_command(con, "!help"))
    print(parse_command(con, "!warn TX"))
    print(parse_command(con, "!fc KAUS"))
    print(parse_command(con, "!banana"))
    print(parse_command(con, "!wx 30.26 -97.74"))