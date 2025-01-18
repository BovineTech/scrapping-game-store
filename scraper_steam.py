import multiprocessing
import requests
import time
from utils import save_to_mongo, get_mongo_db, log_info, regions_steam
import os
from dotenv import load_dotenv

load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
n_processes=os.getenv("n_processes")

STEAM_API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

def fetch_steam_apps():
    response = requests.get(STEAM_API_URL, params={"key": STEAM_API_KEY})
    response.raise_for_status()
    return response.json()["applist"]["apps"]

def fetch_game_details(app_id, proxy):
    base_url = "https://store.steampowered.com/api/appdetails"
    try:
        response = requests.get(base_url, params={"appids": app_id, "l": "en", "key": STEAM_API_KEY})
        response.raise_for_status()
        data = response.json()

        if not str(app_id) in data or not data[str(app_id)]["success"]:
            return {"error": "Game details not available ------"}
        prices = {}
        game_data = data[str(app_id)]["data"]

        index = 0
        while index < len(regions_steam):
            region = regions_steam[index]
            try:
                response = requests.get(base_url, params={"appids": app_id, "cc": region, "l": "en", "key": STEAM_API_KEY}, timeout=10)
                response.raise_for_status()
                data = response.json()
                if str(app_id) in data and data[str(app_id)]["success"]:
                    price_info = data[str(app_id)]["data"].get("price_overview")
                    prices[region] = price_info["final_formatted"] if price_info else "Free or Not Available"
                else:
                    prices[region] = "Not Available"
                index += 1
            except Exception as e:
                print(f"Error fetching game details: {e}")
    except Exception as e:
        return {"error": f"Error fetching game details: {e}"}

    game_details = {
        "title": game_data.get("name", "N/A"),
        "categories": [category["description"] for category in game_data.get("categories", [])],
        "short_description": game_data.get("short_description", "N/A"),
        "full_description": game_data.get("detailed_description", "N/A"),
        "screenshots": [s["path_full"] for s in game_data.get("screenshots", [])],
        "header_image": game_data.get("header_image", "N/A"),
        "rating": game_data.get("metacritic", {}).get("score", "N/A"),
        "publisher": ", ".join(game_data.get("publishers", [])),
        "platforms": ", ".join([k for k, v in game_data.get("platforms", {}).items() if v]),
        "release_date": game_data.get("release_date", {}).get("date", "N/A"),
        "prices": prices
    }
    return game_details

def process_app_range(start_index, end_index, apps, db):
    count = 0
    for index in range(start_index, end_index):
        app = apps[index]
        proxy = my_proxies[index % 10]
        try:
            game_data = fetch_game_details(app["appid"], proxy)
            if "error" not in game_data:
                save_to_mongo(db, "steam_games", game_data)
                count += 1
                if count % 50 == 0:
                    log_info(f"Saved {count} Steam games in this process")
        except Exception as e:
            print(f"Error processing app {app['appid']}: {e}")

def main():
    apps = fetch_steam_apps()
    total_apps = len(apps)
    if total_apps == 0:
        log_info("No Steam apps found to process.")
        return

    db = get_mongo_db()

    # Divide apps into ranges for subprocesses
    chunk_size = (total_apps + n_processes - 1) // n_processes
    ranges = [
        (i * chunk_size, min((i + 1) * chunk_size - 1, total_apps))
        for i in range(n_processes)
    ]

    # Start subprocesses
    processes = []
    for start, end in ranges:
        process = multiprocessing.Process(target=process_app_range, args=(start, end, apps, db))
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()

    log_info("All processes completed.")

if __name__ == "__main__":
    main()
