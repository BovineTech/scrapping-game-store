from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
import re
import pymongo
from dotenv import load_dotenv
import os

API_URL = "https://api.sampleapis.com/switch/games"  # API endpoint
region_urls = [
    "https://www.nintendo.com/en-gb/Search/Search-299117.html?f=147394-86", # United Kingdom
    "https://www.nintendo.com/de-de/Suche-/Suche-299117.html?f=147394-86", # Germany
    "https://www.nintendo.com/fr-fr/Rechercher/Rechercher-299117.html?f=147394-5-81", # France
    "https://www.nintendo.com/it-it/Cerca/Cerca-299117.html?f=147394-86", # Italy
    "https://www.nintendo.com/es-es/Buscar/Buscar-299117.html?f=147394-86", # Spain
    "https://www.nintendo.com/nl-nl/Zoeken/Zoeken-299117.html?f=147394-86", # Netherlands
    "https://www.nintendo.com/pt-pt/Pesquisar/Pesquisa-299117.html?f=147394-86", # Portugal
    "https://www.nintendo.com/de-ch/Suche-/Suche-299117.html?f=147394-86", # Switzerland
    "https://www.nintendo.com/de-at/Suche-/Suche-299117.html?f=147394-86", # Austria
]

# MongoDB setup
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = pymongo.MongoClient(MONGO_URI)
db = client["test"]
collection = db["nintendo_games1"]

# Selenium setup
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox") # options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Adjust path if needed
service = Service(r'C:\\Users\\Administrator\\.wdm\drivers\\chromedriver\\win64\\131.0.6778.204\\chromedriver-win32\\chromedriver.exe')
browser = webdriver.Chrome(service=service, options=options)

# Function to fetch game data
def fetch_games(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an error for bad status codes
        games = response.json()  # Parse the JSON response
        return games
    except requests.RequestException as e:
        print(f"Error fetching games: {e}")
        return []

# Function to structure game data
def process_game_data(game):

    # retrieve data by api
    title = game.get("name", "N/A")
    categories = game.get("genre", [])
    publisher = game.get("publishers")[0] if game.get("publishers") else "N/A"
    release_date = game.get("releaseDates", {})['NorthAmerica']
    
    tmp = title.replace("&", "and")
    tmp = tmp.lower()
    tmp = re.sub(r'[^a-z0-9 ]', '', tmp)
    tmp = tmp.replace(" ","-")

    game_link = "https://www.nintendo.com/us/store/products/" + tmp + "-switch/"
    browser.get(game_link)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    
    # cover image
    tmp = soup.find('img',{'alt': title + " 1"})
    header_image = tmp['src'] if tmp else "No Game Header Imgae"


    # Rating
    tmp = soup.find('h3', string='ESRB rating')
    rating = tmp.find_next('div').find('a').text.strip() if tmp else "No Rating"

    # Short description
    tmp = soup.find('meta', {'name':'description'})['content']
    short_description = tmp if tmp else "No Short Description"

    # Platform
    tmp = soup.find('div', class_='sc-1i9d4nw-14 gxzajP')
    platforms = tmp.find('span').get_text() if tmp else "No platform"

    # Screenshots 
    tmp = soup.find('div', {'class' : '-fzAB SUqIq'})
    screenshots = [img['src'] for img in tmp.find_all('img')] if tmp else []

    # Prices in different regions
    prices = {}
    # USA
    tmp = (soup.find('span', class_='W990N QS4uJ') or soup.find('div', class_='o2BsP QS4uJ'))
    tmp = tmp.text.strip() if tmp else ""
    prices["us"] = tmp.split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATELY"

    # Brazil
    browser.get(game_link.replace("/us/",'/pt-br/'))
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    tmp = (soup.find('span', class_='W990N QS4uJ') or soup.find('div', class_='o2BsP QS4uJ'))
    tmp = tmp.text.strip().replace('\xa0',' ') if tmp else ""
    prices['br'] = tmp.split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATSELY"

    # EUA
    for region_url in region_urls:
        browser.get(region_url)
        try:
            locator = (By.CSS_SELECTOR, 'input[type="search"]')
            WebDriverWait(browser, 30).until(
                EC.presence_of_all_elements_located(locator)  # Wait for matching element
            )
            search_input = browser.find_elements(*locator)[-1]

            WebDriverWait(browser, 30).until(EC.element_to_be_clickable(search_input))
            search_input.send_keys("Fitness Boxing 3 Your Personal")
            search_input.send_keys(Keys.RETURN)

            locator = (By.CSS_SELECTOR, 'span[class=""]')
            WebDriverWait(browser, 30).until(
                EC.visibility_of_all_elements_located(locator)
            )        

            soup = BeautifulSoup(browser.page_source, 'html.parser')
            tmp = soup.find_all('ul', class_="results")[-1]
            tmp = tmp.find('li', class_="searchresult_row page-list-group-item col-xs-12")
            tmp = tmp.find('p', class_='price-small')
            price = tmp.find_all('span')[-1]
            prices[region_url.split('/')[3].split('-')[1]] = price.text.strip() if price else "NOT AVAILABLE SEPARATELY"
        except Exception as e:
            print(f"An error occurred: {e}")

    # Japan
    browser.get("https://www.nintendo.com/jp/software/switch/index.html?sftab=all")
    try:
        locator = (By.CSS_SELECTOR, 'input[class="nc3-c-search__boxText nc3-js-megadrop__focusable nc3-js-searchBox__text"]')
        WebDriverWait(browser, 30).until(
            EC.presence_of_all_elements_located(locator)  # Wait for all matching elements
        )
        search_input = browser.find_elements(*locator)[-1]
        WebDriverWait(browser, 30).until(EC.element_to_be_clickable(search_input))
        search_input.send_keys("Fitness Boxing 3 Your Personal")
        
        results = (By.CSS_SELECTOR, 'div[class="nc3-c-softCard__listItemPrice"]')
        WebDriverWait(browser, 30).until(
            EC.visibility_of_all_elements_located(results)
        )
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        price = soup.find('div', class_='nc3-c-softCard__listItemPrice')
        prices['jp'] = price.text.strip() if price else "NOT AVAILABLE SEPARATELY"
    except Exception as e:
        print(f"An error occurred: {e}")


    game_data = {
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
    return game_data

# Fetch all games
def main():
    games = fetch_games(API_URL)
    if not games:
        print("No game data available.")
        return
    
    tmp_count = 0
    # Process each game
    for game in games:
        game_data = process_game_data(game)
        # Insert into MongoDB
        collection.insert_one(game_data)
        print("-"*10, "saved : ", game_data['title'], "-"*10)
        
        tmp_count += 1
        if tmp_count == 5: break

    browser.quit()
if __name__ == "__main__":
    main()
