from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import logging

def setup_selenium_driver(chrome_driver_path, options=None):
    """Configures and returns a Selenium WebDriver."""
    if options is None:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
    try:
        driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
        logging.info(f"Selenium WebDriver initialized with options: {options.arguments}")
        return driver
    except Exception as e:
        logging.error(f"Error setting up Selenium WebDriver: {e}")
        raise