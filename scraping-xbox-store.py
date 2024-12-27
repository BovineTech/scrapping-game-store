from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import pymongo
from dotenv import load_dotenv
import os

#mongo db setup
# load_dotenv()
# MONGO_URI = os.getenv("MONGO_URI")

# client = pymongo.MongoClient(MONGO_URI)
client = pymongo.MongoClient("mongodb+srv://thierrycaillibot5:LHoQJT9mC8i4KzvP@gamecluster.vqcxn.mongodb.net/")
db = client["test"]
collection = db["xbox_games"]

regions = [
        # "en-us",  # United States as default
        "en-gb",  # United Kingdom      
        "en-eu",  # European Union      
        "en-in",  # India               
        "pt-br",  # Brazil              
        "en-au",  # Australia           
        "en-ca",  # Canada
        "ru-ru",  # Russia              
        "zh-cn",  # China               
        "es-mx",  # Mexico              
        "en-za",  # South Africa         
        "es-ar",  # Argentina
        "tr-tr",  # Turkey               
        "ar-sa",  # Saudi Arabia         
        "ar-ae",  # United Arab Emirates 
        "en-hu",  # Hungary              
        "es-co",  # Colombia             
        "en-pl",  # Poland              
        "en-no",  # Norway              
    ]

# Selenium setup
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--enable-unsafe-swiftshader")
options.add_argument("--disable-software-rasterizer") # Prevent fallback errors

# Replace with the correct path
service = Service('C:\\Users\\Administrator\\.wdm\drivers\\chromedriver\\win64\\131.0.6778.204\\chromedriver-win32\\chromedriver.exe')
browser = webdriver.Chrome(service=service, options=options)

url = "https://www.xbox.com/en-US/games/browse"
browser.get(url)

count = 0
while True:
    try:
        load_more_button = WebDriverWait(browser, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "Load more")]'))
        )
    except TimeoutException:
        print("Timeout: Load more button not found or not clickable.")
        break
    load_more_button = browser.find_element(By.XPATH, '//button[contains(@aria-label, "Load more")]')
    load_more_button.click()
    count += 1
    print("-"*20, "Load more button", count, " times clikced","-"*20)
    
# Parse the loaded page
soup = BeautifulSoup(browser.page_source, 'html.parser')
games = soup.find_all('div', class_='ProductCard-module__cardWrapper___6Ls86 shadow') # Update with the correct class

for game in games:
    try:
        details_link = game.find('a', href=True)['href']
        browser.get(details_link)
        details_soup = BeautifulSoup(browser.page_source, 'html.parser')

        tmp = details_soup.find('h1', class_="typography-module__xdsH1___7oFBA ProductDetailsHeader-module__productTitle___Hce0B")
        title = tmp.text.strip() if tmp else "No Title"

        tmp = details_soup.find('span', class_="ProductInfoLine-module__starRatingsDisplayChange___mbgn5 ProductInfoLine-module__textInfo___jOZ96")
        categories = tmp.text.split("•") if tmp else []
        if categories:
            categories.pop(0)
            rating = categories.pop() if categories[-1].endswith('K') & categories else "Average Rating Not Yet Available"
        else:
            categories = "No Categories"
            rating = "Average Rating Not Yet Available"
        tmp = details_soup.find('meta', {'name':'description'})['content']
        short_description = tmp if tmp else "No Short Description"

        tmp = details_soup.find('p', class_="Description-module__description___ylcn4 typography-module__xdsBody2___RNdGY ExpandableText-module__container___Uc17O")
        full_description = tmp.text.strip() if tmp else "No Full Description"

        tmp = details_soup.find('section', {'aria-label' : 'Gallery'})
        screenshots = [img['src'] for img in tmp.find_all('img')] if tmp else "No Screenshot"

        tmp = details_soup.find('img', class_='WrappedResponsiveImage-module__image___QvkuN ProductDetailsHeader-module__productImage___QK3JA')
        header_image = tmp['src'] if tmp else "No Game Header Imgae"
        
        tmp = details_soup.find('h3', class_='typography-module__xdsBody1___+TQLW', string='Published by')
        tmp = tmp.find_parent('div', class_='ModuleColumn-module__col___StJzB') if tmp else ""
        tmp = tmp.find('div', class_="typography-module__xdsBody2___RNdGY") if tmp else ""
        publisher = tmp.text.strip() if tmp else "No Publisher"

        tmp = details_soup.find('ul', class_="FeaturesList-module__wrapper___KIw42 commonStyles-module__featureListStyle___8SVho")
        tmp = tmp.find_all('li') if tmp else ""
        platforms = [item.text.strip() for item in tmp] if tmp else "No Platforms"

        tmp = details_soup.find('h3', class_='typography-module__xdsBody1___+TQLW', string='Release date')
        tmp = tmp.find_parent('div', class_='ModuleColumn-module__col___StJzB') if tmp else ""
        tmp = tmp.find('div', class_="typography-module__xdsBody2___RNdGY") if tmp else ""
        release_date = tmp.text.strip() if tmp else "No Release Data"

        prices = {}
        tmp = details_soup.find('span', class_="Price-module__boldText___1i2Li Price-module__moreText___sNMVr AcquisitionButtons-module__listedPrice___PS6Zm")
        if tmp:        
            prices["us"] = tmp.text.strip()
            for region in regions:
                browser.get(details_link.replace("en-US", region))
                price_soup = BeautifulSoup(browser.page_source, 'html.parser')
                tmp = price_soup.find('span', class_="Price-module__boldText___1i2Li Price-module__moreText___sNMVr AcquisitionButtons-module__listedPrice___PS6Zm")
                prices[region.split('-')[1]] = tmp.text.strip() if tmp else "BUNDLE NOT AVAILABLE"
        else :
            prices["us"] = "NOT AVAILABLE SEPARATELY"
            for region in regions:
                prices[region.split('-')[1]] = "NOT AVAILABLE SEPARATELY"
        print(prices)
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

