# Generated by Django 3.2.12 on 2022-04-03 07:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0003_auto_20220402_0936'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='allergy',
            options={'ordering': ['sort_order'], 'verbose_name': 'Аллергия', 'verbose_name_plural': 'Аллергии'},
        ),
    ]
