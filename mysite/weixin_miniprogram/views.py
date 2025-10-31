from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from .models import CheckList, Activities

from .serializers import ActivityCreateSerializer, ActivityDeleteSerializer, \
        ActivityWhiteListUpdateSerializer, ActivityItemsUpdateSerializer, \
        ActivitySerializer, ActivityTitleUpdateSerializer


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


@api_view(['GET', 'POST'])
def activities(request):

    if request.method == 'GET':

        weixin_id = request.GET.get('weixin_id')
        if not weixin_id:
            return Response({
                'error': '参数 weixin_id 不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 查找白名单中包含该微信ID的所有活动
        all_activities = Activities.objects.all()
        accessible_activities = []
        for activity in all_activities:
            if weixin_id in activity.white_list:
                accessible_activities.append(activity)

        # 使用序列化器返回数据
        serializer = ActivitySerializer(accessible_activities, many=True)

        return Response({
            'weixin_id': weixin_id,
            'count': len(accessible_activities),
            'data': serializer.data
        })

    elif request.method == 'POST':
        serializer = ActivityCreateSerializer(data=request.data)
        if serializer.is_valid():

            data = serializer.validated_data.copy()

            # ['item_1', 'item_2', 'item_3', ...]
            activity_item_list = data['activity_items']

            # {
            #     "1": {"name": "item_1", "status": "", "operator": ""},
            #     "2": {"name": "item_2", "status": "", "operator": ""},
            #     "3": {"name": "item_3", "status": "", "operator": ""}
            # }
            data['activity_items'] = {}
            for index, item_name in enumerate(activity_item_list):
                data['activity_items'][str(index + 1)] = {
                    "name": item_name,
                    "status": "",
                    "operator": ""
                }

            activity = Activities.objects.create(**data)
            serializer = ActivitySerializer(activity)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def activity(request, id):

    activity = get_object_or_404(Activities, id=id)

    if request.method == 'GET':
        serializer = ActivitySerializer(activity)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        serializer = ActivityDeleteSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # 权限验证：只有创建者可以删除活动
        if data['weixin_id'] != activity.creator_weixin_id:
            return Response({
                'error': '权限不足，只有活动创建者可以删除活动'
            }, status=status.HTTP_403_FORBIDDEN)

        # 删除活动
        activity.delete()

        return Response({
            'message': '活动删除成功'
        }, status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = ActivityTitleUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        weixin_id = data['weixin_id']
        creator_weixin_id = activity.creator_weixin_id
        if weixin_id != creator_weixin_id:
            return Response({
                'error': '权限不足，只有活动创建者可以操作白名单'
            }, status=status.HTTP_403_FORBIDDEN)

        new_activity_title = data['activity_title']
        activity.activity_title = new_activity_title
        activity.save()

        serializer = ActivitySerializer(activity)
        return Response(serializer.data)


@api_view(['PUT'])
def activity_white_list(request, id):

    activity = get_object_or_404(Activities, id=id)
    serializer = ActivityWhiteListUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    weixin_id = data['weixin_id']
    creator_weixin_id = activity.creator_weixin_id
    if weixin_id != creator_weixin_id:
        return Response({
            'error': '权限不足，只有活动创建者可以操作白名单'
        }, status=status.HTTP_403_FORBIDDEN)

    new_white_list = list(set([creator_weixin_id] + data['white_list']))
    activity.white_list = new_white_list
    activity.save()

    serializer = ActivitySerializer(activity)
    return Response(serializer.data)


@api_view(['PUT'])
def activity_items(request, id):

    activity = get_object_or_404(Activities, id=id)
    serializer = ActivityItemsUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # 权限验证：操作者必须在白名单中
    if data['weixin_id'] not in activity.white_list:
        return Response({
            'error': '权限不足，操作者不在白名单中'
        }, status=status.HTTP_403_FORBIDDEN)

    # 检查活动事项是否存在
    item_id = str(data['activity_item_id'])  # JSON键是字符串
    if item_id not in activity.activity_items:
        return Response({
            'error': f'活动事项ID {item_id} 不存在'
        }, status=status.HTTP_404_NOT_FOUND)

    current_item = activity.activity_items[item_id]

    # 检查是否可以操作：status为空或operator与当前operator一致
    if (current_item.get('status', '') != '' and current_item.get('operator', '') != data['weixin_id']):
        return Response({
            'error': '无法操作，该活动事项已被其他人操作'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 更新活动事项
    if data['activity_item_status'] == '':
        # 重置状态和操作者
        activity.activity_items[item_id]['status'] = ''
        activity.activity_items[item_id]['operator'] = ''
    else:
        activity.activity_items[item_id]['status'] = data['activity_item_status']
        activity.activity_items[item_id]['operator'] = data['weixin_id']

    activity.save()
    serializer = ActivitySerializer(activity)
    return Response(serializer.data)
