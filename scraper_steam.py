import requests
import time
from utils import save_to_mongo, get_mongo_db, log_info, regions_steam, my_proxies

STEAM_API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

def fetch_steam_apps():
    response = requests.get(STEAM_API_URL)
    response.raise_for_status()
    return response.json()["applist"]["apps"]

def fetch_game_details(app_id, proxy):
    base_url = "https://store.steampowered.com/api/appdetails"
    try:
        response = requests.get(base_url, params={"appids": app_id, "l": "en"}, proxies=proxy, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not str(app_id) in data or not data[str(app_id)]["success"]:
            return {"error": "Game details not available ------"}
        prices = {}
        game_data = data[str(app_id)]["data"]
        
        index = 0
        # for region in regions_steam:
        while index < len(regions_steam):
            region = regions_steam[index]
            try:
                response = requests.get(base_url, params={"appids": app_id, "cc": region, "l": "en"}, proxies=my_proxies[index % 10], timeout=10)
                response.raise_for_status()
                data = response.json()
                if str(app_id) in data and data[str(app_id)]["success"]:
                    price_info = data[str(app_id)]["data"].get("price_overview")
                    prices[region] = price_info["final_formatted"] if price_info else "Free or Not Available"
                else:
                    prices[region] = "Not Available"
                index += 1
            except Exception as e:
                print("Steam : ", app_id, f"------too many requests : {my_proxies[index % 10]} : waiting for server")
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

def main():
    apps = fetch_steam_apps()
    db = get_mongo_db()

    index = 0
    while index < len(apps):
        app = apps[index]
        proxy = my_proxies[index % 10]
        game_data = fetch_game_details(app["appid"], proxy)
        if "error" in game_data:
            if "429" in game_data['error']:
                # time.sleep(60)
                print(app['appid'], f"------too many requests : {proxy} : waiting for server")
                continue
            else: print("Steam : ", app['appid'], "------",game_data["error"])
        else:
            save_to_mongo(db, "steam_games", game_data)
            log_info(f"Saved Steam game {index+1}: {game_data['title']}")
            print(f"Saved Steam game: {game_data['title']}")
        index += 1

if __name__ == "__main__":
    main()