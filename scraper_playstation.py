from bs4 import BeautifulSoup
import requests
import multiprocessing
import re
import time
from utils import log_info, save_to_mongo, get_mongo_db, regions_playstation
import os
from dotenv import load_dotenv

load_dotenv()
n_processes = int(os.getenv("n_processes", 8))  # Default to 4 processes if not set

PLAYSTATION_URL = "https://store.playstation.com/en-us/pages/browse/1"

def get_total_pages():
    while True:
        try:
            response = requests.get(PLAYSTATION_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            ol_tag = soup.select_one('ol.psw-l-space-x-1.psw-l-line-center.psw-list-style-none')
            total_pages = int(ol_tag.select('li')[-1].find('span', class_="psw-fill-x").text.strip())
            return total_pages
        except Exception as e:
            print(f"Error fetching total pages: {e}")
            time.sleep(60)

def fetch_page_links(start_page, end_page):
    links = []
    for i in range(start_page, end_page):
        try:
            url = f"https://store.playstation.com/en-us/pages/browse/{i + 1}"
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            all_links = [a['href'] for a in soup.find_all('a', href=True)]
            filtered_links = [link for link in all_links if re.match(r"/en-us/concept/\d+", link)]
            links.extend(filtered_links)
            if (i + 1) % 50 == 0:
                log_info(f"Filtered {i + 1} pages in process {multiprocessing.current_process().name}")
        except Exception as e:
            print(f"Error fetching page {i + 1}: {e}")
    return links

def fetch_playstation_games(total_pages):
    chunk_size = (total_pages + n_processes - 1) // n_processes
    ranges = [(i * chunk_size, min((i + 1) * chunk_size, total_pages)) for i in range(n_processes)]

    with multiprocessing.Pool(processes=n_processes) as pool:
        results = pool.starmap(fetch_page_links, ranges)

    return [link for sublist in results for link in sublist]

def process_playstation_game(game):
    try:
        response = requests.get("https://store.playstation.com" + game)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        def get_text_safe(tag):
            return tag.text.strip() if tag else "N/A"

        title = get_text_safe(soup.find(attrs={"data-qa": "mfe-game-title#name"}))
        short_description = get_text_safe(soup.find(attrs={"class": "psw-l-switcher psw-with-dividers"}))
        full_description = get_text_safe(soup.find(attrs={"data-qa": "pdp#overview"}))

        header_img_tag = soup.find('img', {'data-qa': 'gameBackgroundImage#heroImage#preview'})
        header_image = header_img_tag['src'] if header_img_tag else "N/A"

        rating = get_text_safe(soup.find(attrs={"data-qa": "mfe-star-rating#overall-rating#average-rating"}))

        publisher = get_text_safe(soup.find(attrs={'data-qa': "gameInfo#releaseInformation#publisher-value"}))
        platforms = get_text_safe(soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#platform-value'}))
        release_date = get_text_safe(soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#releaseDate-value'}))

        categorie_tag = soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#genre-value'})
        categories = [span.text.strip() for span in categorie_tag.find_all('span')] if categorie_tag else []

        prices = {"us": get_text_safe(soup.find(attrs={"data-qa": "mfeCtaMain#offer0#finalPrice"}))}
        for region in regions_playstation:
            try:
                region_response = requests.get("https://store.playstation.com" + game.replace("en-us", region))
                region_response.raise_for_status()
                region_soup = BeautifulSoup(region_response.content, "html.parser")
                region_price_tag = region_soup.find(attrs={"data-qa": "mfeCtaMain#offer0#finalPrice"})
                prices[region.split('-')[1]] = get_text_safe(region_price_tag)
            except Exception as e:
                log_info(f"Error fetching price for region {region}: {e}")

        return {
            "title": title,
            "categories": categories,
            "short_description": short_description,
            "full_description": full_description,
            "screenshots": [],
            "header_image": header_image,
            "rating": rating,
            "publisher": publisher,
            "platforms": platforms,
            "release_date": release_date,
            "prices": prices,
        }
    except requests.exceptions.RequestException as req_err:
        log_info(f"Network error: {req_err}")
    except Exception as e:
        log_info(f"Error processing game: {e}")


def process_games_range(start_index, end_index, games):
    log_info(f"Processing games from index {start_index} to {end_index}")
    db = get_mongo_db()

    for index in range(start_index, end_index):
        try:
            game_data = process_playstation_game(games[index])
            if game_data:
                save_to_mongo(db, "playstation_games", game_data)
                if (index - start_index + 1) % 100 == 0:
                    log_info(f"Saved {index - start_index + 1} games in this process")
        except Exception as e:
            log_info(f"Error processing game at index {index}: {e}")

def main():
    log_info("Waiting for fetching Playstation games...")
    total_pages = get_total_pages()
    games = fetch_playstation_games(total_pages)

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
