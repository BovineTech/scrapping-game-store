import schedule
import time
import subprocess

from pymongo import MongoClient

from dotenv import load_dotenv
import os

# MongoDB setup
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["test"]

def run_python_file(file_path):
    try:
        print(f"Starting {file_path}...")
        subprocess.run(['python', file_path], check=True)
        print(f"Successfully completed {file_path}")

        collection_name = file_path.split('-')[1] + "_games2"
        db.drop_collection(collection_name)
        db[collection_name+'1'].rename(collection_name)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while executing {file_path}: {e}")

def run_all_python_files():
    python_files = ['scraping-steam-apistore.py',
                    # 'scraping-playstation-store.py',
                    'scraping-nintendo-apistore.py',
                    # 'scraping-xbox-store.py',
                    ]
    for file in python_files:
        run_python_file(file)

# At a specific interval (everyday)
def schedule_jobs():
    schedule.every(1).minutes.do(run_all_python_files)

def main():
    schedule_jobs() # Set up the scheduled jobs
    
    while True:
        schedule.run_pending()
        time.sleep(1)  # Wait a second before checking again

if __name__ == "__main__":
    main()
