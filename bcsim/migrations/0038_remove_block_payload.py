# Generated by Django 3.2.8 on 2022-02-01 12:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0037_alter_block_nonce'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='block',
            name='payload',
        ),
    ]