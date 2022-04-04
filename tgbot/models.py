from __future__ import annotations

from typing import Union, Optional, Tuple

from django.db import models
from django.db.models import QuerySet, Manager
from telegram import Update
from telegram.ext import CallbackContext

from dtb.settings import DEBUG
from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, CreateTracker
from utils.models import GetOrNoneManager
from django.db import models
from django.db.models import Q
import random


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(max_length=8,
                                     help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)

    is_blocked_bot = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Телефон (+код xxx xxx-xx-xx)'
    )

    objects = GetOrNoneManager()
    admins = AdminUserManager()

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(
            user_id=data["user_id"],
            defaults=data
        )

        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                if str(payload).strip() != str(data["user_id"]).strip():
                    u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        u, _ = cls.get_user_and_created(update, context)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(
            deep_link=str(self.user_id),
            created_at__gt=self.created_at
        )

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" \
            if self.last_name else f"{self.first_name}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = '_Пользователи'


class Location(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()

    objects = GetOrNoneManager()

    def __str__(self):
        return f"user: {self.user}" \
               f", created at {self.created_at.strftime('(%H:%M, %d %B %Y)')}"

    def save(self, *args, **kwargs):
        super(Location, self).save(*args, **kwargs)
        # Parse location with arcgis
        from arcgis.tasks import save_data_from_arcgis
        if DEBUG:
            save_data_from_arcgis(
                latitude=self.latitude,
                longitude=self.longitude,
                location_id=self.pk
            )
        else:
            save_data_from_arcgis.delay(
                latitude=self.latitude,
                longitude=self.longitude,
                location_id=self.pk
            )


class MenuType(models.Model):
    name = models.CharField(
        max_length=255, unique=True, blank=False, default='',
        verbose_name='Наименование меню',
    )

    class Meta:
        verbose_name = 'Тип меню'
        verbose_name_plural = 'Типы меню'

    def __str__(self):
        return self.name


class Allergy(models.Model):
    name = models.CharField(
        max_length=255, unique=True, blank=False, default='',
        verbose_name='Наименование аллергии',
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )

    class Meta:
        verbose_name = 'Аллергия'
        verbose_name_plural = 'Аллергии'

    def __str__(self):
        return self.name


class Dish(models.Model):
    menu_type = models.ForeignKey(
        MenuType,
        on_delete=models.CASCADE,
        null=True,
        verbose_name='Тип меню',
        related_name='dish_menu_type'
    )
    name = models.CharField(
        max_length=255, blank=False, default='',
        verbose_name='Наименование',
    )
    description = models.CharField(
        max_length=2048, blank=True,
        verbose_name='Описание',
    )
    recipe = models.CharField(
        max_length=2048, blank=True,
        verbose_name='Рецепт приготовления',
    )
    calories = models.CharField(
        max_length=20, blank=False,
        default='',
        verbose_name='Калорийность',
    )
    picture = models.URLField(
        max_length=4096,
        verbose_name='Ссылка на картинку',
    )

    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'

    def __str__(self):
        return f'Блюдо "{self.name}"'

    def get_allergies(self):
        dish_allergy = []
        for dish_ingredient in self.ingredient_dish.all():
            dish_allergy = set(dish_allergy) | \
                set(dish_ingredient.allergy.filter(~Q(name="нет")))
        return dish_allergy

    def get_full_description(self):
        dish_description = f'''{self.picture}
Блюдо: {self.name}
Описание: {self.description}
Рецепт приготовления: {self.recipe}
Калорийность: {self.calories}
Ингредиенты:
'''
        for ingredient in self.ingredient_dish.all():
            dish_description += f'{ingredient.name}, {ingredient.amount}, ' \
                                f'{ingredient.unit}\n'
        return dish_description


class DishIngredient(models.Model):
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        verbose_name='Блюдо',
        related_name='ingredient_dish'
    )
    name = models.CharField(
        max_length=255, blank=False, default='',
        verbose_name='Ингредиент'
    )
    amount = models.CharField(
        max_length=20, default='',
        verbose_name='Количество'
    )
    unit = models.CharField(
        max_length=255, blank=False, default='',
        verbose_name='Единица измерения'
    )
    allergy = models.ManyToManyField(
        Allergy,
        related_name='ingredient_allergy',
    )

    class Meta:
        verbose_name = 'Ингредиент блюда'
        verbose_name_plural = 'Ингредиенты блюд'

    def __str__(self):
        return f'Блюдо "{self.name}"'


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscribe_user'
    )
    number_of_meals = models.IntegerField(
        blank=False, default=1,
        verbose_name='Количество приёмов пищи за день',
    )
    number_of_person = models.IntegerField(
        blank=False, default=1,
        verbose_name='Количество персон',
    )
    allergy = models.ManyToManyField(
        Allergy,
        verbose_name='Аллергии',
    )
    menu_type = models.ForeignKey(
        MenuType,
        on_delete=models.DO_NOTHING,
        verbose_name='Тип меню',
        related_name='subscribe_menu_type'
    )
    duration = models.IntegerField(
        default=1,
        verbose_name='Длительность подписки, мес.',
    )
    subscription_paid = models.BooleanField(
        blank=False,
        default=False,
        verbose_name='Подписка оплачена'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписка'

    def __str__(self):
        return f'Подписка "{self.id}"'

    def get_subscribe_dish(self):
        menu_type_dishes = Dish.objects.filter(menu_type=self.menu_type)
        subs_allergies = set(self.allergy.filter(~Q(name="нет")))
        # print(f'subs_allergies: {subs_allergies}')
        dishes = []
        # for dish in menu_type_dishes:
        for dish in Dish.objects.filter(menu_type=self.menu_type):
            dish_allergies = dish.get_allergies()
            # if not dish_allergies & subs_allergies:
            if not dish.get_allergies() & subs_allergies:
                dishes.append(dish)
        return dishes[random.randint(0, len(dishes) - 1)]
