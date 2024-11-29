from django.shortcuts import render
from django.core.paginator import Paginator
from .models import DoubanPost


def jiaoyou(request):

    only_good = request.GET.get('only_good', 'false') == 'true'

    if only_good:
        posts = DoubanPost.objects.filter(good=True)
    else:
        posts = DoubanPost.objects.all()

    posts = posts.order_by('-is_new')
    posts = posts.order_by('-last_reply')

    paginator = Paginator(posts, 25)
    page_number = request.GET.get('page', 1)

    page_obj = paginator.get_page(page_number)

    data = {
        'page_obj': page_obj,
        'only_good': only_good
    }
    return render(request, 'douban/jiaoyou.html', data)


def zufang(request):
    return render(request, 'douban/zufang.html')
