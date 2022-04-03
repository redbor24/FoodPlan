import requests

from environs import Env
from bs4 import BeautifulSoup
from random import randint
from urllib.parse import urljoin

from save_to_json import save_to_json


def get_dish_urls(user_agent):
    headers = {
        'user-agent': user_agent,
    }
    url = 'https://www.vsegdavkusno.ru/category/dieta-nizkouglevodnyie'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    raw_urls = soup.select('.col-lg-3')
    urls = [
        urljoin('https://www.vsegdavkusno.ru/', url.select_one('.recipe-card a')['href']) for url in raw_urls
    ]
    return urls


def get_dish_detail(url, user_agent):
    headers = {
        'user-agent': user_agent,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title = soup.select_one('h1').text
    raw_img_url = soup.select_one('.WY_link img')['src'].split('0x0')
    raw_img_url, *_ = raw_img_url
    path_im_url = raw_img_url + '268x0_c9e.webp'
    img_url = urljoin('https://www.vsegdavkusno.ru', path_im_url)
    description = soup.select_one('.card-binfo__description').text.strip().replace('\n', '')
    raw_ingredients = soup.select('.ingredients__list>li')
    ingredients = list()
    for ingredient in raw_ingredients:
        try:
            ingredient_text = ingredient.text
            name, raw_amount = ingredient_text.split(' - ')
            name = name.strip()
            if 'по вкусу' in raw_amount:
                amount, measurement = 'По вкусу', 'По вкусу'
            else:
                amount, measurement = raw_amount.split(None, 1)
            ingredients.append(
                {
                    'name': name,
                    'amount': amount,
                    'measurement': measurement.strip(),
                }
            )
        except Exception as error:
            continue
    raw_recept = soup.select_one('.recipe-rich').text.split('\n')
    recept = ' '.join(raw_recept)
    recept = recept.strip().replace('   ', '')
    return {
        'title': title,
        'img_url': img_url,
        'description': description,
        'recept': recept,
        'calories': randint(100, 300),
        'ingredients': ingredients
    }


def main():
    dishes = list()
    env = Env()
    env.read_env()
    user_agent = env('USER_AGENT')
    urls = get_dish_urls(user_agent)
    for url in urls:
        dishes.append(get_dish_detail(url, user_agent))
    save_to_json(dishes, filename='low_card_dishes.json')


if __name__ == '__main__':
    main()
