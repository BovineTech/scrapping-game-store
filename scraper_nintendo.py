import requests
import time
import re
import multiprocessing
from bs4 import BeautifulSoup
from utils import log_info, get_mongo_db, save_to_mongo, get_selenium_browser, search_game, regions_nintendo
import os
from dotenv import load_dotenv

load_dotenv()
n_processes = int(os.getenv("n_processes", 8))  # Default to 4 processes if not set

API_URL = "https://api.sampleapis.com/switch/games"  # API endpoint
JAPAN_URL = "https://www.nintendo.com/jp/software/switch/index.html?sftab=all"

def fetch_games():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Nintendo: Error fetching games: {e}")
        return []

def process_nintendo_game(browser, game):
    try:
        title = game.get("name", "N/A")
        categories = game.get("genre", [])
        publisher = game.get("publishers", ["N/A"])[0]
        release_date = game.get("releaseDates", {}).get('NorthAmerica', "N/A")

        sanitized_title = re.sub(r'[^a-z0-9 ]', '', title.replace("&", "and").lower()).replace(" ", "-")
        game_link = f"https://www.nintendo.com/us/store/products/{sanitized_title}-switch/"

        browser.get(game_link)
        soup = BeautifulSoup(browser.page_source, "html.parser")

        def safe_find(soup, selector, attr=None):
            element = soup.select_one(selector)
            return element[attr] if attr and element else (element.text.strip() if element else None)

        header_image = safe_find(soup, f'img[alt="{title} 1"]', 'src') or "No Game Header Image"
        rating = safe_find(soup, 'h3:contains("ESRB rating") + div a') or "No Rating"
        short_description = safe_find(soup, 'meta[name="description"]', 'content') or "No Short Description"
        platforms = safe_find(soup, 'div.sc-1i9d4nw-14.gxzajP span') or "No platform"
        screenshots = [img['src'] for img in soup.select('div.-fzAB.SUqIq img')] or []

        prices = {}
        tmp = soup.select_one('span.W990N.QS4uJ, div.o2BsP.QS4uJ')
        prices["us"] = tmp.text.split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATELY"

        # Brazil Price
        brazil_link = game_link.replace("/us/", "/pt-br/")
        browser.get(brazil_link)
        brazil_soup = BeautifulSoup(browser.page_source, 'html.parser')
        tmp = brazil_soup.select_one('span.W990N.QS4uJ, div.o2BsP.QS4uJ')
        prices['br'] = tmp.text.replace('\xa0', ' ').split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATELY"

        for region in regions_nintendo:
            region_url = game_link.replace("/us/", f"/{region}/")
            browser.get(region_url)
            region_soup = BeautifulSoup(browser.page_source, 'html.parser')
            tmp = region_soup.select_one('span.W990N.QS4uJ, div.o2BsP.QS4uJ')
            prices[region.split('-')[1]] = tmp.text.split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATELY"

        # Japan
        browser.get(JAPAN_URL)
        search_dom = 'input.nc3-c-search__boxText'
        result_dom = 'div.nc3-c-softCard__listItemPrice'
        soup = search_game(browser, search_dom, result_dom, title)
        prices['jp'] = safe_find(soup, 'div.nc3-c-softCard__listItemPrice') or "NOT AVAILABLE SEPARATELY"

        return {
            "title": title,
            "categories": categories,
            "short_description": short_description,
            "full_description": [],
            "screenshots": screenshots,
            "header_image": header_image,
            "rating": rating,
            "publisher": publisher,
            "platforms": platforms,
            "release_date": release_date,
            "prices": prices
        }
    except Exception as e:
        print(f"Nintendo: Error processing game: {e}")
        return {}

def process_games_range(start_index, end_index, games):
    log_info(f"Processing games from index {start_index} to {end_index}")
    db = get_mongo_db()
    browser = get_selenium_browser()

    for index in range(start_index, end_index):
        try:
            game_data = process_nintendo_game(browser, games[index])
            if game_data:
                save_to_mongo(db, "nintendo_games", game_data)
                if (index - start_index + 1) % 50 == 0:
                    log_info(f"Saved {start_index} ~ {index} Nintendo games in this process")
        except Exception as e:
            print(f"Error processing game at index {index}: {e}")

    browser.quit()

def main():
    log_info("Waiting for fetching Nintendo games...")
    games = fetch_games()

    total_games = len(games)
    if total_games == 0:
        log_info("No games found to process.")
        return

    chunk_size = (total_games + n_processes - 1) // n_processes
    ranges = [
        (i * chunk_size, min((i + 1) * chunk_size, total_games))
        for i in range(n_processes)
    ]

    processes = []
    for start, end in ranges:
        process = multiprocessing.Process(target=process_games_range, args=(start, end, games))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    log_info("All processes completed.")

if __name__ == "__main__":
    main()
