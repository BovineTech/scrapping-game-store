import time
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from utils import log_info, log_error

SCRAPER_INTERVALS = {
    "scraper_steam.py": 10,  # Run every 10 seconds
    "scraper_nintendo.py": 15,  # Run every 15 seconds
    "scraper_playstation.py": 20,  # Run every 20 seconds
    "scraper_xbox.py": 25,  # Run every 25 seconds
}

processes = []  # List to store subprocess references

def run_scraper(scraper):
    try:
        log_info(f"========== Starting {scraper}... ==========")
        # Use CREATE_NEW_PROCESS_GROUP for Windows
        proc = subprocess.Popen(
            ["python", scraper],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        processes.append(proc)  # Add to the list of subprocesses
        proc.wait()  # Wait for the process to finish
        log_info(f"========== Finished {scraper} and Updated db. ==========")
    except Exception as e:
        log_error(f"Error running {scraper}: {e}")

def main():
    with ThreadPoolExecutor() as executor:
        while True:
            futures = []
            for scraper, interval in SCRAPER_INTERVALS.items():
                futures.append(executor.submit(run_scraper, scraper))
                time.sleep(interval)  # Delay before starting the next scraper

if __name__ == "__main__":
    main()
