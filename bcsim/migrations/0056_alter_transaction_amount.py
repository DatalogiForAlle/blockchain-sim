# Generated by Django 3.2.8 on 2022-02-03 13:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0055_transaction_amount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]