# Generated by Django 5.0 on 2024-12-06 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stockbasicinfo',
            name='date',
            field=models.DateField(db_index=True),
        ),
    ]
