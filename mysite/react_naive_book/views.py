import logging
from django.shortcuts import render

from .models import Lesson

logger = logging.getLogger(__name__)


def lesson(request, lesson_number):

    source_code = ""
    knowledge = ""
    try:
        lesson = Lesson.objects.filter(lesson_number=lesson_number).first()
        if lesson:
            source_code = lesson.source_code
            knowledge = lesson.knowledge
    except Exception as e:
        logger.error(e)

    lesson_numbers = [lesson.lesson_number for lesson in Lesson.objects.all()]

    data = {
        'lesson_numbers': lesson_numbers,
        'code_content': source_code,
        'markdown_content': knowledge
    }
    template = 'react_naive_book/lesson.html'
    return render(request, template, data)
