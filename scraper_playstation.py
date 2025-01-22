from bs4 import BeautifulSoup
import requests
import multiprocessing
import re
import time
from utils import log_info, log_error, save_to_mongo, get_mongo_db, regions_playstation

n_processes = 32  # Adjust based on your system's performance
PLAYSTATION_URL = "https://store.playstation.com/en-us/pages/browse/1"
HEADERS = {"User-Agent": "Mozilla/5.0"}  # Adding headers to reduce blocking

def get_total_pages():
    while True:
        try:
            response = requests.get(PLAYSTATION_URL, headers=HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            ol_tag = soup.select_one('ol.psw-l-space-x-1.psw-l-line-center.psw-list-style-none')
            total_pages = int(ol_tag.select('li')[-1].find('span', class_="psw-fill-x").text.strip())
            return total_pages
        except requests.RequestException as e:
            print(f"Error fetching total pages: {e}")
            time.sleep(20)  # Retry after delay

def fetch_page_links(start_page, end_page):
    links = []
    for i in range(start_page, end_page):
        try:
            url = f"https://store.playstation.com/en-us/pages/browse/{i + 1}"
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            all_links = [a['href'] for a in soup.find_all('a', href=True)]
            filtered_links = [link for link in all_links if re.match(r"/en-us/concept/\d+", link)]
            links.extend(filtered_links)
            if (i + 1) % 50 == 0:
                log_info(f"Processed {i + 1} pages in process {multiprocessing.current_process().name}")
        except requests.RequestException as e:
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
        url = f"https://store.playstation.com{game}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        def get_text_safe(tag):
            return tag.text.strip() if tag else "N/A"

        game_details = {
            "title": get_text_safe(soup.find(attrs={"data-qa": "mfe-game-title#name"})),
            "short_description": get_text_safe(soup.find(attrs={"class": "psw-l-switcher psw-with-dividers"})),
            "full_description": get_text_safe(soup.find(attrs={"data-qa": "pdp#overview"})),
            "header_image": soup.find('img', {'data-qa': 'gameBackgroundImage#heroImage#preview'})['src']
                            if soup.find('img', {'data-qa': 'gameBackgroundImage#heroImage#preview'}) else "N/A",
            "rating": get_text_safe(soup.find(attrs={"data-qa": "mfe-star-rating#overall-rating#average-rating"})),
            "publisher": get_text_safe(soup.find(attrs={'data-qa': "gameInfo#releaseInformation#publisher-value"})),
            "platforms": get_text_safe(soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#platform-value'})),
            "release_date": get_text_safe(soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#releaseDate-value'})),
            "categories": [span.text.strip() for span in soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#genre-value'}).find_all('span')] if soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#genre-value'}) else [],
            "prices": fetch_game_prices(game)
        }
        return game_details
    except requests.RequestException as e:
        print(f"Network error fetching game {game}: {e}")
    except Exception as e:
        print(f"Error processing game {game}: {e}")

def fetch_game_prices(game):
    prices = {"us": "N/A"}
    for region in regions_playstation:
        try:
            region_url = f"https://store.playstation.com{game.replace('en-us', region)}"
            response = requests.get(region_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            price_tag = soup.find(attrs={"data-qa": "mfeCtaMain#offer0#finalPrice"})
            prices[region.split('-')[1]] = price_tag.text.strip() if price_tag else "Not Available"
        except requests.RequestException as e:
            print(f"Error fetching price for {region}: {e}")
    return prices

def process_games_range(start_index, end_index, games):
    log_info(f"Processing games {start_index} to {end_index}")
    db = get_mongo_db()

    for index in range(start_index, end_index):
        try:
            game_data = process_playstation_game(games[index])
            if game_data:
                save_to_mongo(db, "playstation_games", game_data)
                if (index - start_index + 1) % 100 == 0:
                    log_info(f"Saved {index - start_index + 1} games")
            else:
                print(f"Missing data for game {index}")
        except Exception as e:
            print(f"Error processing game at index {index}: {e}")

def main():
    log_info("Waiting for fetching Playstation games...")
    total_pages = get_total_pages()
    games = fetch_playstation_games(total_pages)

    total_games = len(games)
    if total_games == 0:
        log_info("No games found to process.")
        return

    log_info(f"Fetched {total_games} games in Playstation.")
    chunk_size = (total_games + n_processes - 1) // n_processes
    ranges = [(i * chunk_size, min((i + 1) * chunk_size, total_games)) for i in range(n_processes)]

    with multiprocessing.Pool(processes=n_processes) as pool:
        pool.starmap(process_games_range, [(start, end, games) for start, end in ranges])

    log_info("="*20, "All  Playstation processes completed.", "="*20)

if __name__ == "__main__":
    main()
