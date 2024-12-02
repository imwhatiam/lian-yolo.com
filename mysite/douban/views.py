from django.shortcuts import render
from django.core.paginator import Paginator
from .models import DoubanPost


def jiaoyou(request):

    only_good = request.GET.get('only_good', 'true') == 'true'
    is_new = request.GET.get('is_new', 'true') == 'true'

    posts = DoubanPost.objects.all()
    if only_good:
        posts = posts.filter(good=True)
    if is_new:
        posts = posts.filter(is_new=True)

    posts = posts.order_by('-is_new')
    posts = posts.order_by('-last_reply')

    paginator = Paginator(posts, 25)
    page_number = request.GET.get('page', 1)

    page_obj = paginator.get_page(page_number)

    data = {
        'page_obj': page_obj,
        'only_good': only_good,
        'is_new': is_new,
    }
    return render(request, 'douban/jiaoyou.html', data)


def zufang(request):
    return render(request, 'douban/zufang.html')
