from bs4 import BeautifulSoup
import requests
import multiprocessing
import re
import time
from utils import log_info, save_to_mongo, get_mongo_db, regions_playstation


PLAYSTATION_URL = "https://store.playstation.com/en-us/pages/browse/1"
n_processes = 8

def get_total_pages():
    response = requests.get(PLAYSTATION_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    ol_tag = soup.find('ol', class_="psw-l-space-x-1 psw-l-line-center psw-list-style-none")
    li_tags = ol_tag.find_all('li')
    li_tag = li_tags[-1]
    total_pages = int(li_tag.find('span', class_="psw-fill-x").text.strip())
    return total_pages

def fetch_page_links(start_page, end_page):
    links = []
    for i in range(start_page, end_page):
        url = f"https://store.playstation.com/en-us/pages/browse/{i+1}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        all_links = [a['href'] for a in soup.find_all('a', href=True)]
        filtered_links = [link for link in all_links if re.match(r"/en-us/concept/\d+", link)]
        links += filtered_links
        if ((i+1) % 50 == 0):
            print(f"{i+1} pages filtered from Playstation in process {multiprocessing.current_process().name}")
    return links

def fetch_playstation_games(total_pages):
    # Calculate page ranges for each subprocess
    chunk_size = (total_pages + n_processes - 1) // n_processes  # Ceiling division
    ranges = [
        (i * chunk_size, min((i + 1) * chunk_size - 1, total_pages))
        for i in range(n_processes)
    ]

    # Function to fetch links in parallel and collect results
    with multiprocessing.Pool(processes=n_processes) as pool:
        results = pool.starmap(fetch_page_links, ranges)

    # Flatten the results
    total_links = [link for sublist in results for link in sublist]

    return total_links

def process_playstation_game(game):
    try:
        response = requests.get("https://store.playstation.com" + game)
        response.raise_for_status()  # Raise an error if the response status is not 200
        soup = BeautifulSoup(response.content, "html.parser")

        # Helper function to safely extract text
        def get_text_safe(tag):
            return tag.text.strip() if tag else "N/A"

        # Extract game details with error handling
        title = get_text_safe(soup.find(attrs={"data-qa": "mfe-game-title#name"}))
        short_description = get_text_safe(soup.find(attrs={"class": "psw-l-switcher psw-with-dividers"}))
        full_description = get_text_safe(soup.find(attrs={"data-qa": "pdp#overview"}))

        header_img_tag = soup.find('img', {'data-qa': 'gameBackgroundImage#heroImage#preview'})
        header_image = header_img_tag['src'] if header_img_tag else "N/A"

        tmp = soup.find(attrs={"data-qa": "mfe-star-rating#overall-rating#average-rating"})
        rating = get_text_safe(tmp)

        publisher = get_text_safe(soup.find(attrs={'data-qa': "gameInfo#releaseInformation#publisher-value"}))
        platforms = get_text_safe(soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#platform-value'}))
        release_date = get_text_safe(soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#releaseDate-value'}))

        categorie_tag = soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#genre-value'})
        categories = (
            [span.text.strip() for span in categorie_tag.find_all('span')] if categorie_tag else []
        )

        # Extract game price
        prices = {}
        main_price_tag = soup.find(attrs={"data-qa": "mfeCtaMain#offer0#finalPrice"})
        prices["us"] = get_text_safe(main_price_tag)

        for region in regions_playstation:
            region_response = requests.get("https://store.playstation.com" + game.replace("en-us", region))
            region_response.raise_for_status()
            region_soup = BeautifulSoup(region_response.content, "html.parser")
            region_price_tag = region_soup.find(attrs={"data-qa": "mfeCtaMain#offer0#finalPrice"})
            prices[region.split('-')[1]] = get_text_safe(region_price_tag)

        game_data = {
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
        return game_data

    except requests.exceptions.RequestException as req_err:
        return {"error": f"Network error: {req_err}"}
    except Exception as e:
        return {"error": f"Error fetching game details: {e}"}


def process_games_range(start_index, end_index, games):
    log_info(f"Processing games from index {start_index} to {end_index}")
    db = get_mongo_db()

    for index in range(start_index, end_index):
        try:
            game_data = process_playstation_game(games[index])
            if "error" in game_data:
                print(f"! {start_index} playstation.py : exception occur : plz check the network", game_data["error"])
                time.sleep(120)
                continue
            else:
                save_to_mongo(db, "playstation_games", game_data)
                if (index - start_index + 1) % 50 == 0:
                    log_info(f"Saved Playstation {index - start_index + 1} games in this process")
        except Exception as e:
            log_info(f"Error processing game at index {index}: {str(e)}")

def main():
    log_info("Waiting for fetching Playstation games...")
    total_pages = get_total_pages()
    games = fetch_playstation_games(total_pages)

    total_games = len(games)
    if total_games == 0:
        log_info("No games found to process.")
        return

    # Calculate the ranges for each subprocess
    chunk_size = (total_games + n_processes - 1) // n_processes  # Ceiling division to cover all games
    ranges = [
        (i * chunk_size, min((i + 1) * chunk_size - 1, total_games))
        for i in range(n_processes)
    ]

    # Create and start subprocesses
    processes = []
    for start, end in ranges:
        process = multiprocessing.Process(target=process_games_range, args=(start, end, games))
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()

    log_info("All processes completed.")

if __name__ == "__main__":
    main()