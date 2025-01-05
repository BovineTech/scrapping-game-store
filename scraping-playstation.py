from bs4 import BeautifulSoup
import requests
import re
import pymongo
from dotenv import load_dotenv
import os

#mongo database
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = pymongo.MongoClient(MONGO_URI)
db = client["test"]
collection = db["playstation_games"]

totalLinks =[]

regions = [
    # 'en-us',
    'en-eu',
    'de-at',
    'es-ar',
    'ar-bh',
    'fr-be',
    'pt-br',
    'en-gb',
    'de-de',
    'en-hk',
    'en-gr',
    'en-in',
    'es-es',
    'it-it',
    'ar-qa',
    'en-kw',
    'ar-lb',
    'de-lu',
    'nl-nl',
    'ar-ae',
    'ar-om',
    'pl-pl',
    'pt-pt',
    "ro-ro",
    'ar-sa',
    'sl-si',
    'sk-sk',
    'tr-tr',
    'fi-fi',
    'fr-fr',
    'en-za'
]

last_page_url = f"https://store.playstation.com/en-us/pages/browse/1"
response = requests.get(last_page_url)
soup = BeautifulSoup(response.content, "html.parser")
ol_tag = soup.find('ol', class_="psw-l-space-x-1 psw-l-line-center psw-list-style-none")
li_tags = ol_tag.find_all('li')
li_tag = li_tags[-1]
page_num = int(li_tag.find('span', class_="psw-fill-x").text.strip())

for i in range(page_num):
    url = f"https://store.playstation.com/en-us/pages/browse/{i+1}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    all_links = [a['href'] for a in soup.find_all('a', href=True)]
    filtered_links = [link for link in all_links if re.match(r"/en-us/concept/\d+", link)]
    totalLinks += filtered_links
    print("-"*30, i + 1, "-"*30, "\n")

for link in totalLinks:
    response = requests.get("https://store.playstation.com" + link)
    soup = BeautifulSoup(response.content, "html.parser")
    
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
    for region in regions:
        region_url = url.replace("en-us", region)
        response = requests.get(region_url)
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
    # Insert into MongoDB
    collection.insert_one(game_data)
    print("-"*10, "saved : ", title, "-"*10)
    