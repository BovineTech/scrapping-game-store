import requests
from pymongo import MongoClient

from dotenv import load_dotenv
import os
import time

# MongoDB setup
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["test"]
collection = db["steam_games1"]
STEAM_API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

regions = [
        "us",  # United States
        "gb",  # United Kingdom
        "eu",  # European Union
        "jp",  # Japan
        "in",  # India
        "br",  # Brazil
        "au",  # Australia
        "ca",  # Canada
        "ru",  # Russia
        "cn",  # China
        "kr",  # South Korea
        "mx",  # Mexico
        "za",  # South Africa
        "ar",  # Argentina
        "tr",  # Turkey
        "id",  # Indonesia
        "sg",  # Singapore
        "ph",  # Philippines
        "th",  # Thailand
        "my",  # Malaysia
        "nz",  # New Zealand
        "sa",  # Saudi Arabia
        "ae",  # United Arab Emirates
    ]

def get_app_list():    
    try:
        response = requests.get(STEAM_API_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        
        if "applist" in data and "apps" in data["applist"]:
            return data["applist"]["apps"]
        else:
            print("No app data found in response.")
            return []   
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []

def get_game_details(app_id):
    base_url = "https://store.steampowered.com/api/appdetails"
    game_details = {}
    prices = {}

    try:
        response = requests.get(base_url, params={"appids": app_id, "l": "en"})
        response.raise_for_status()
        data = response.json()
        
        if str(app_id) in data and data[str(app_id)]["success"]:
            game_data = data[str(app_id)]["data"]
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
            }
        else:
            return {"error": "Game details not available ------"}
    except Exception as e:
        return {"error": f"Error fetching game details: {e}"}
    for region in regions:
        try:
            response = requests.get(base_url, params={"appids": app_id, "cc": region, "l": "en"})
            response.raise_for_status()
            data = response.json()

            if str(app_id) in data and data[str(app_id)]["success"]:
                price_info = data[str(app_id)]["data"].get("price_overview")
                prices[region] = price_info["final_formatted"] if price_info else "Free or Not Available"
            else:
                prices[region] = "Not Available"
        except Exception as e:
            prices[region] = f"Error: {e}"

    game_details["prices"] = prices
    return game_details

def save_to_mongo(game_details):
    try:
        collection.insert_one(game_details)
        # print(f"-----------Game '{game_details['title']}' saved to MongoDB!--------------")
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")

if __name__ == "__main__":
    appid_list = get_app_list()
    index = 0

    tmp_count = 0
    while index < len(appid_list):
        game_details = get_game_details(appid_list[index]['appid'])
        if "error" in game_details:
            if "429" in game_details['error']:
                time.sleep(5)
                print(appid_list[index]['appid'], "------too many requests : sleep 5s")
            else: print(appid_list[index]['appid'], "------",game_details["error"])
        else:
            print(appid_list[index]['appid'], f"------'{game_details['title']}':saved to MongoDB")
            save_to_mongo(game_details)
            tmp_count += 1
            if tmp_count == 5: break
        index += 1
