import requests
import re

from bs4 import BeautifulSoup

from save_to_json import save_to_json

def get_dish_urls():
    url = 'https://keto-diets.ru/recepti/veg'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    raw_urls = soup.select('.category-obed')
    urls = [url.select_one('a')['href'] for url in raw_urls]
    return urls


def parse_dish_page(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title = soup.select_one('h1').text
    img_url = soup.select_one('.cooked-recipe-gallery a')['href']
    raw_description = soup.select_one('.cooked-clearfix').text
    description = ''.join(raw_description.split('\n'))
    raw_ingredients = soup.select_one('.cooked-recipe-ingredients')
    ingredients = []
    for ingredient in raw_ingredients:
        try:
            name = ingredient.select_one('.cooked-ing-name').text
            amount = ingredient.select_one('.cooked-ing-amount').text
            measurement = ingredient.select_one('.cooked-ing-measurement').text
            ingredients.append(
                {
                    'name': name,
                    'amount': amount,
                    'measurement': measurement,
                }
            )
        except Exception as error:
            continue
    cooked_dish = soup.select_one('.cooked-recipe-directions')
    raw_recept = [step.text for step in cooked_dish]
    recept = ' '.join(raw_recept)
    recept = re.sub(r'[^\w\s]+|[\d]+', r'', recept.replace('\n', ''))
    calories = soup.select_one('.cooked-clearfix>dt').text
    return {
        'title': title,
        'img_url': img_url,
        'description': description,
        'recept': recept,
        'calories': calories,
        'ingredients': ingredients
    }


def main():
    dishes = list()
    urls = get_dish_urls()
    for url in urls[:25]:
        dishes.append(parse_dish_page(url))
    save_to_json(dishes, filename='keto_dish.json')


if __name__ == '__main__':
    main()
