import argparse
import requests

from environs import Env
from random import randint
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from save_to_json import save_to_json


def add_argument_parser():
    parser = argparse.ArgumentParser(
        description='''Парсит сайт https://povar.ru/
        на вход принимает ссылку на категорию блюд
        по умолчанию категория "Горячие блюда", и 
        имя файла json куда будет сохранена информация
        по первым сорока блюдам категории.
        '''
    )
    parser.add_argument(
        '--url',
        default='https://povar.ru/list/goryachie_bliuda/',
        help='url-категории блюд',
    )
    parser.add_argument(
        'filename',
        help='Имя .json файла с результатами',
    )

    return parser


def get_dish_urls(url, user_agent):
    headers = {
        'user-agent': user_agent
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    raw_urls = soup.find_all(class_='recipe')
    urls = [urljoin('https://povar.ru', url.find('h3').find('a').get('href')) for url in raw_urls]
    return urls


def get_dish_detail(url, user_agent):
    headers = {
        'user-agent': user_agent
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title = soup.select_one('.detailed').text
    img_url = soup.select_one('.bigImgBox img')['src']
    description = soup.select_one('.detailed_full').text.strip()
    raw_ingredients = soup.select('.detailed_ingredients>li')
    ingredients = []
    for ingredient in raw_ingredients:
        try:
            ingredient_text = ingredient.text
            name, amount = ingredient_text.split('—')
            name = name.strip()
            raw_amount = amount.strip()
            if 'По вкусу' in raw_amount:
                amount, measurement = 'По вкусу', 'По вкусу'
            else:
                amount, measurement = raw_amount.split(None, 1)
            ingredients.append(
                {
                    'name': name,
                    'amount': amount,
                    'measurement': measurement.replace('\xa0', ' '),
                }
            )
        except Exception as error:
            continue
    raw_recept = soup.select('.detailed_step_description_big')
    raw_recept = [step.text.strip() for step in raw_recept]
    recept = ' '.join(raw_recept)
    return {
        'title': title,
        'img_url': img_url,
        'description': description,
        'recept': recept,
        'calories': randint(400, 900),
        'ingredients': ingredients
    }


def main():
    env = Env()
    env.read_env()
    user_agent = env('USER_AGENT')
    parser = add_argument_parser()
    args = parser.parse_args()
    filename = args.filename
    urls = get_dish_urls(args.url, user_agent)
    dishes = list()
    for url in urls:
        dishes.append(get_dish_detail(url, user_agent))
    save_to_json(dishes, filename=filename)


if __name__ == '__main__':
    main()
