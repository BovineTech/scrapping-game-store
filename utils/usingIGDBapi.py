import requests

# Set your API credentials
client_id = '3dh8m75cf954n82rczaznw42ucc1dy'  # Replace with your actual client ID
client_secret = 'txsxxflu54jkhoj8t3cl2d5ccfblds'  # Replace with your actual client secret
url = 'https://api.igdb.com/v4/games'

# Obtain an OAuth token using your client credentials
token_url = 'https://id.twitch.tv/oauth2/token'
data = {
    'client_id': client_id,
    'client_secret': client_secret,
    'grant_type': 'client_credentials'
}

# Get the access token
token_response = requests.post(token_url, data=data)
token = token_response.json().get('access_token')

# Now use the token to make API requests to IGDB
headers = {
    'Client-ID': client_id,
    'Authorization': f'Bearer {token}'
}
# Example query to get game data (e.g., games for Nintendo Switch)
query = f'''
fields name,summary,storyline,platforms,rating,release_dates,cover,screenshots;
search "The Legend of Zelda: Breath of the Wild";
limit 1;
'''

response = requests.post(url, headers=headers, data=query)

if response.status_code == 200:
    games = response.json()
    for game in games:
        print(f"Title: {game['name']}")
        print(f"Summary: {game.get('summary', 'N/A')}")
        print(f"Platforms: {game.get('platforms', 'N/A')}")
        print(f"Rating: {game.get('rating', 'N/A')}")
        print("=" * 40)
else:
    print(f"Error fetching data: {response.status_code}")