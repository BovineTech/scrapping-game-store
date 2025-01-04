from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")