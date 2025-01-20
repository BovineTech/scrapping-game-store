import multiprocessing
import requests
from requests.adapters import Retry, HTTPAdapter
from utils import save_to_mongo, get_mongo_db, log_info, regions_steam
from dotenv import load_dotenv
import itertools

load_dotenv()
# STEAM_API_KEY = os.getenv("STEAM_API_KEY")
n_processes = 32  # Set to 32 subprocesses
STEAM_API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

# Load proxies from a file
PROXIES = [line.strip() for line in open("proxies.txt") if line.strip()]
proxy_pool = itertools.cycle(PROXIES)  # Round-robin proxy cycling

# Set up a session with retries and connection pooling
def create_session(proxy):
    session = requests.Session()
    retries = Retry(
        total=5, 
        backoff_factor=1, 
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    # Assign a proxy to the session
    session.proxies = {"http": proxy, "https": proxy}
    return session

def fetch_steam_apps(session):
    response = session.get(STEAM_API_URL)
    response.raise_for_status()
    return response.json()["applist"]["apps"]

def fetch_game_details(app_id, session):
    base_url = "https://store.steampowered.com/api/appdetails"
    try:
        response = session.get(base_url, params={"appids": app_id, "l": "en"})
        response.raise_for_status()
        data = response.json()

        if not str(app_id) in data or not data[str(app_id)]["success"]:
            return {"error": "Game details not available"}

        prices = {}
        game_data = data[str(app_id)]["data"]

        # Fetch region prices concurrently
        price_requests = []
        for region in regions_steam:
            price_requests.append(fetch_price_for_region(app_id, region, session))

        # Aggregate region prices
        price_responses = [price_request for price_request in price_requests]
        for region, price_info in price_responses:
            prices[region] = price_info if price_info else "Not Available"

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
    except Exception as e:
        return {"error": f"Error fetching game details: {e}"}

def fetch_price_for_region(app_id, region, session):
    base_url = "https://store.steampowered.com/api/appdetails"
    try:
        response = session.get(base_url, params={"appids": app_id, "cc": region, "l": "en"}, timeout=10)
        response.raise_for_status()
        data = response.json()
        if str(app_id) in data and data[str(app_id)]["success"]:
            price_info = data[str(app_id)]["data"].get("price_overview")
            return region, price_info["final_formatted"] if price_info else "Free or Not Available"
        else:
            return region, "Not Available"
    except Exception as e:
        log_info(f"Error fetching price for region {region}: {e}")
        return region, None

def process_apps_range(start_index, end_index, apps, proxy):
    session = create_session(proxy)  # Assign a proxy to the session
    db = get_mongo_db()  # Create DB connection within each subprocess
    log_info(f"Processing games from index {start_index} to {end_index} using proxy {proxy}")
    count = 0

    for index in range(start_index, end_index):
        app = apps[index]
        try:
            game_data = fetch_game_details(app["appid"], session)
            if "error" not in game_data:
                save_to_mongo(db, "steam_games", game_data)
                if count % 200 == 0:
                    log_info(f"Saved {start_index} ~ {end_index} Steam games in this process")
            count += 1
        except Exception as e:
            print(f"Error processing app {app['appid']}: {e}")

def main():
    proxy_list = list(itertools.islice(proxy_pool, n_processes))  # Get unique proxies for each process

    apps = fetch_steam_apps(create_session(next(proxy_pool)))  # Initial fetch using a proxy
    total_apps = len(apps)
    if total_apps == 0:
        log_info("No Steam apps found to process.")
        return

    # Divide apps into ranges for subprocesses
    chunk_size = (total_apps + n_processes - 1) // n_processes
    ranges = [(i * chunk_size, min((i + 1) * chunk_size, total_apps)) for i in range(n_processes)]

    # Use Pool to manage processes efficiently with round-robin proxies
    with multiprocessing.Pool(processes=n_processes) as pool:
        pool.starmap(process_apps_range, [(start, end, apps, proxy_list[i]) for i, (start, end) in enumerate(ranges)])

    log_info("All processes completed.")

if __name__ == "__main__":
    main()
