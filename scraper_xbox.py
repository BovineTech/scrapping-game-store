from bs4 import BeautifulSoup
from utils import get_mongo_db, save_to_mongo, get_selenium_browser, log_info, click_loadmore_btn, regions_xbox
import time
import multiprocessing
import os
from dotenv import load_dotenv

load_dotenv()
n_processes = int(os.getenv("n_processes", 8))  # Default to 8 if not set
XBOX_URL = "https://www.xbox.com/en-US/games/browse"

def fetch_xbox_games():
    browser = get_selenium_browser()
    browser = click_loadmore_btn(browser, '//button[contains(@aria-label, "Load more")]')
    soup = BeautifulSoup(browser.page_source, "html.parser")
    browser.quit()
    return soup.find_all('div', class_='ProductCard-module__cardWrapper___6Ls86 shadow')

def process_xbox_game(game):
    try:
        browser = get_selenium_browser()  # Create a new browser instance per process
        details_link = game.find('a', href=True)['href']
        browser.get(details_link)
        details_soup = BeautifulSoup(browser.page_source, 'html.parser')

        def safe_find(tag, css_class, attr=None):
            element = details_soup.find(tag, class_=css_class)
            return element[attr] if attr and element else (element.text.strip() if element else None)

        title = safe_find('h1', "typography-module__xdsH1___7oFBA ProductDetailsHeader-module__productTitle___Hce0B") or "No Title"
        categories_and_rating = safe_find('span', "ProductInfoLine-module__starRatingsDisplayChange___mbgn5 ProductInfoLine-module__textInfo___jOZ96")
        categories = categories_and_rating.split("•") if categories_and_rating else []
        rating = categories.pop() if categories and categories[-1].endswith('K') else "Average Rating Not Yet Available"
        short_description = safe_find('meta', None, 'content') or "No Short Description"
        full_description = safe_find('p', "Description-module__description___ylcn4 typography-module__xdsBody2___RNdGY ExpandableText-module__container___Uc17O") or "No Full Description"
        screenshots = [img['src'] for img in details_soup.select('section[aria-label="Gallery"] img')] or []
        header_image = safe_find('img', "WrappedResponsiveImage-module__image___QvkuN ProductDetailsHeader-module__productImage___QK3JA", 'src') or "No Game Header Image"
        publisher = safe_find('div', "typography-module__xdsBody2___RNdGY") or "No Publisher"
        platforms = [item.text.strip() for item in details_soup.select('ul.FeaturesList-module__wrapper___KIw42 li')] or "No Platforms"
        release_date = safe_find('div', "typography-module__xdsBody2___RNdGY") or "No Release Date"

        prices = {"us": safe_find('span', "Price-module__boldText___1i2Li Price-module__moreText___sNMVr AcquisitionButtons-module__listedPrice___PS6Zm") or "BUNDLE NOT AVAILABLE"}
        for region in regions_xbox:
            try:
                browser.get(details_link.replace("en-US", region))
                price_soup = BeautifulSoup(browser.page_source, 'html.parser')
                price = price_soup.find('span', class_="Price-module__boldText___1i2Li Price-module__moreText___sNMVr AcquisitionButtons-module__listedPrice___PS6Zm")
                prices[region.split('-')[1]] = price.text.strip() if price else "BUNDLE NOT AVAILABLE"
            except Exception as e:
                print(f"Error fetching price for region {region}: {e}")

        browser.quit()
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

def process_games_range(start_index, end_index, games):
    db = get_mongo_db()
    log_info(f"Processing games from index {start_index} to {end_index}")

    for index in range(start_index, end_index):
        try:
            game_data = process_xbox_game(games[index])
            if game_data:
                save_to_mongo(db, "xbox_games", game_data)
                if (index - start_index + 1) % 100 == 0:
                    log_info(f"Saved {start_index} ~ {index} Xbox games in this process")
        except Exception as e:
            print(f"Error processing Xbox game at index {index}: {e}")

def main():
    log_info("Waiting for fetching Xbox games...")
    games = fetch_xbox_games()

    total_games = len(games)
    if total_games == 0:
        log_info("No games found to process.")
        return

    chunk_size = (total_games + n_processes - 1) // n_processes
    ranges = [(i * chunk_size, min((i + 1) * chunk_size, total_games)) for i in range(n_processes)]

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
