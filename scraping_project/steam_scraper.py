import requests
import pymongo
import logging
import json

logging.basicConfig(level=logging.INFO)

STEAM_API_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

def scrape_steam_games(mongo_uri):
    client = pymongo.MongoClient(mongo_uri)
    db = client["test"]
    collection = db["steam_games"]

    response = requests.get(STEAM_API_URL)
    data = response.json()
    apps = data["applist"]["apps"]

    error_log = []

    for app in apps[:10]:  # Limit to 10 for demo purposes
        try:
            collection.insert_one(app)
            logging.info(f"Saved: {app['name']}")
        except Exception as e:
            error_msg = f"Error saving app: {e}"
            logging.error(error_msg)
            error_log.append({"app": app, "error": error_msg})

    with open("steam_error_log.json", "w") as log_file:
        json.dump(error_log, log_file, indent=4)