from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import os
from dotenv import load_dotenv

# Flask app initialization
app = Flask(__name__)

# MongoDB URI
load_dotenv()
app.config["MONGO_URI"] = os.getenv("MONGO_URI") + "test"
app.config["JWT_SECRET_KEY"] = os.urandom(24)  # Secret key for JWT

# Initialize PyMongo and JWT
mongo = PyMongo(app)
jwt = JWTManager(app)

# Helper function to paginate results
def paginate(collection, page, per_page, filters=None):
    query = {}
    if filters:
        query = filters
    results = list(collection.find(query, {"_id": 0}).skip((page - 1) * per_page).limit(per_page))
    return results

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get("username")
    password = request.json.get("password")
    
    if username == "admin" and password == "password123":  # Replace with real authentication
        token = create_access_token(identity=username)
        return jsonify(access_token=token), 200
    else:
        return jsonify({"msg": "Invalid credentials"}), 401
    
@app.route('/games', methods=['GET'])
@jwt_required()  # Protect this route with JWT
def get_games():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    service = request.args.get('service')
    region = request.args.get('region')
    
    filters = {}
    if region:
        filters["prices." + region] = {"$ne": "Free or Not Available"}  # Example filter for valid prices

    if service == "steam":
        collection = mongo.db.steam_games
    elif service == "xbox":
        collection = mongo.db.xbox_games
    elif service == "playstation":
        collection = mongo.db.playstation_games
    elif service == "nintendo":
        collection = mongo.db.nintendo_games
    else: # If no service is provided, we return data from all services
        collection = mongo.db.steam_games  # Defaulting to steam if no service is selected

    # Get paginated data from the collection
    games = paginate(collection, page, per_page, filters)

    for game in games:
        if region in game['prices']:
            game['price'] = game['prices'].get(region, "Not Available")
            del game['prices']

    return jsonify({"games": games}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)