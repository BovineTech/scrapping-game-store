from bs4 import BeautifulSoup
import requests
import pymongo
import logging
import json

logging.basicConfig(level=logging.INFO)

def scrape_playstation_games(mongo_uri):
    client = pymongo.MongoClient(mongo_uri)
    db = client["test"]
    collection = db["playstation_games"]

    url = "https://store.playstation.com/en-us/pages/browse/1"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    games = soup.find_all('a', href=True)

    error_log = []

    for game in games:
        try:
            title = game.text.strip()
            collection.insert_one({"title": title})
            logging.info(f"Saved: {title}")
        except Exception as e:
            error_msg = f"Error saving game: {e}"
            logging.error(error_msg)
            error_log.append({"game": game, "error": error_msg})

    with open("playstation_error_log.json", "w") as log_file:
        json.dump(error_log, log_file, indent=4)