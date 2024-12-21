from bs4 import BeautifulSoup
import requests
import re

for i in range(10,30):
    url = f"https://store.steampowered.com/app/{i}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    if(soup.title.text.strip() != "Welcome to Steam"):
        title = soup.find('div', class_='apphub_AppName').text.strip()
        full_description = soup.find(id='game_area_description').get_text(strip=True).replace("About This Game", "")
        short_description = soup.find('div', class_='game_description_snippet').get_text(strip=True)
        price = soup.find('div', class_='discount_final_price').get_text(strip=True)
        cover_url = soup.find('img', {'class': 'game_header_image_full'}).get('src')
        rating = re.sub(r"[^\d]", "", soup.findAll('span', class_='responsive_hidden')[1].text.strip())

        tmp = soup.find('div', class_='game_area_purchase_platform').find_all('span', class_='platform_img')
        platforms = [span['class'][1] for span in tmp]
        release_date = soup.find('div', class_='date').text.strip()
        tmp = soup.find('div', class_='dev_row').find('a')
        publisher_url = tmp['href']
        publisher_name = tmp.text.strip()

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