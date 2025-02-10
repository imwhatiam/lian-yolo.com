from django.shortcuts import render


def index(request):

    return render(request, 'index.html')


def react_home(request):

    return render(request, 'react-home.html')
