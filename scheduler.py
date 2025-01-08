import schedule
import time
import subprocess
from utils import update_mongo, get_mongo_db

SCRAPERS = [
    "scraper_steam.py",
    "scraper_nintendo.py",
    "scraper_playstation.py",
    "scraper_xbox.py",
]

def run_scrapers():
    for scraper in SCRAPERS:
        try:
            print(f"========== Starting {scraper}... ==========")
            subprocess.run(["python", scraper], check=True)
            print(f"========== Successfully ran {scraper}. ==========")
            db = get_mongo_db()
            update_mongo(db, scraper)
        except Exception as e:
            print(f"Error running {scraper}: {e}")

def main():
    schedule.every(1).seconds.do(run_scrapers)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()