# Generated by Django 3.2.8 on 2022-01-24 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0025_alter_block_nonce'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='nonce',
            field=models.PositiveIntegerField(null=True),
        ),
    ]