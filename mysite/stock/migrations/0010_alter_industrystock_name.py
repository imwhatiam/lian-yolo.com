# Generated by Django 5.0 on 2025-02-13 02:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0009_industrystock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='industrystock',
            name='name',
            field=models.CharField(db_index=True, max_length=100),
        ),
    ]
