# Generated by Django 3.2.12 on 2022-04-02 01:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0011_alter_dishingredient_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Телефон (+код xxx xxx-xx-xx)'),
        ),
        migrations.AlterField(
            model_name='dish',
            name='calories',
            field=models.CharField(default='', max_length=20, verbose_name='Калорийность'),
        ),
        migrations.AlterField(
            model_name='dish',
            name='picture',
            field=models.URLField(max_length=1024, verbose_name='Ссылка на картинку'),
        ),
        migrations.RemoveField(
            model_name='subscribe',
            name='allergy',
        ),
        migrations.AddField(
            model_name='subscribe',
            name='allergy',
            field=models.ManyToManyField(to='tgbot.Allergy', verbose_name='Аллергии'),
        ),
    ]
