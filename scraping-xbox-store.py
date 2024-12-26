import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
import pymongo
import time
from dotenv import load_dotenv
import os

# Load environment variables
# load_dotenv()
# MONGO_URI = os.getenv("MONGO_URI")
# DATABASE_NAME = "xbox_game_data"
# COLLECTION_NAME = "games"

# MongoDB setup
# client = pymongo.MongoClient(MONGO_URI)
# db = client[DATABASE_NAME]
# collection = db[COLLECTION_NAME]

# Selenium setup
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Replace with the correct path
service = Service('C:\\Users\\Administrator\\.wdm\drivers\\chromedriver\\win64\\131.0.6778.204\\chromedriver-win32\\chromedriver.exe')
browser = webdriver.Chrome(service=service, options=options)

url = "https://www.xbox.com/en-US/games/browse"
browser.get(url)
time.sleep(3)  # Allow time for JavaScript to load
# len = 0
# while True:
#     try:
#         load_more_button = browser.find_element(By.XPATH, '//button[contains(@aria-label, "Load more")]')

#         # Scroll to the button if necessary
#         ActionChains(browser).move_to_element(load_more_button).perform()  
#         load_more_button.click()

#         len = len + 1
#         time.sleep(len/25 + 2)  # Adjust based on content load time
#     except NoSuchElementException:
#         # If the "Load More" button is not found, all content is likely loaded
#         print("No more 'Load More' button found. All games loaded.")
#         break
#     except ElementClickInterceptedException:
#         # Handle cases where another element overlaps the button
#         print("Click intercepted. Retrying...")
#         time.sleep(2)

# Parse the loaded page
soup = BeautifulSoup(browser.page_source, 'html.parser')
games = soup.find_all('div', class_='ProductCard-module__cardWrapper___6Ls86 shadow') # Update with the correct class

data = []

for game in games:
    try:
        # Open game details page
        details_link = game.find('a', href=True)['href']
        browser.get(details_link)
        time.sleep(3)
        details_soup = BeautifulSoup(browser.page_source, 'html.parser')

        title = details_soup.find('h1', class_="typography-module__xdsH1___7oFBA ProductDetailsHeader-module__productTitle___Hce0B").text.strip()

        tmp = game.find_all('ul', class_="FeaturesList-module__wrapper___KIw42 commonStyles-module__featureListStyle___8SVho")
        print("-------------------------------------------\n",tmp)
        categories = [tag.text for tag in tmp.find_all('li')] if tmp else "N/A"

        print("-------------------------------------------\n", categories)
        break
        # description_short = game.find('p', class_='short-description').text.strip() if game.find('p', class_='short-description') else ""

        # description_full = details_soup.find('div', class_='description').text.strip() if details_soup.find('div', class_='description') else ""
        # screenshots = [img['src'] for img in details_soup.find_all('img', class_='screenshot')]
        # game_cover = details_soup.find('img', class_='cover')['src'] if details_soup.find('img', class_='cover') else ""
        
        # rating = details_soup.find('span', class_='rating').text.strip() if details_soup.find('span', class_='rating') else ""
        # publisher = details_soup.find('span', class_='publisher').text.strip() if details_soup.find('span', class_='publisher') else ""
        # platforms = [plat.text.strip() for plat in details_soup.find_all('span', class_='platform')]
        # release_date = details_soup.find('span', class_='release-date').text.strip() if details_soup.find('span', class_='release-date') else ""

        # prices = {
        #     currency.text.strip(): price.text.strip()
        #     for currency, price in zip(details_soup.find_all('span', class_='currency'), details_soup.find_all('span', class_='price'))
        # }

        # game_data = {
        #     "title": title,
        #     "categories": categories,
        #     "description_short": description_short,
        #     "description_full": description_full,
        #     "screenshots": screenshots,
        #     "game_cover": game_cover,
        #     "rating": rating,
        #     "publisher": publisher,
        #     "platforms": platforms,
        #     "release_date": release_date,
        #     "prices": prices
        # }

        # # Insert into MongoDB
        # collection.insert_one(game_data)
        # data.append(game_data)
    except Exception as e:
        print(f"Error processing game: {e}")

browser.quit()

# print(f"Scraped {len(data)} games and saved to MongoDB.")

