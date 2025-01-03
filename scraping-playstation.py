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
    url = f"https://store.playstation.com/en-us/pages/browse/{i}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    all_links = [a['href'] for a in soup.find_all('a', href=True)]
    filtered_links = [link for link in all_links if re.match(r"/en-us/concept/\d+", link)]
    totalLinks += filtered_links
    print("-"*30, i, "-"*30, "\n")

gameCount  = len(totalLinks)

for i in range(gameCount):
    gameInfo = {}
    url = "https://store.playstation.com" + totalLinks[i]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    ## Game title    
    title = soup.find(attrs={"data-qa": "mfe-game-title#name"}).text
    gameInfo["title"] = title
    
    # short description
    short_description = soup.find(attrs={"class": "psw-l-switcher psw-with-dividers"}).text
    gameInfo["short description"] = short_description
    
    # full description
    full_description = soup.find(attrs={"data-qa": "pdp#overview"}).text
    gameInfo["full description"] = full_description
    
    # screenshorta
    screenshorts = []
    gameInfo["screenshorts"] = screenshorts
    
    # covers
    header_img_tag = soup.find('img', {'data-qa': 'gameBackgroundImage#heroImage#preview'})
    header_img = header_img_tag['src']
    gameInfo["header_image"] = header_img
    
    # rating
    rating = soup.find(attrs={"data-qa": "mfe-star-rating#overall-rating#average-rating"}).text
    gameInfo["rating"] = rating 
    
    # publisher
    publisher = soup.find(attrs={'data-qa': "gameInfo#releaseInformation#publisher-value"}).text
    gameInfo['publisher'] = publisher
    # platform
    platforms = soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#platform-value'}).text
    gameInfo["platforms"] = platforms   
    
    # release date
    release_data = soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#releaseDate-value'}).text
    gameInfo["release_date"] = release_data
    
    # categories
    categorie_tag = soup.find(attrs={'data-qa': 'gameInfo#releaseInformation#genre-value'})
    categories = categorie_tag.find('span').text.strip().split(",")
    gameInfo["categories"] = categories 
    
    # Game Price
    price = {}
    price["us"] = soup.find(attrs={"data-qa": "mfeCtaMain#offer0#finalPrice"}).text.strip()
    for region in regions:
        region_url = url.replace("en-us", region)
        response = requests.get(region_url)
        soup = BeautifulSoup(response.content, "html.parser")
        region_price = soup.find(attrs={"data-qa": "mfeCtaMain#offer0#finalPrice"})
        price[region.split('-')[1]] = region_price.text.strip() if region_price else "N/A"
        
    gameInfo["price"] = price

    # Insert into MongoDB
    collection.insert_one(gameInfo)
    print("-"*10, "saved : ", title, "-"*10)
    