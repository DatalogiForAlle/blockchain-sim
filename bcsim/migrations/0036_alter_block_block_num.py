# Generated by Django 3.2.8 on 2022-02-01 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0035_alter_token_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='block_num',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
