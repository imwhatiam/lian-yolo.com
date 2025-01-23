from django.db import models


class Lesson(models.Model):

    lesson_number = models.IntegerField(db_index=True, unique=True)
    source_code = models.TextField(blank=True)
    knowledge = models.TextField(blank=True)

    def __str__(self):
        return f"lesson {self.lesson_number}, knowledge: {self.knowledge[:50]}"
