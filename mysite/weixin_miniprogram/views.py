from django.shortcuts import render
from django.db.models import Q
from .models import CheckList


def checklist_tree(request):
    query = request.GET.get('q', '')
    top_nodes = CheckList.objects.filter(parent=None).order_by('order_num').prefetch_related('children')

    if query:
        nodes = CheckList.objects.filter(Q(title__icontains=query)).order_by('order_num')
    else:
        nodes = top_nodes

    return render(request,
                  'weixin_miniprogram/checklist_tree.html',
                  {'nodes': nodes, 'query': query})
