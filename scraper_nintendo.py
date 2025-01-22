import requests
import re
import multiprocessing
from bs4 import BeautifulSoup
from utils import (
    log_info, get_mongo_db, save_to_mongo, 
    get_selenium_browser, search_game, regions_nintendo
)
import warnings

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning)

n_processes = 16  # Adjust based on system performance

API_URL = "https://api.sampleapis.com/switch/games"
JAPAN_URL = "https://www.nintendo.com/jp/software/switch/index.html?sftab=all"
HEADERS = {"User-Agent": "Mozilla/5.0"}  # Add headers to prevent bot detection


def fetch_games():
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Nintendo : Error fetching games: {e}")
        return []
    
def safe_find(soup, selector, attr=None):
    if not soup or not selector:
        print(f"Error: Invalid arguments passed to safe_find: soup={soup}, selector={selector}")
        return "N/A"

    if isinstance(soup, list):
        soup = soup[0] if soup else None

    element = soup.select_one(selector) if soup else None
    if not element:
        return "N/A"

    return element.get(attr, element.text.strip()) if attr else element.text.strip()


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

        if not soup:
            print(f"Error: Unable to load page content for {title}")
            return None

        header_image = safe_find(soup.find('img', {'alt': f'{title} 1'}), 'src') or "No Image"
        rating = safe_find(soup, 'h3:-soup-contains("ESRB rating") + div a') or "No Rating"
        short_description = safe_find(soup, 'meta[name="description"]', 'content') or "No Description"
        platforms = safe_find(soup.find('div', class_='sc-1i9d4nw-14 gxzajP span')) or "Unknown"
        screenshots_list = soup.select('div.-fzAB.SUqIq img')
        screenshots = [img['src'] for img in screenshots_list] if screenshots_list else []

        prices = {}
        tmp = safe_find(soup, 'span.W990N.QS4uJ, div.o2BsP.QS4uJ')
        prices["us"] = tmp.split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATELY"

        # Brazil Price
        brazil_link = game_link.replace("/us/", "/pt-br/")
        browser.get(brazil_link)
        brazil_soup = BeautifulSoup(browser.page_source, 'html.parser')
        tmp = safe_find(brazil_soup, 'span.W990N.QS4uJ, div.o2BsP.QS4uJ')
        prices['br'] = tmp.replace('\xa0', ' ').split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATELY"

        for region in regions_nintendo:
            region_url = game_link.replace("/us/", f"/{region}/")
            browser.get(region_url)
            region_soup = BeautifulSoup(browser.page_source, 'html.parser')
            tmp = safe_find(region_soup, 'span.W990N.QS4uJ, div.o2BsP.QS4uJ')
            prices[region.split('-')[1]] = tmp.split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATELY"

        # Fetch Japan Price
        browser.get(JAPAN_URL)
        search_dom = 'input.nc3-c-search__boxText'
        result_dom = 'div.nc3-c-softCard__listItemPrice'
        japan_soup = search_game(browser, search_dom, result_dom, title)
        prices['jp'] = safe_find(japan_soup, 'div.nc3-c-softCard__listItemPrice') or "NOT AVAILABLE SEPARATELY"

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
            "prices": prices,
        }
    except Exception as e:
        print(f"Error processing game {title}: {e}")
        return None

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
    log_info("Fetching Nintendo games...")
    games = fetch_games()

    total_games = len(games)
    if total_games == 0:
        log_info("No games found to process.")
        return

    log_info(f"Found {total_games} games in Nintendo.")
    chunk_size = (total_games + n_processes - 1) // n_processes
    ranges = [(i * chunk_size, min((i + 1) * chunk_size, total_games)) for i in range(n_processes)]

    with multiprocessing.Pool(processes=n_processes) as pool:
        pool.starmap(process_games_range, [(start, end, games) for start, end in ranges])

    log_info("All processes completed.")

if __name__ == "__main__":
    main()
