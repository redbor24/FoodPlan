import os
import requests
import re
import json

from time import sleep
from bs4 import BeautifulSoup


def save_to_json(items):
    json_filepath = 'dish.json'
    with open(json_filepath, 'a') as file:
        json.dump(items, file, indent=4, ensure_ascii=False)


def get_dish_url():
    url = 'https://keto-diets.ru/recepti/veg'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    raw_urls = soup.find_all('article', class_='category-obed')
    urls = [url.find('a').get('href') for url in raw_urls]
    return urls


def parse_dish_page(url):
    response = requests.get(url)
    response.raise_for_status()
    # with open('index.html')as file:
    #     response = file.read()
    soup = BeautifulSoup(response.text, 'lxml')
    title = soup.select_one('h1').text
    img_url = soup.find(class_='cooked-recipe-gallery').find('a').get('href')
    raw_description = soup.select_one('.cooked-clearfix').text
    description = ''.join(raw_description.split('\n'))
    raw_ingredients = soup.find('div', class_='cooked-recipe-ingredients')
    ingredients = []
    for ingredient in raw_ingredients:
        try:
            name = ingredient.find(class_='cooked-ing-name').text
            amount = ingredient.find(class_='cooked-ing-amount').text
            measurement = ingredient.find(class_='cooked-ing-measurement').text
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
    # print(parse_dish_page())
    urls = get_dish_url()
    iteration_count = int(len(urls)) - 1
    print(f'Всего итераций {iteration_count}')
    for url in urls[:25]:
        save_to_json(parse_dish_page(url))
        iteration_count = iteration_count - 1
        print(f'Осталось итераций {iteration_count}')
        sleep(3)


if __name__ == '__main__':
    main()
