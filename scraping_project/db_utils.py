from pymongo import MongoClient
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def get_mongo_client(mongo_uri):
    """Connects to MongoDB and returns the client."""
    try:
        return MongoClient(mongo_uri)
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise