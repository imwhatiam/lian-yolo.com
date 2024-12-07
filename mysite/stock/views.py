from django.shortcuts import render
from .models import StockBasicInfo


def fupan(request):

    return render(request, 'stock/fupan.html')
