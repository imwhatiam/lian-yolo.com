from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from .models import CheckList, Activity

from .serializers import ActivityCreateSerializer, WhiteListUpdateSerializer, \
        ActivityItemUpdateSerializer, ActivityItemAddSerializer, ActivitySerializer


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


@api_view(['POST'])
def create_activity(request):
    """
    1. 创建活动
    """
    serializer = ActivityCreateSerializer(data=request.data)
    if serializer.is_valid():
        # 设置白名单默认为创建者的微信ID
        activity_data = serializer.validated_data.copy()
        activity_data['white_list'] = [activity_data['creator_weixin_id']]

        activity = Activity.objects.create(**activity_data)
        return Response({
            'id': activity.id,
            'message': '活动创建成功'
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def add_white_list(request, id):
    """
    2. 白名单中新增
    """
    activity = get_object_or_404(Activity, id=id)
    serializer = WhiteListUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # 权限验证：只有创建者可以操作
    if data['creator_weixin_id'] != activity.creator_weixin_id:
        return Response({
            'error': '权限不足，只有活动创建者可以操作白名单'
        }, status=status.HTTP_403_FORBIDDEN)

    # 添加新的微信ID到白名单（去重）
    current_white_list = activity.white_list
    new_white_list = list(set(current_white_list + data['guest_weixin_id_list']))

    activity.white_list = new_white_list
    activity.save()

    return Response({
        'message': '白名单添加成功',
        'white_list': new_white_list
    })


@api_view(['PUT'])
def remove_white_list(request, id):
    """
    3. 白名单中删除
    """
    activity = get_object_or_404(Activity, id=id)
    serializer = WhiteListUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # 权限验证：只有创建者可以操作
    if data['creator_weixin_id'] != activity.creator_weixin_id:
        return Response({
            'error': '权限不足，只有活动创建者可以操作白名单'
        }, status=status.HTTP_403_FORBIDDEN)

    # 从白名单中移除指定的微信ID
    current_white_list = activity.white_list
    new_white_list = [weixin_id for weixin_id in current_white_list if weixin_id not in data['guest_weixin_id_list']]

    # 确保创建者始终在白名单中
    if activity.creator_weixin_id not in new_white_list:
        new_white_list.append(activity.creator_weixin_id)

    activity.white_list = new_white_list
    activity.save()

    return Response({
        'message': '白名单删除成功',
        'white_list': new_white_list
    })


@api_view(['PUT'])
def update_activity_item(request, id):
    """
    4. 更新活动事项
    """
    activity = get_object_or_404(Activity, id=id)
    serializer = ActivityItemUpdateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    item_id = str(data['activity_item_id'])  # JSON键是字符串

    # 权限验证：操作者必须在白名单中
    if data['activity_item_operator'] not in activity.white_list:
        return Response({
            'error': '权限不足，操作者不在白名单中'
        }, status=status.HTTP_403_FORBIDDEN)

    # 检查活动事项是否存在
    if item_id not in activity.activity_item:
        return Response({
            'error': f'活动事项ID {item_id} 不存在'
        }, status=status.HTTP_404_NOT_FOUND)

    current_item = activity.activity_item[item_id]

    # 检查是否可以操作：status为空或operator与当前operator一致
    if (current_item.get('status', '') != '' and current_item.get('operator', '') != data['activity_item_operator']):
        return Response({
            'error': '无法操作，该活动事项已被其他人操作'
        }, status=status.HTTP_400_BAD_REQUEST)

    # 更新活动事项
    if data['activity_item_status'] == '':
        # 重置状态和操作者
        activity.activity_item[item_id]['status'] = ''
        activity.activity_item[item_id]['operator'] = ''
    else:
        activity.activity_item[item_id]['status'] = data['activity_item_status']
        activity.activity_item[item_id]['operator'] = data['activity_item_operator']

    activity.save()

    return Response({
        'message': '活动事项更新成功',
        'activity_item': activity.activity_item[item_id]
    })


@api_view(['PUT'])
def add_activity_item(request, id):
    """
    5. 新增活动事项
    """
    activity = get_object_or_404(Activity, id=id)
    serializer = ActivityItemAddSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # 权限验证：只有创建者可以添加活动事项
    if data['creator_weixin_id'] != activity.creator_weixin_id:
        return Response({
            'error': '权限不足，只有活动创建者可以添加活动事项'
        }, status=status.HTTP_403_FORBIDDEN)

    # 生成新的活动事项ID
    existing_ids = [int(key) for key in activity.activity_item.keys() if key.isdigit()]
    new_item_id = max(existing_ids) + 1 if existing_ids else 1

    # 添加新的活动事项
    activity.activity_item[str(new_item_id)] = data['activity_item']
    activity.save()

    return Response({
        'message': '活动事项添加成功',
        'new_item_id': new_item_id,
        'activity_item': data['activity_item']
    })


@api_view(['GET'])
def get_activity_detail(request, id):
    """
    获取活动详情
    """
    activity = get_object_or_404(Activity, id=id)
    serializer = ActivitySerializer(activity)
    return Response(serializer.data)
