# Generated by Django 3.2.12 on 2022-03-31 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0009_auto_20220331_1310'),
    ]

    operations = [
        migrations.AddField(
            model_name='dishingredient',
            name='allergy',
            field=models.ManyToManyField(related_name='ingredient_allergy', to='tgbot.Allergy'),
        ),
    ]