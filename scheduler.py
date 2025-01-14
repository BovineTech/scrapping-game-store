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

processes = []  # List to store subprocess references

def run_scraper(scraper):
    try:
        log_info(f"========== Starting {scraper}... ==========")

        if platform.system() == "Windows":
            # On Windows, use CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(
                ["python", scraper],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP  # Only for Windows
            )
        else:
            # On Unix-based systems, use os.setsid() to start the process in a new session
            proc = subprocess.Popen(
                ["python", scraper],
                preexec_fn=os.setsid  # Start process in its own group (Unix/Linux)
            )

        log_info(f"Process {scraper} started with PID {proc.pid}")

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
