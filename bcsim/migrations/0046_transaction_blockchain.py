# Generated by Django 3.2.8 on 2022-02-01 15:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bcsim', '0045_alter_transaction_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='blockchain',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bcsim.blockchain'),
        ),
    ]
