# Generated by Django 3.2.8 on 2022-02-03 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0054_remove_transaction_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='amount',
            field=models.IntegerField(default=None),
        ),
    ]