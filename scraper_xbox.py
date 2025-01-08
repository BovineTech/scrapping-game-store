# xbox_scraper.py
from bs4 import BeautifulSoup
from utils import get_mongo_db, save_to_mongo, get_selenium_browser, click_loadmore_btn, regions_xbox

XBOX_URL = "https://www.xbox.com/en-US/games/browse"

def fetch_xbox_games(browser):
    browser =  click_loadmore_btn(browser, '//button[contains(@aria-label, "Load more")]')
    soup = BeautifulSoup(browser.page_source, "html.parser")
    return soup.find_all('div', class_='ProductCard-module__cardWrapper___6Ls86 shadow')

def process_xbox_game(browser, game):
    details_link = game.find('a', href=True)['href']
    browser.get(details_link)
    details_soup = BeautifulSoup(browser.page_source, 'html.parser')

    tmp = details_soup.find('h1', class_="typography-module__xdsH1___7oFBA ProductDetailsHeader-module__productTitle___Hce0B")
    title = tmp.text.strip() if tmp else "No Title"

    tmp = details_soup.find('span', class_="ProductInfoLine-module__starRatingsDisplayChange___mbgn5 ProductInfoLine-module__textInfo___jOZ96")
    categories = tmp.text.split("•") if tmp else []
    if categories:
        categories.pop(0)
        rating = categories.pop() if categories[-1].endswith('K') else "Average Rating Not Yet Available"
    else:
        categories = "No Categories"
        rating = "Average Rating Not Yet Available"
    tmp = details_soup.find('meta', {'name':'description'})['content']
    short_description = tmp if tmp else "No Short Description"

    tmp = details_soup.find('p', class_="Description-module__description___ylcn4 typography-module__xdsBody2___RNdGY ExpandableText-module__container___Uc17O")
    full_description = tmp.text.strip() if tmp else "No Full Description"

    tmp = details_soup.find('section', {'aria-label' : 'Gallery'})
    screenshots = [img['src'] for img in tmp.find_all('img')] if tmp else []

    tmp = details_soup.find('img', class_='WrappedResponsiveImage-module__image___QvkuN ProductDetailsHeader-module__productImage___QK3JA')
    header_image = tmp['src'] if tmp else "No Game Header Imgae"
    
    tmp = details_soup.find('h3', class_='typography-module__xdsBody1___+TQLW', string='Published by')
    tmp = tmp.find_parent('div', class_='ModuleColumn-module__col___StJzB') if tmp else ""
    tmp = tmp.find('div', class_="typography-module__xdsBody2___RNdGY") if tmp else ""
    publisher = tmp.text.strip() if tmp else "No Publisher"

    tmp = details_soup.find('ul', class_="FeaturesList-module__wrapper___KIw42 commonStyles-module__featureListStyle___8SVho")
    tmp = tmp.find_all('li') if tmp else ""
    platforms = [item.text.strip() for item in tmp] if tmp else "No Platforms"

    tmp = details_soup.find('h3', class_='typography-module__xdsBody1___+TQLW', string='Release date')
    tmp = tmp.find_parent('div', class_='ModuleColumn-module__col___StJzB') if tmp else ""
    tmp = tmp.find('div', class_="typography-module__xdsBody2___RNdGY") if tmp else ""
    release_date = tmp.text.strip() if tmp else "No Release Data"

    prices = {}
    tmp = details_soup.find('span', class_="Price-module__boldText___1i2Li Price-module__moreText___sNMVr AcquisitionButtons-module__listedPrice___PS6Zm")
    prices["us"] = tmp.text.strip() if tmp else "BUNDLE NOT AVAILABLE"
    for region in regions_xbox:
        browser.get(details_link.replace("en-US", region))
        price_soup = BeautifulSoup(browser.page_source, 'html.parser')
        tmp = price_soup.find('span', class_="Price-module__boldText___1i2Li Price-module__moreText___sNMVr AcquisitionButtons-module__listedPrice___PS6Zm")
        prices[region.split('-')[1]] = tmp.text.strip() if tmp else "BUNDLE NOT AVAILABLE"

    game_data = {
        "title": title,                          
        "categories": categories,
        "short_description": short_description,
        "full_description": full_description,
        "screenshots": screenshots,
        "header_image": header_image,
        "rating": rating,
        "publisher": publisher,
        "platforms": platforms,
        "release_date": release_date,
        "prices": prices
    }
    return game_data

def main():
    browser = get_selenium_browser()
    browser.get(XBOX_URL)
    games = fetch_xbox_games(browser)
    db = get_mongo_db()

    index = 0
    while index < len(games):
        try:
            game_data = process_xbox_game(browser, games[index])
            save_to_mongo(db, "xbox_games1", game_data)
            print(f"-------Saved Xbox game: {game_data['title']}.---------")
            index += 1
        except Exception:
            print("-"*30, "! exception occur : plz check the network !", "-"*30)
    browser.quit()

if __name__ == "__main__":
    main()