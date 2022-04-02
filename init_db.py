from tgbot.models import Allergy, MenuType


def fill_allergy():
    Allergy.objects.all().delete()
    Allergy(sort_order=0, name='нет').save()
    Allergy(sort_order=1, name='Рыба и морепродукты').save()
    Allergy(sort_order=1, name='Мясо').save()
    Allergy(sort_order=1, name='Зерновые').save()
    Allergy(sort_order=1, name='Продукты пчеловодства').save()
    Allergy(sort_order=1, name='Орехи и бобовые').save()
    Allergy(sort_order=1, name='Молочные продукты').save()


def fill_menu_types():
    MenuType.objects.all().delete()
    MenuType(name='Классическое').save()
    MenuType(name='Низкоуглеводное').save()
    MenuType(name='Вегетарианское').save()
    MenuType(name='Кето').save()


if __name__ == '__main__':
    fill_allergy()
    fill_menu_types()
