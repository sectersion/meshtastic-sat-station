import threading
import time
import argparse
from db import init_db
from ingest import ingest_new
from bot import run_bot
import logging
from pathlib import Path

DB_PATH    = Path("weather.db")
EMWIN_PATH = Path("/var/lib/goestools/emwin")
MOCK_PATH  = Path("mock_emwin")   

logger = logging.getLogger(__name__)

def config():
    if DB_PATH.is_file():
        logger.info("DB Found")
    else:
        logger.warning("DB not found")
    
    if EMWIN_PATH.is_file():
        logger.info("EMWIN path found.")
    else:
        logger.warning("EMWIN path not found. Make sure it exists.")



def ingest_loop(con, emwin_path):
    while True:
        ingest_new(con, emwin_path)
        logger.info("Ingested new EMWIN data.")
        time.sleep(60)

def main():
    logging.basicConfig(filename='sat.log', level=logging.ERROR)
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    emwin_path = MOCK_PATH if args.mock else EMWIN_PATH

    con = init_db(DB_PATH)
    logger.info("DB Initialized")
    # ingest thread
    t = threading.Thread(target=ingest_loop, args=(con, emwin_path), daemon=True)
    t.start()
    logger.info("Started ingest thread")
    # bot (blocking — runs on main thread)
    try:
        run_bot(con)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()