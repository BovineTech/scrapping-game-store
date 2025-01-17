from bs4 import BeautifulSoup
import requests
import multiprocessing
import re
import time
from utils import log_info, save_to_mongo, get_mongo_db, regions_playstation


PLAYSTATION_URL = "https://store.playstation.com/en-us/pages/browse/1"
n_processes = 16

def get_total_pages():
    response = requests.get(PLAYSTATION_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    ol_tag = soup.find('ol', class_="psw-l-space-x-1 psw-l-line-center psw-list-style-none")
    li_tags = ol_tag.find_all('li')
    li_tag = li_tags[-1]
    total_pages = int(li_tag.find('span', class_="psw-fill-x").text.strip())
    return total_pages

def fetch_playstation_games(total_pages):
    total_links = []
    for i in range(total_pages):
        url = f"https://store.playstation.com/en-us/pages/browse/{i+1}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        all_links = [a['href'] for a in soup.find_all('a', href=True)]
        filtered_links = [link for link in all_links if re.match(r"/en-us/concept/\d+", link)]
        total_links += filtered_links
        if((i+1) % 50 == 0):
            print(f"{i+1} pages filtered from Playstation")
    return total_links

def process_playstation_game(game):
    response = requests.get("https://store.playstation.com" + game)
    soup = BeautifulSoup(response.content, "html.parser")
    
    try:
        # Game title    
        title = soup.find(attrs={"data-qa": "mfe-game-title#name"}).text
        short_description = soup.find(attrs={"class": "psw-l-switcher psw-with-dividers"}).text
        full_description = soup.find(attrs={"data-qa": "pdp#overview"}).text
        header_img_tag = soup.find('img', {'data-qa': 'gameBackgroundImage#heroImage#preview'})
        header_image = header_img_tag['src']

        tmp = soup.find(attrs={"data-qa": "mfe-star-rating#overall-rating#average-rating"})
        rating = tmp.text if tmp else "N/A"

        publisher = soup.find(attrs={'data-qa': "gameInfo#releaseInformation#publisher-value"}).text
        platforms = soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#platform-value'}).text
        release_date = soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#releaseDate-value'}).text
        categorie_tag = soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#genre-value'})
        categories = categorie_tag.find('span').text.strip().split(",")    
        
        # Game Price
        prices = {}
        prices["us"] = soup.find(attrs={"data-qa": "mfeCtaMain#offer0#finalPrice"}).text.strip()
        for region in regions_playstation:
            response = requests.get("https://store.playstation.com" + game.replace("en-us", region))
            soup = BeautifulSoup(response.content, "html.parser")
            region_price = soup.find(attrs={"data-qa": "mfeCtaMain#offer0#finalPrice"})
            prices[region.split('-')[1]] = region_price.text.strip() if region_price else "N/A"

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
                "prices": prices
            }
        return game_data
    except Exception as e:
        return {"error": f"Error fetching game details: {e}"}

def process_games_range(start_index, end_index, games):
    log_info(f"Processing games from index {start_index} to {end_index}")
    db = get_mongo_db()

    for index in range(start_index, end_index):
        try:
            game_data = process_playstation_game(games[index])
            if "error" in game_data:
                print("! playstation.py : exception occur : plz check the network", game_data["error"])
                time.sleep(120)
                continue
            else:
                save_to_mongo(db, "playstation_games", game_data)
                if (index - start_index + 1) % 50 == 0:
                    log_info(f"Saved Playstation {index - start_index + 1} games in this process")
        except Exception as e:
            log_info(f"Error processing game at index {index}: {str(e)}")

def main(n_processes=8):
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

# def main():
#     log_info("Waiting for fetching Playstation games...")
#     total_pages = get_total_pages()
#     games = fetch_playstation_games(total_pages)
#     db = get_mongo_db()

#     index = 0
#     while index < len(games):
#         game_data = process_playstation_game(games[index])
#         if "error" in game_data:
#             print("! playstation.py : exception occur : plz check the network", game_data["error"])
#             time.sleep(120)
#             continue
#         else:
#             save_to_mongo(db, "playstation_games", game_data)
#             index += 1
#             if(index % 50 == 0):
#                 log_info(f"Saved Playstation {index} games")

if __name__ == "__main__":
    main()