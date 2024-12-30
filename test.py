from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Initialize the WebDriver
service = Service('C:\\Users\\Administrator\\.wdm\\drivers\\chromedriver\\win64\\131.0.6778.204\\chromedriver-win32\\chromedriver.exe')
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--enable-unsafe-swiftshader")
options.add_argument("--disable-software-rasterizer")

browser = webdriver.Chrome(service=service, options=options)

browser.get("https://www.nintendo.com/jp/software/switch/index.html?sftab=all")

try:
    title = "Fitness Boxing 3 Your Personal"

    search_input = browser.find_elements(By.CSS_SELECTOR, 'input[class="nc3-c-search__boxText nc3-js-megadrop__focusable nc3-js-searchBox__text"]')
    search_input[-1].clear()
    search_input[-1].send_keys(title)

    # Wait for the results to appear
    WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'li[class="soft-main-smallBanner__item soft-topBanner__item soft-topBanner__itemSmall"]'))
    )
    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    
    # Extract the price information
    price = soup.find('div', class_='nc3-c-softCard__listItemPrice')
    if price:
        print("-" * 50, "\n", price.text.strip())
    else:
        print("Price not found")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the WebDriver
    browser.quit()
