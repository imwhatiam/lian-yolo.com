from django.shortcuts import render
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page

from .models import DoubanPost


# Cache this view for 24 hours
@cache_page(60 * 60 * 24)
def jiaoyou(request):

    only_good = request.GET.get('only_good', 'false') == 'true'
    is_new = request.GET.get('is_new', 'false') == 'true'
    title = request.GET.get('title', '')

    posts = DoubanPost.objects.all()
    if only_good:
        posts = posts.filter(good=True)
    if is_new:
        posts = posts.filter(is_new=True)
    if title:
        posts = posts.filter(title__icontains=title)

    posts = posts.order_by('-is_new')
    posts = posts.order_by('-last_reply')

    paginator = Paginator(posts, 25)
    page_number = request.GET.get('page', 1)

    page_obj = paginator.get_page(page_number)

    data = {
        'page_obj': page_obj,
        'only_good': only_good,
        'is_new': is_new,
        'title': title,
    }
    return render(request, 'douban/jiaoyou.html', data)


def zufang(request):
    return render(request, 'douban/zufang.html')
