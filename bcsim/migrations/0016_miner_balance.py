# Generated by Django 3.2.8 on 2021-12-07 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0015_alter_blockchain_creator_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='miner',
            name='balance',
            field=models.IntegerField(default=0),
        ),
    ]
