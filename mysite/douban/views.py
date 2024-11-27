from django.shortcuts import render


def zufang(request):
    return render(request, 'douban/zufang.html')


def jiaoyou(request):
    return render(request, 'douban/jiaoyou.html')
