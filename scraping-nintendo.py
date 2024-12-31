from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import pymongo
from dotenv import load_dotenv
import os
from time import sleep


# Load environment variables
# load_dotenv()
# MONGO_URI = os.getenv("MONGO_URI")
# DATABASE_NAME = "xbox_game_data"
# COLLECTION_NAME = "games"

# MongoDB setup
# client = pymongo.MongoClient(MONGO_URI)
# db = client[DATABASE_NAME]
# collection = db[COLLECTION_NAME]

region_urls = [
    "https://www.nintendo.com/en-gb/Search/Search-299117.html?f=147394-86", # United Kingdom
    # "https://www.nintendo.com/de-de/Suche-/Suche-299117.html?f=147394-86", # Germany
    # "https://www.nintendo.com/fr-fr/Rechercher/Rechercher-299117.html?f=147394-5-81" # France
    # "https://www.nintendo.com/it-it/Cerca/Cerca-299117.html?f=147394-86" # Italy
    # "https://www.nintendo.com/es-es/Buscar/Buscar-299117.html?f=147394-86" # Spain
    # "https://www.nintendo.com/nl-nl/Zoeken/Zoeken-299117.html?f=147394-86" # Netherlands
    # "https://www.nintendo.com/pt-pt/Pesquisar/Pesquisa-299117.html?f=147394-86" # Portugal
    # "https://www.nintendo.com/de-ch/Suche-/Suche-299117.html?f=147394-86" # Switzerland
    # "https://www.nintendo.com/de-at/Suche-/Suche-299117.html?f=147394-86" # Austria
]
# Selenium setup
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Adjust path if needed
# Replace with the correct path
service = Service('C:\\Users\\Administrator\\.cache\\selenium\\chromedriver\\win64\\131.0.6778.204\\chromedriver.exe')
browser = webdriver.Chrome(service=service, options=options)

url = "https://www.nintendo.com/us/store/games/#show=1&p=1&sort=df"
browser.get(url)

# while True:
#     try:
#         load_more_button = WebDriverWait(browser, 60).until(
#             EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "Load more")]'))
#         )
#     except TimeoutException:
#         print("Timeout: Load more button not found or not clickable.")
#         break
#     load_more_button = browser.find_element(By.XPATH, '//button[contains(@aria-label, "Load more")]')
#     load_more_button.click()
    

    
# Parse the loaded page
soup = BeautifulSoup(browser.page_source, 'html.parser')
section = soup.find('section', class_='sc-1dskkk7-2 frpTjE')
games = section.find_all('div', class_='y83ib')
games += section.find_all('div', class_='y83ib H5L8k')

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
        
        tmp = section.find('h3', text='Release date')
        release_date = tmp.find_next('div').text.strip() if tmp else "No Release Date"
        
        # cateories
        categories = [genre.text for genre in section.find_all('h3', text='Genre')[0].find_next('div').find_all('a')]
        
        # publisher
        tmp = section.find('h3', text='Publisher')
        publisher = tmp.find_next('div').find('a').text.strip() if tmp else "No Pulblisher"
        
        # Rating
        tmp = section.find('h3', text='ESRB rating')
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
        
        # USA
        prices = {}    
        tmp = details_soup.find('span', class_='W990N QS4uJ').text.strip()   
        
        if tmp:
            prices["us"] = tmp.split(':')[-1].strip()
            
            tmp = details_link
            browser.get(tmp.replace("/us/",'/pt-br/'))
            price_soup = BeautifulSoup(browser.page_source, 'html.parser')
            tmp = price_soup.find('span', class_='W990N QS4uJ')
            tmp = tmp.text.strip().replace('\xa0',' ') if tmp else ""
            prices['br'] = tmp.split(':')[-1].strip() if tmp else "No"
                  
            # for region_url in region_urls:
            #     browser.get(region_url)
            #     input_element = browser.find_element(By.CSS_SELECTOR, "div.queryBox input[type='search']")
           
        # print("------------------>", prices)
             
        # else:
        #     prices["us"] = "NOT AVAILABLE SEPARATELY"
        #     for region in regions:
        #        prices[region.split('-')[1]] = "NOT AVAILABLE SEPARATELY"
        # print(prices)
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
        # collection.insert_one(game_data)
       
    except Exception as e:
        print(f"Error processing game: {e}")
        break

browser.quit()