import schedule
import time
import subprocess
import logging
from utils import update_mongo, get_mongo_db

SCRAPERS = [
    "scraper_steam.py",
    "scraper_nintendo.py",
    "scraper_playstation.py",
    "scraper_xbox.py",
]

# Configure logging
logging.basicConfig(
    filename="scraper.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

def log_info(message):
    logging.info(message)
    print(message)

def log_error(message):
    logging.error(message)
    print(message)

def run_scrapers():
    for scraper in SCRAPERS:
        try:
            log_info(f"========== Starting {scraper}... ==========")
            subprocess.run(["python", scraper], check=True)
            db = get_mongo_db()
            update_mongo(db, scraper)
            log_info(f"========== Successfully ran {scraper} and Updated db. ==========")
        except Exception as e:
            log_error(f"Error running {scraper}: {e}")

def main():
    schedule.every(1).seconds.do(run_scrapers)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()