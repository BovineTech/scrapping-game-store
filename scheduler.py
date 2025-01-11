import schedule
import time
import subprocess
from utils import update_mongo, get_mongo_db, initialize_mongo, log_info, log_error

SCRAPERS = [
    "scraper_steam.py",
    "scraper_nintendo.py",
    "scraper_playstation.py",
    "scraper_xbox.py",
]

def run_scrapers():
    for scraper in SCRAPERS:
        try:
            log_info(f"========== Starting {scraper}... ==========")
            db = get_mongo_db()
            initialize_mongo(db, scraper)
            subprocess.run(["python", scraper], check=True)
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