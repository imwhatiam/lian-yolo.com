# Generated by Django 5.0 on 2025-02-28 06:31

import weixin_miniprogram.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('openid', models.CharField(db_index=True, max_length=100, unique=True)),
                ('nickname', models.CharField(db_index=True, max_length=100)),
                ('avatar_url', models.URLField(max_length=500)),
                ('activities', models.JSONField(default=list)),
                ('created_at', models.BigIntegerField(default=weixin_miniprogram.models.current_timestamp)),
                ('updated_at', models.BigIntegerField(default=weixin_miniprogram.models.current_timestamp)),
            ],
        ),
    ]
