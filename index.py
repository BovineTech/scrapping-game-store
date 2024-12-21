from bs4 import BeautifulSoup
import requests
import re


url = f"https://store.steampowered.com/app/2513280"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

tmp = soup.find('div', class_='apphub_AppName')
title = tmp.text.strip() if tmp else 'No Title'

tmp = soup.find(id='game_area_description')
full_description = tmp.get_text(strip=True).replace("About This Game", "") if tmp else 'No Full Description'

tmp = soup.find('div', class_='game_description_snippet')
short_description = tmp.get_text(strip=True) if tmp else 'No Short Description'

tmp = soup.find('div', class_='discount_final_price')
price = tmp.get_text(strip=True) if tmp else 'No Price'

tmp = soup.find('img', {'class': 'game_header_image_full'})
cover_url = tmp.get('src') if tmp else 'No Cover Image'

tmp = soup.findAll('span', class_='responsive_hidden')
if len(tmp) > 1:
    rating = tmp[1].text.strip()
else:
    rating = tmp[0].text.strip()
rating = re.sub(r"[^\d]", "", rating)

tmp = soup.find('div', class_='game_area_purchase_platform')
if(tmp):
    tmp = tmp.find_all('span', class_='platform_img')
    platforms = [span['class'][1] for span in tmp] if tmp else "No Platform"
else:
    platforms = "No Platform"

tmp = soup.find('div', class_='date')
release_date = tmp.text.strip() if tmp else "No Release Data"

tmp = soup.find('div', class_='date')
release_date = tmp.text.strip() if tmp else "No Release Data"

publisher_link = soup.find('div', class_='dev_row').find('a')
if publisher_link:
    publisher_url = publisher_link['href']
    publisher_name = publisher_link.text.strip()
else:
    publisher_url = publisher_name = 'No data found'

print(title)
print(full_description)
print(short_description)
print(price)
print(cover_url)
print(rating)
print(publisher_name)
print(publisher_url)
print(platforms)
print(release_date)

# game_info = {
#     'Title': title,
#     'Full Description': full_description,
#     'Short Description': short_description,
#     'Price': price,
#     'Cover Image': cover_url,
#     'Rating': rating,
#     'Publisher Name': publisher_name,
#     'Publisher URL': publisher_url,
#     'Platforms': platforms,
#     'Release Date': release_date
# }
# print(game_info)