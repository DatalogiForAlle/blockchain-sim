# Generated by Django 3.2.8 on 2021-12-06 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0010_auto_20211206_1234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='block_id',
            field=models.IntegerField(),
        ),
    ]
