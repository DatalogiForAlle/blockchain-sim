# Generated by Django 3.2.8 on 2022-02-02 11:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0049_auto_20220202_1220'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='sender',
            new_name='buyer',
        ),
        migrations.RenameField(
            model_name='transaction',
            old_name='recipient',
            new_name='seller',
        ),
    ]