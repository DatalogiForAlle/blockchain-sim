# Generated by Django 3.2.8 on 2022-02-03 10:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0051_auto_20220202_1358'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='in_queue',
            new_name='processed',
        ),
    ]
