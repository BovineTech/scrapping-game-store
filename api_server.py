import os
import psutil
import subprocess
from flask_cors import CORS
from flask import Flask, jsonify, send_file, request
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from dotenv import load_dotenv
from utils import log_info

# Flask app initialization
app = Flask(__name__)
CORS(app)

# MongoDB URI
load_dotenv()
app.config["MONGO_URI"] = os.getenv("MONGO_URI") + "test"
app.config["JWT_SECRET_KEY"] = os.urandom(24)  # Secret key for JWT

# Initialize PyMongo and JWT
mongo = PyMongo(app)
jwt = JWTManager(app)

# Endpoint to start the scheduler
@app.route('/scheduler/start', methods=['POST'])
@jwt_required()
def start_scheduler():
    try:
        log_info("******************** Started Scheduler... ********************")
        subprocess.Popen(["python", "scheduler.py"])
        return jsonify({"msg": "Scheduler started"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error starting scheduler: {e}"}), 500

# Endpoint to stop the scheduler
@app.route('/scheduler/stop', methods=['POST'])
@jwt_required()
def stop_scheduler():
    try:
        scheduler_stopped = False
        for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
            cmdline = proc.info['cmdline']
            if cmdline and "scheduler.py" in cmdline:
                proc.kill()  # Forcefully terminate the process
                scheduler_stopped = True
                log_info("******************** Killed Scheduler... ********************")
                break
        
        if scheduler_stopped:
            return jsonify({"msg": "Scheduler stopped"}), 200
        else:
            return jsonify({"msg": "Scheduler not running"}), 404
    except Exception as e:
        return jsonify({"msg": f"Error stopping scheduler: {str(e)}"}), 500

# Route to fetch the game count
@app.route('/games/count', methods=['GET'])
@jwt_required()
def get_game_count():
    service = request.args.get('service')
    if service == "steam":
        collection = mongo.db.steam_games
    elif service == "xbox":
        collection = mongo.db.xbox_games
    elif service == "playstation":
        collection = mongo.db.playstation_games
    elif service == "nintendo":
        collection = mongo.db.nintendo_games
    else:
        return jsonify({"msg": "Invalid service"}), 400
    
    count = collection.count_documents({})
    return jsonify({"count": count}), 200

# Route to fetch the scraper logs
@app.route('/logs', methods=['GET'])
@jwt_required()
def fetch_logs():
    try:
        return send_file("scraper.log", mimetype="text/plain")
    except Exception as e:
        return jsonify({"msg": f"Error fetching logs: {e}"}), 500

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