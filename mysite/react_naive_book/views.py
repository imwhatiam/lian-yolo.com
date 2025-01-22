from django.shortcuts import render

from .content import get_code_content, get_markdown_content


def lesson(request, lesson_number):

    template = 'react_naive_book/lesson.html'
    code_content = get_code_content(int(lesson_number))
    markdown_content = get_markdown_content(int(lesson_number))
    data = {
        'lesson_number': lesson_number,
        'code_content': code_content,
        'markdown_content': markdown_content
    }
    return render(request, template, data)
