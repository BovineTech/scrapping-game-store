import os
import psutil
import subprocess
from flask_cors import CORS
from flask import Flask, jsonify, send_file, request
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
from utils import log_info

# Flask app initialization
app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()
app.config["MONGO_URI"] = os.getenv("MONGO_URI") + "test"
app.config["JWT_SECRET_KEY"] = os.urandom(24)

# Access IP and server port
access_ip = os.getenv("access_ip", "127.0.0.1")
server_port = os.getenv("server_port", "5000")

# Initialize PyMongo and JWT
mongo = PyMongo(app)
jwt = JWTManager(app)

# Swagger configuration
swagger_config = {
    "swagger": "2.0",
    "info": {
        "title": "Game Scraping API",
        "description": "API for managing game scrapers and retrieving game details.",
        "version": "1.0.0"
    },
    "host": f"{access_ip}:{server_port}",
    "basePath": "/",
    "schemes": ["http"],
    "paths": {
        "/login": {
            "post": {
                "summary": "Login",
                "description": "Authenticate user and generate a JWT token.",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "username": {
                                    "type": "string",
                                    "example": "admin"
                                },
                                "password": {
                                    "type": "string",
                                    "example": "password123"
                                }
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Token generated successfully."
                    },
                    "401": {
                        "description": "Invalid credentials."
                    }
                }
            }
        },
        "/games": {
            "get": {
                "summary": "Get Games",
                "description": "Retrieve a paginated list of games from the database.",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "type": "integer",
                        "required": False,
                        "default": 1
                    },
                    {
                        "name": "per_page",
                        "in": "query",
                        "type": "integer",
                        "required": False,
                        "default": 10
                    },
                    {
                        "name": "service",
                        "in": "query",
                        "type": "string",
                        "enum": [
                            "steam",
                            "xbox",
                            "playstation",
                            "nintendo"
                        ]
                    },
                    {
                        "name": "region",
                        "in": "query",
                        "type": "string"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A paginated list of games.",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "games": {
                                    "type": "array",
                                    "items": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized."
                    }
                }
            }
        },
        "/scheduler/start": {
            "post": {
                "summary": "Start Scheduler",
                "description": "Start the game scraper scheduler process.",
                "responses": {
                    "200": {
                        "description": "Scheduler started successfully."
                    },
                    "500": {
                        "description": "Error occurred while starting the scheduler."
                    }
                }
            }
        },
        "/scheduler/stop": {
            "post": {
                "summary": "Stop Scheduler",
                "description": "Stop the game scraper scheduler process.",
                "responses": {
                    "200": {
                        "description": "Scheduler stopped successfully."
                    },
                    "404": {
                        "description": "Scheduler not running."
                    },
                    "500": {
                        "description": "Error occurred while stopping the scheduler."
                    }
                }
            }
        },
        "/games/count": {
            "get": {
                "summary": "Get Game Count",
                "description": "Retrieve the count of games for a specific service.",
                "parameters": [
                    {
                        "name": "service",
                        "in": "query",
                        "type": "string",
                        "enum": [
                            "steam",
                            "xbox",
                            "playstation",
                            "nintendo"
                        ],
                        "required": True
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Game count retrieved successfully."
                    },
                    "400": {
                        "description": "Invalid service."
                    }
                }
            }
        },
        "/logs": {
            "get": {
                "summary": "Fetch Logs",
                "description": "Retrieve the scraper logs file.",
                "responses": {
                    "200": {
                        "description": "Logs retrieved successfully."
                    },
                    "500": {
                        "description": "Error occurred while fetching logs."
                    }
                }
            }
        }
    },
}

@app.route("/swagger.json")
def swagger_json():
    return jsonify(swagger_config)

# Swagger UI blueprint
SWAGGER_URL = '/swagger'
API_URL = '/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Game Scraping API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Routes
@app.route('/scheduler/start', methods=['POST'])
@jwt_required()
def start_scheduler():
    try:
        log_info("******************** Started Scheduler... ********************")
        subprocess.Popen(["python", "scheduler.py"])
        return jsonify({"msg": "Scheduler started"}), 200
    except Exception as e:
        return jsonify({"msg": f"Error starting scheduler: {e}"}), 500

@app.route('/scheduler/stop', methods=['POST'])
@jwt_required()
def stop_scheduler():
    try:
        scheduler_stopped = False
        for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
            cmdline = proc.info['cmdline']
            if cmdline and "scheduler.py" in cmdline:
                proc.kill()
                scheduler_stopped = True
                log_info("******************** Killed Scheduler... ********************")
                break
        
        if scheduler_stopped:
            return jsonify({"msg": "Scheduler stopped"}), 200
        else:
            return jsonify({"msg": "Scheduler not running"}), 404
    except Exception as e:
        return jsonify({"msg": f"Error stopping scheduler: {str(e)}"}), 500

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
    
    if username == "admin" and password == "password123":
        token = create_access_token(identity=username)
        return jsonify(access_token=token), 200
    else:
        return jsonify({"msg": "Invalid credentials"}), 401
    
@app.route('/games', methods=['GET'])
@jwt_required()
def get_games():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    service = request.args.get('service')
    region = request.args.get('region')
    
    filters = {}
    if region:
        filters["prices." + region] = {"$ne": "Free or Not Available"}

    if service == "steam":
        collection = mongo.db.steam_games
    elif service == "xbox":
        collection = mongo.db.xbox_games
    elif service == "playstation":
        collection = mongo.db.playstation_games
    elif service == "nintendo":
        collection = mongo.db.nintendo_games
    else:
        collection = mongo.db.steam_games

    games = paginate(collection, page, per_page, filters)

    for game in games:
        if region in game['prices']:
            game['price'] = game['prices'].get(region, "Not Available")
            del game['prices']
    return jsonify({"games": games}), 200

if __name__ == '__main__':
    app.run(host=access_ip, port=server_port, debug=False)
