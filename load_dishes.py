import json
# import re
from tgbot.models import MenuType, Dish, DishIngredient


# def prepare_value(str_value):
#     str_value = str_value.replace('¼', '0.25').replace('½', '0.5'). \
#         replace('¾', '0.75').replace('⅓', '0.33').replace(',', '.')
#     return re.sub(r'[^0-9.,-]', '', str_value)


def load_dishes(dishes_json, menu_type):
    try:
        menu = MenuType.objects.get(name=menu_type)
    except Exception as e:
        print(f'Ошибка для "{menu_type}"! {e}')

    print(f' Удаление блюд меню "{menu_type}" перед загрузкой...')
    print(f'  блюд: {Dish.objects.count()}')
    print(f'  ингредиентов: {DishIngredient.objects.count()}')
    try:
        Dish.objects.filter(menu_type=menu).delete()
        print(f' Удаление завершено:')
        print(f'  блюд: {Dish.objects.count()}')
        print(f'  ингредиентов: {DishIngredient.objects.count()}')
    except Exception as e:
        print(f'Ошибка удаления блюд: {e}')

    with open(dishes_json, 'r', encoding='utf-8') as f:
        dishes = json.load(f)

    for dish in dishes:
        print(f"Dish: {dish['title']}, {dish['calories']}")
        new_dish = Dish(
            menu_type=menu,
            name=dish['title'],
            description=dish['description'],
            recipe=dish['recept'],
            calories=dish['calories']
            # picture=
        )
        new_dish.save()
        for ingredient in dish['ingredients']:
            print(ingredient['name'], ingredient['amount'], ingredient['measurement'])
            DishIngredient(
                dish=new_dish,
                name=ingredient['name'],
                amount=ingredient['amount'],
                unit=ingredient['measurement']
            ).save()

    print(f' Список блюд для меню "{menu_type}" загружен:')
    print(f'  блюд: {Dish.objects.count()}')
    print(f'  ингредиентов: {DishIngredient.objects.count()}')


if __name__ == '__main__':
    load_dishes('json/dishes.json', 'Кето')
