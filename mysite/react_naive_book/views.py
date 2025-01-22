import logging
from django.shortcuts import render

from .models import Lessons

logger = logging.getLogger(__name__)


def lesson(request, lesson_number):

    source_code = ""
    knowledge = ""
    try:
        lesson = Lessons.objects.filter(lesson_number=lesson_number).first()
        if lesson:
            source_code = lesson.source_code
            knowledge = lesson.knowledge
    except Exception as e:
        logger.error(e)

    data = {
        'lesson_number': lesson_number,
        'code_content': source_code,
        'markdown_content': knowledge
    }
    template = 'react_naive_book/lesson.html'
    return render(request, template, data)
