from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from typing import List, Optional
import os

# Initialize FastAPI app
app = FastAPI()

# Token-based authorization
security = HTTPBearer()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "your_online_mongo_uri")
client = MongoClient(MONGO_URI)
db = client["your_database_name"]

# Collections
COLLECTIONS = ["steam_games", "xbox_games", "nintendo_games", "playstation_games"]

# Authentication function
def authorize(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "your_secret_token":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials

@app.get("/")
def root():
    return {"message": "Welcome to the Games API"}

# 1. Authorization Endpoint (Handled with token in headers)

# 2. Get All Data (with pagination, filtering)
@app.get("/games")
def get_all_games(
    collection: str = Query(..., description="Collection name"),
    region: Optional[str] = Query(None, description="Filter by region"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    _ = Depends(authorize)
):
    if collection not in COLLECTIONS:
        raise HTTPException(status_code=400, detail="Invalid collection name")

    # Fetch data with optional region filter
    query = {}
    if region:
        query[f"prices.{region}"] = {"$exists": True}

    skip = (page - 1) * limit
    data = list(db[collection].find(query).skip(skip).limit(limit))
    for doc in data:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string

    total = db[collection].count_documents(query)
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": data,
    }

# 3. Get Document by ID
@app.get("/games/{collection}/{game_id}")
def get_game_by_id(
    collection: str,
    game_id: str,
    _ = Depends(authorize)
):
    if collection not in COLLECTIONS:
        raise HTTPException(status_code=400, detail="Invalid collection name")

    game = db[collection].find_one({"_id": ObjectId(game_id)})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    game["_id"] = str(game["_id"])
    return game
