# from bs4 import BeautifulSoup
import requests
# import re

currencies = [
    "USD",  # US Dollar
    "EUR",  # Euro
    "GBP",  # British Pound
    "RUB",  # Russian Ruble
    "BRL",  # Brazilian Real
    "JPY",  # Japanese Yen
    "AUD",  # Australian Dollar
    "CAD",  # Canadian Dollar
    "CNY",  # Chinese Yuan
    "KRW",  # South Korean Won
    "TRY",  # Turkish Lira
    "NZD",  # New Zealand Dollar
    "INR",  # Indian Rupee
    "MXN",  # Mexican Peso
    "IDR",  # Indonesian Rupiah
    "PHP",  # Philippine Peso
    "SGD",  # Singapore Dollar
    "THB",  # Thai Baht
    "MYR",  # Malaysian Ringgit
    "ZAR",  # South African Rand
    "HKD",  # Hong Kong Dollar
    "SAR",  # Saudi Riyal
    "AED",  # United Arab Emirates Dirham
]

regions = [
        "us",  # United States
        "gb",  # United Kingdom
        "eu",  # European Union
        "jp",  # Japan
        "in",  # India
        "br",  # Brazil
        "au",  # Australia
        "ca",  # Canada
        "ru",  # Russia
        "cn",  # China
        "kr",  # South Korea
        "mx",  # Mexico
        "za",  # South Africa
        "ar",  # Argentina
        "tr",  # Turkey
        "id",  # Indonesia
        "sg",  # Singapore
        "ph",  # Philippines
        "th",  # Thailand
        "my",  # Malaysia
        "nz",  # New Zealand
        "sa",  # Saudi Arabia
        "ae",  # United Arab Emirates
    ]

def get_game_details(app_id, currency="JPY"):
    api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc={currency}"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        
        if str(app_id) not in data or not data[str(app_id)]["success"]:
            print("Game not found or details unavailable.")
            return None
        
        game_data = data[str(app_id)]["data"]
        
        # Extract information
        game_details = {
            "title": game_data.get("name", "N/A"),
            "short_description": game_data.get("short_description", "N/A"),
            "full_description": game_data.get("detailed_description", "N/A"),
            "price": game_data.get("price_overview", {}).get("final_formatted", "Free"),
            "screenshots": [screenshot["path_full"] for screenshot in game_data.get("screenshots", [])],
            "cover_image": game_data.get("header_image", "N/A"),
            "publisher": game_data.get("publishers", ["N/A"])[0],
            "platforms": game_data.get("platforms", {}),
            "release_date": game_data.get("release_date", {}).get("date", "N/A"),
        }
        
        return game_details
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_app_list():
    api_url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        
        if "applist" in data and "apps" in data["applist"]:
            return data["applist"]["apps"]
        else:
            print("No app data found in response.")
            return []
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []

def get_game_price_in_currencies(app_id, currencies):
    base_url = "https://store.steampowered.com/api/appdetails"
    prices = {}

    for currency in currencies:
        params = {"appids": app_id, "cc": currency}
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if str(app_id) in data and data[str(app_id)]["success"]:
                price_info = data[str(app_id)]["data"].get("price_overview")
                prices[currency] = price_info["final_formatted"] if price_info else "Free"
            else:
                prices[currency] = "Price not available"
        except requests.exceptions.RequestException as e:
            prices[currency] = f"Error: {e}"

    return prices

def get_game_prices_in_currencies(app_id, regions):
    base_url = "https://store.steampowered.com/api/appdetails"
    prices = {}

    for region in regions:
        params = {"appids": app_id, "cc": region, "l": "en"}  # Use 'cc' for country and 'l' for language
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if str(app_id) in data and data[str(app_id)]["success"]:
                price_info = data[str(app_id)]["data"].get("price_overview")
                if price_info:
                    prices[region] = price_info["final_formatted"]  # Regional price
                else:
                    prices[region] = "Free or Not Available"
            else:
                prices[region] = "Price not available"
        except requests.exceptions.RequestException as e:
            prices[region] = f"Error: {e}"

    return prices

if __name__ == "__main__":
    app_id = 10  # Example app ID (CS: GO)
    
    print(f"Fetching prices for App ID {app_id}...")
    prices = get_game_prices_in_currencies(app_id, regions)
    
    for region, price in prices.items():
        print(f"Region ({region.upper()}): {price}")

# if __name__ == "__main__":
#     app_id = 10  # Replace with the App ID of the game (e.g., 440 for Team Fortress 2)
    
#     print(f"Fetching prices for App ID {app_id}...")
#     prices = get_game_price_in_currencies(app_id, currencies)
    
#     for currency, price in prices.items():
#         print(f"{currency}: {price}")

# if __name__ == "__main__":
#     currencies = get_steam_supported_currencies()
#     print("Steam Supported Currencies:")
#     for currency in currencies:
#         print(currency)

# if __name__ == "__main__":
#     app_list = get_app_list()
#     if app_list:
#         print(f"Total Apps: {len(app_list)}")
#         for i in range(101,105):
#             print(app_list[i])
#             # print(f"App ID: {app_list[i]['appid']}, Name: {app_list[i]['name']}")
#         # for app in app_list[:20]:
#         #     print(f"App ID: {app['appid']}, Name: {app['name']}")

# if __name__ == "__main__":
#     app_id = 10  # Replace with the App ID of the game (e.g., 440 for Team Fortress 2)
#     currency = "JPN"  # Replace with desired currency code
#     game_details = get_game_details(app_id, currency)
    
#     if game_details:
#         print(f"Title: {game_details['title']}")
#         print(f"Short Description: {game_details['short_description']}")
#         print(f"Full Description: {game_details['full_description'][:200]}...")  # Truncated for display
#         print(f"Price: {game_details['price']}")
#         print(f"Screenshots: {game_details['screenshots']}")
#         print(f"Cover Image: {game_details['cover_image']}")
#         print(f"Publisher: {game_details['publisher']}")
#         print(f"Platforms: {', '.join([k for k, v in game_details['platforms'].items() if v])}")
#         print(f"Release Date: {game_details['release_date']}")