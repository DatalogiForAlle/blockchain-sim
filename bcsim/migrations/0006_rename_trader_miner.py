# Generated by Django 3.2.8 on 2021-12-01 11:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0005_trader'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Trader',
            new_name='Miner',
        ),
    ]