# Generated by Django 5.0 on 2025-01-17 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0004_industris_stocks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='industris',
            name='name',
            field=models.CharField(db_index=True, max_length=10),
        ),
    ]
