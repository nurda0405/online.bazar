# Generated by Django 5.1.1 on 2024-11-19 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram', '0003_allowed_seller_phone_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='allowed_seller',
            name='name',
            field=models.TextField(default='name'),
            preserve_default=False,
        ),
    ]
