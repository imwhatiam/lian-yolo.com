# Generated by Django 5.0 on 2025-01-18 07:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0006_alter_industris_name_alter_stockbasicinfo_name_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='StockBasicInfo',
            new_name='StockTradeInfo',
        ),
    ]