# Generated by Django 5.0 on 2025-01-22 10:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('react_naive_book', '0002_alter_lessons_lesson_number'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Lessons',
            new_name='Lesson',
        ),
    ]
