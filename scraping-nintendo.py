from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pymongo
from dotenv import load_dotenv
import os

# MongoDB setup
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = pymongo.MongoClient(MONGO_URI)
db = client["test"]
collection = db["nintendo_games"]

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
# Selenium setup
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
# options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Adjust path if needed

service = Service(r'C:\\Users\\Administrator\\.wdm\drivers\\chromedriver\\win64\\131.0.6778.204\\chromedriver-win32\\chromedriver.exe')
browser = webdriver.Chrome(service=service, options=options)
url = "https://www.nintendo.com/us/store/games/#show=1&p=1&sort=df"
browser.get(url)

# load more
# count = 0
# while True:
#     try:
#         load_more_button = WebDriverWait(browser, 60).until(
#             EC.element_to_be_clickable((By.XPATH, "//button[span[text()='Load more results']]"))
#         )
#         load_more_button.click()
#         count += 1
#         print("-"*20, "Load more button", count, " times clikced","-"*20)
#     except TimeoutException:
#         print("Timeout: Load more button not found or not clickable.")
#         break

# Parse the loaded page
soup = BeautifulSoup(browser.page_source, 'html.parser')
section = soup.find('section', class_='sc-1dskkk7-2 frpTjE')
games = section.find_all('div', class_='y83ib')

for game in games:
    try:
        details_link = "https://www.nintendo.com" + game.find('a', href=True)['href']
        browser.get(details_link)
        details_soup = BeautifulSoup(browser.page_source, 'html.parser')

        # game title
        tmp = details_soup.find('h1', class_="s954l _3TUsN _39p7O")
        title = tmp.text.strip() if tmp else "No Title"
     
        # cover image
        tmp = title + " 1"
        tmp = details_soup.find('img',{'alt':tmp})
        header_image = tmp['src'] if tmp else "No Game Header Imgae"
        
        # Release data
        section = details_soup.find('div', class_='sc-m2d4bo-0 dzfqOu')
        
        tmp = section.find('h3', string='Release date')
        release_date = tmp.find_next('div').text.strip() if tmp else "No Release Date"
        
        # cateories
        categories = [genre.text for genre in section.find_all('h3', string='Genre')[0].find_next('div').find_all('a')]
        
        # publisher
        tmp = section.find('h3', string='Publisher')
        publisher = tmp.find_next('div').find('a').text.strip() if tmp else "No Pulblisher"
        
        # Rating
        tmp = section.find('h3', string='ESRB rating')
        rating = tmp.find_next('div').find('a').text.strip() if tmp else "No Rating"

        # Short description
        tmp = details_soup.find('meta', {'name':'description'})['content']
        short_description = tmp if tmp else "No Short Description"
                
        # Full description
        full_description = []
        
        # Platform
        tmp= details_soup.find('div', class_='sc-1i9d4nw-14 gxzajP')
        platforms = tmp.find('span').get_text() if tmp else "No platform"
        
        # Screenshort 
        tmp = details_soup.find('div', {'class' : '-fzAB SUqIq'})
        screenshots = [img['src'] for img in tmp.find_all('img')] if tmp else "No Screenshot"
        
        # Prices in different regions
        prices = {}
        # USA
        tmp = (details_soup.find('span', class_='W990N QS4uJ') or details_soup.find('div', class_='o2BsP QS4uJ'))
        tmp = tmp.text.strip() if tmp else ""
        prices["us"] = tmp.split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATELY"

        # Brazil
        tmp = details_link
        browser.get(tmp.replace("/us/",'/pt-br/'))
        price_soup = BeautifulSoup(browser.page_source, 'html.parser')
        tmp = (price_soup.find('span', class_='W990N QS4uJ') or price_soup.find('div', class_='o2BsP QS4uJ'))
        tmp = tmp.text.strip().replace('\xa0',' ') if tmp else ""
        prices['br'] = tmp.split(':')[-1].strip() if tmp else "NOT AVAILABLE SEPARATELY"

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
            "full_description": full_description,
            "screenshots": screenshots,
            "header_image": header_image,
            "rating": rating,
            "publisher": publisher,
            "platforms": platforms,
            "release_date": release_date,
            "prices": prices
        }
        # Insert into MongoDB
        collection.insert_one(game_data)
        print("-"*10, "saved : ", title, "-"*10)

    except Exception as e:
        print(f"Error processing game: {e}")
        break

browser.quit()