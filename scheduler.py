import time
import os
import platform
import subprocess
from concurrent.futures import ThreadPoolExecutor
from utils import log_info, log_error

SCRAPER_INTERVALS = {
    "scraper_steam.py": 10,  # Run every 10 seconds
    "scraper_nintendo.py": 15,  # Run every 15 seconds
    "scraper_playstation.py": 20,  # Run every 20 seconds
    "scraper_xbox.py": 25,  # Run every 25 seconds
}

def run_scraper(scraper, interval):
    while True:
        try:
            log_info(f"========== Starting {scraper}... ==========")

            if platform.system() == "Windows":
                # On Windows, use CREATE_NEW_PROCESS_GROUP
                proc = subprocess.Popen(
                    ["python", scraper],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # On Unix-based systems, use os.setsid()
                proc = subprocess.Popen(
                    ["python3", scraper],  # Use "python3" on Ubuntu
                    preexec_fn=os.setsid
                )

            log_info(f"Process {scraper} started with PID {proc.pid}")

            # Wait for the process to finish
            proc.wait()

            log_info(f"========== Finished {scraper} and Updated db. ==========")

        except Exception as e:
            log_error(f"Error running {scraper}: {e}")
            time.sleep(300)

        # Wait for the interval before restarting the scraper
        time.sleep(interval)

def main():
    with ThreadPoolExecutor() as executor:
        for scraper, interval in SCRAPER_INTERVALS.items():
            executor.submit(run_scraper, scraper, interval)

if __name__ == "__main__":
    main()
