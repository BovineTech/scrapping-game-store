from config import MONGO_URI, CHROME_DRIVER_PATH
from nintendo_scraper import scrape_nintendo_games
from playstation_scraper import scrape_playstation_games
from steam_scraper import scrape_steam_games
from xbox_scraper import scrape_xbox_games
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run game scrapers.")
    parser.add_argument("--platform", choices=["nintendo", "playstation", "steam", "xbox", "all"], default="all", help="Platform to scrape.")
    args = parser.parse_args()

    if args.platform == "nintendo" or args.platform == "all":
        scrape_nintendo_games(MONGO_URI, CHROME_DRIVER_PATH)
    if args.platform == "playstation" or args.platform == "all":
        scrape_playstation_games(MONGO_URI)
    if args.platform == "steam" or args.platform == "all":
        scrape_steam_games(MONGO_URI)
    if args.platform == "xbox" or args.platform == "all":
        scrape_xbox_games(MONGO_URI, CHROME_DRIVER_PATH)

if __name__ == "__main__":
    main()
