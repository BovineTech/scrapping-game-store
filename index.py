# from autoscraper import AutoScraper
# import re

# # scraper = AutoScraper()
# for i in range(5):
#     url = f"https://store.playstation.com/en-us/pages/browse/{i}"
#     wanted_list = ["&quot;id&quot;:&quot;228748&quot;,&quot;index&quot;:0,&quot;name&quot;:&quot;Fortnite&quot;,&quot;titleId&quot;:&quot;&quot;,&quot;emsExperienceId&quot;:&quot;7bbceafe-bfa8-11ee-b375-5e45f4e139ac&quot;,&quot;emsViewId&quot;:&quot;9b309fc6-d7d4-11ee-a31f-a2110459ffc0&quot;,&quot;emsComponentId&quot;:&quot;a2c6a6e0-9ba1-11ef-9795-4e5a84bfbf77&quot;"]
#     result = scraper.build(url, wanted_list)    
#     print(result)

# # # # Here we can also pass html content via the html parameter instead of the url (html=html_content)

# # Step 1: Target URL
# url = "https://store.playstation.com/en-us/pages/browse/2"  # Replace with the URL you want to scrape

# # Step 2: Provide an example of the link to extract
# # example_links = "/en-us/concept/123"  # Replace with an example href from the target page


# # Step 3: Create and Train the AutoScraper
# scraper = AutoScraper()
# # scraper.build(url, wanted_list)
# # scraper.build(url, example_links)

# # Step 4: Get results
# scraper.build(url)
# results = scraper.get_result_similar(url)

# # Display the extracted links
# # (Optional) Save the scraper for future use

# # Example: Filter links that match the general format
# # filtered_links = [link for link in results if re.match(r"/en-us/concept/\d+", link)]
# print(results)
# hello 

from bs4 import BeautifulSoup
import requests
import re

totalLinks =[]
gameInfos = [{}]

for i in range(2):
    url = f"https://store.playstation.com/en-us/pages/browse/{i}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    all_links = [a['href'] for a in soup.find_all('a', href=True)]
    filtered_links = [link for link in all_links if re.match(r"/en-us/concept/\d+", link)]
    totalLinks += filtered_links
gameCount  = len(totalLinks)
# for i in range(gameCount):
#     url = "https://store.playstation.com" + totalLinks[i]
#     print(url)
for i in range(5):
    gameInfo = {}
    url = "https://store.playstation.com" + totalLinks[i]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    ##
    descript = soup.find(attrs={"data-qa": "mfe-game-overview#description"}).text
    gameInfo["descrip"] = descript
    ##
    averRating = soup.find(attrs={"data-qa": "mfe-star-rating#overall-rating#average-rating"}).text
    gameInfo["averRating"] = averRating
    ##
    name = soup.find(attrs={"data-qa": "mfe-game-title#name"}).text
    gameInfo["name"] = name
    gameInfos.append(gameInfo)
for i in range(len(gameInfos)):
    for key, value in gameInfos[i].items():
        print(key, value)