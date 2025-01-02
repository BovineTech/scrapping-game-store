from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Initialize the WebDriver
service = Service('C:\\Users\\Administrator\\.wdm\\drivers\\chromedriver\\win64\\131.0.6778.204\\chromedriver-win32\\chromedriver.exe')
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--enable-unsafe-swiftshader")
options.add_argument("--disable-software-rasterizer")

browser = webdriver.Chrome(service=service, options=options)

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

for region in region_urls:
    browser.get(region)
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

        if price:
            print("-" * 50, "\n", price.text.strip())
        else:
            print("Price not found")
    except Exception as e:
        print(f"An error occurred: {e}")
    break
browser.quit()
