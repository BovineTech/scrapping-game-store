from scraping_utils import setup_selenium_driver
from bs4 import BeautifulSoup
import pymongo
import logging
import json

logging.basicConfig(level=logging.INFO)

def scrape_xbox_games(mongo_uri, chrome_driver_path):
    client = pymongo.MongoClient(mongo_uri)
    db = client["test"]
    collection = db["xbox_games"]

    driver = setup_selenium_driver(chrome_driver_path)
    url = "https://www.xbox.com/en-US/games/browse"
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    games = soup.find_all('div', class_='ProductCard-module__cardWrapper___6Ls86')

    error_log = []

    for game in games:
        try:
            title = game.find('h1').text.strip()
            collection.insert_one({"title": title})
            logging.info(f"Saved: {title}")
        except Exception as e:
            error_msg = f"Error saving game: {e}"
            logging.error(error_msg)
            error_log.append({"game": game, "error": error_msg})
    driver.quit()

    with open("xbox_error_log.json", "w") as log_file:
        json.dump(error_log, log_file, indent=4)