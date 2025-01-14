import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
from utils import get_mongo_db, log_info, log_error

SCRAPER_INTERVALS = {
    "scraper_steam.py": 10,  # Run every 10 seconds
    "scraper_nintendo.py": 15,  # Run every 15 seconds
    "scraper_playstation.py": 20,  # Run every 20 seconds
    "scraper_xbox.py": 25,  # Run every 25 seconds
}

def run_scraper(scraper):
    try:
        log_info(f"========== Starting {scraper}... ==========")
        subprocess.run(["python", scraper], check=True)
        log_info(f"========== Finished {scraper} and Updated db. ==========")
    except Exception as e:
        log_error(f"Error running {scraper}: {e}")

def main():
    with ThreadPoolExecutor() as executor:
        while True:
            futures = []
            for scraper, interval in SCRAPER_INTERVALS.items():
                futures.append((scraper, executor.submit(run_scraper, scraper), interval))

            for scraper, future, interval in futures:
                future.result()  # Wait for the scraper to finish
                log_info(f"Waiting {interval} seconds before running {scraper} again...")
                time.sleep(interval)  # Wait for the specified interval before the next iteration

if __name__ == "__main__":
    main()