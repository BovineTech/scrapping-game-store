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
    locator = (By.CSS_SELECTOR, 'input[class="nc3-c-search__boxText nc3-js-megadrop__focusable nc3-js-searchBox__text"]')
    WebDriverWait(browser, 30).until(
        EC.presence_of_all_elements_located(locator)  # Wait for all matching elements
    )
    search_input = browser.find_elements(*locator)[-1]
    WebDriverWait(browser, 30).until(EC.element_to_be_clickable(search_input))
    search_input.send_keys("Fitness Boxing 3 Your Personal")
    
    # browser.save_screenshot("!debug_screenshot5.png")
    
    results = (By.CSS_SELECTOR, 'div[class="nc3-c-softCard__listItemPrice"]')
    WebDriverWait(browser, 30).until(
        EC.visibility_of_all_elements_located(results)
    )
    # browser.save_screenshot("!debug_screenshot6.png")

    soup = BeautifulSoup(browser.page_source, 'html.parser')
    price = soup.find('div', class_='nc3-c-softCard__listItemPrice')
    if price:
        print("-" * 50, "\n", price.text.strip())
    else:
        print("Price not found")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    browser.quit()
