import requests

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

def get_game_details(app_id, regions):
    base_url = "https://store.steampowered.com/api/appdetails"
    game_details = {}
    prices = {}

    try:
        response = requests.get(base_url, params={"appids": app_id, "l": "en"})
        response.raise_for_status()
        data = response.json()
        
        if str(app_id) in data and data[str(app_id)]["success"]:
            game_data = data[str(app_id)]["data"]
            game_details = {
                "title": game_data.get("name", "N/A"),
                "short_description": game_data.get("short_description", "N/A"),
                "full_description": game_data.get("detailed_description", "N/A"),
                "screenshots": [s["path_full"] for s in game_data.get("screenshots", [])],
                "header_image": game_data.get("header_image", "N/A"),
                "rating": game_data.get("metacritic", {}).get("score", "N/A"),
                "publisher": ", ".join(game_data.get("publishers", [])),
                "platforms": ", ".join([k for k, v in game_data.get("platforms", {}).items() if v]),
                "release_date": game_data.get("release_date", {}).get("date", "N/A"),
            }
        else:
            return {"error": f"-------------{app_id}--------------Game details not available-------------------------------------"}
    except Exception as e:
        return {"error": f"Error fetching game details: {e}"}
    for region in regions:
        try:
            response = requests.get(base_url, params={"appids": app_id, "cc": region, "l": "en"})
            response.raise_for_status()
            data = response.json()

            if str(app_id) in data and data[str(app_id)]["success"]:
                price_info = data[str(app_id)]["data"].get("price_overview")
                prices[region] = price_info["final_formatted"] if price_info else "Free or Not Available"
            else:
                prices[region] = "Not Available"
        except Exception as e:
            prices[region] = f"Error: {e}"

    game_details["prices"] = prices
    return game_details

if __name__ == "__main__":
    game_details = get_game_details(10,regions)
    print(game_details)
    # appid_list = get_app_list()
    # if appid_list:
    #     for i in range(len(appid_list)):
    #         game_details = get_game_details(appid_list[i]['appid'], regions)
    #         if "error" in game_details:
    #             print(game_details["error"])
    #         else:
    #             # print(game_details)
    #             print(f"Title: {game_details['title']}-------------id:{appid_list[i]['appid']}---")
    #             print(f"Short Description: {game_details['short_description']}")
    #             print(f"Publisher: {game_details['publisher']}")
    #             print(f"Platforms: {game_details['platforms']}")
    #             print(f"Release Date: {game_details['release_date']}")
    #             print(f"Rating: {game_details['rating']}")
    #             print(f"Header Image: {game_details['header_image']}")
    #             print(f"Screenshots: {', '.join(game_details['screenshots'])}\n")
    #             # Display regional prices
    #             print("Prices in different regions:")
    #             for region, price in game_details["prices"].items():
    #                 print(f"  {region.upper()}: {price}")