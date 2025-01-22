from bs4 import BeautifulSoup
from utils import (
    get_mongo_db, save_to_mongo, get_selenium_browser, log_info,
    click_loadmore_btn, regions_xbox
)
import multiprocessing
import requests
import itertools
from requests.adapters import HTTPAdapter

n_processes = 100
XBOX_URL = "https://www.xbox.com/en-US/games/browse"

# Load proxies from file
with open("proxies.txt") as f:
    PROXIES = [line.strip() for line in f if line.strip()]
proxy_pool = itertools.cycle(PROXIES)  # Efficient round-robin proxy cycling

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.xbox.com/",
    "Connection": "keep-alive",
}

def create_session(proxy_list):
    proxy = next(itertools.cycle(proxy_list))
    session = requests.Session()
    session.proxies = {"http": proxy, "https": proxy}
    session.headers.update(HEADERS)
    session.mount('https://', HTTPAdapter(max_retries=3))
    return session

def fetch_xbox_games():
    try:
        browser = get_selenium_browser()
        browser.get(XBOX_URL)
        browser = click_loadmore_btn(browser, '//button[contains(@aria-label, "Load more")]')
        soup = BeautifulSoup(browser.page_source, "html.parser")
        browser.quit()
        return soup.find_all('div', class_='ProductCard-module__cardWrapper___6Ls86 shadow')
    except Exception as e:
        print(f"Error fetching Xbox game list: {e}")
        return []

def safe_find(soup, tag, css_class=None, attr=None):
    element = soup.find(tag, class_=css_class) if css_class else soup.find(tag)
    if attr:
        return element[attr] if element else None
    return element.text.strip() if element else "N/A"

def fetch_price_for_region(details_link, region, proxy_list):
    try:
        region_url = details_link.replace("en-US", region)
        session = create_session(proxy_list)
        response = session.get(region_url, timeout=10)
        response.raise_for_status()
        price_soup = BeautifulSoup(response.content, 'html.parser')
        price_element = safe_find(price_soup, 'span', "Price-module__boldText___1i2Li")
        return price_element or "BUNDLE NOT AVAILABLE"
    except requests.RequestException as e:
        print(f"Error fetching price for region {region}: {e}")
        return "BUNDLE NOT AVAILABLE"

def process_xbox_game(browser, game, proxy_list):
    try:
        details_link = game.find('a', href=True)['href']
        browser.get(details_link)
        details_soup = BeautifulSoup(browser.page_source, 'html.parser')

        title = safe_find(details_soup, 'h1', "typography-module__xdsH1___7oFBA") or "No Title"
        category_rating_text = safe_find(details_soup, 'span', "ProductInfoLine-module__textInfo___jOZ96")
        categories = category_rating_text.split("•") if category_rating_text else []
        rating = categories.pop() if categories and categories[-1].endswith('K') else "Not Rated"
        short_description = safe_find(details_soup, 'meta', attr='content') or "No Description"
        full_description = safe_find(details_soup, 'p', "Description-module__description___ylcn4") or "No Description"
        screenshots = [img['src'] for img in details_soup.select('section[aria-label="Gallery"] img')] or []
        header_image = safe_find(details_soup, 'img', "ProductDetailsHeader-module__productImage___QK3JA", 'src') or "No Image"
        publisher = safe_find(details_soup, 'div', "typography-module__xdsBody2___RNdGY") or "No Publisher"
        platforms = [item.text.strip() for item in details_soup.select('ul.FeaturesList-module__wrapper___KIw42 li')] or ["No Platforms"]
        release_date = safe_find(details_soup, 'div', "typography-module__xdsBody2___RNdGY") or "No Release Date"

        prices = {"us": safe_find(details_soup, 'span', "Price-module__boldText___1i2Li") or "BUNDLE NOT AVAILABLE"}
        prices.update({region.split('-')[1]: fetch_price_for_region(details_link, region, proxy_list) for region in regions_xbox})

        return {
            "title": title,
            "categories": categories,
            "short_description": short_description,
            "full_description": full_description,
            "screenshots": screenshots,
            "header_image": header_image,
            "rating": rating,
            "publisher": publisher,
            "platforms": platforms,
            "release_date": release_date,
            "prices": prices,
        }
    except Exception as e:
        print(f"Error processing game details: {e}")
        return None

def process_games_range(start_index, end_index, games, proxy_list):
    db = get_mongo_db()
    browser = get_selenium_browser()

    for index in range(start_index, end_index):
        try:
            game_data = process_xbox_game(browser, games[index], proxy_list)
            if game_data:
                save_to_mongo(db, "xbox_games", game_data)
        except Exception as e:
            print(f"Error processing Xbox game at index {index}: {e}")
    browser.quit()

def main():
    log_info("Waiting for fetching Xbox games...")
    games = fetch_xbox_games()

    total_games = len(games)
    if total_games == 0:
        log_info("No games found to process.")
        return

    log_info(f"Found {total_games} games in Xbox.")
    chunk_size = (total_games + n_processes - 1) // n_processes
    ranges = [(i * chunk_size, min((i + 1) * chunk_size, total_games)) for i in range(n_processes)]
    proxy_list = list(itertools.islice(proxy_pool, n_processes))  # Get unique proxies for each process

    with multiprocessing.Pool(processes=n_processes) as pool:
        pool.starmap(process_games_range, [(start, end, games, proxy_list[i]) for i, (start, end) in enumerate(ranges)])

    log_info("All Xbox processes completed.")

if __name__ == "__main__":
    main()
