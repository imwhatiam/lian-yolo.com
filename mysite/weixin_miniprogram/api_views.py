import os
import logging
import requests
from functools import wraps

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from django.db import connection
from django.core.cache import cache

from .models import CheckList, WeixinUserInfo, Activities
from .serializers import CheckListSerializer
from utils.admin_permission import PostAdminOnly, DeleteAdminOnly

logger = logging.getLogger(__name__)


class JSCode2SessionView(APIView):

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):

        code = request.data.get("code")
        if not code:
            error_msg = "code is required"
            logger.error(error_msg)
            logger.error(request.data)
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        app_id = os.getenv("WEIXIN_MINIPROGRAM_APP_ID")
        app_secret = os.getenv("WEIXIN_MINIPROGRAM_APP_SECRET")
        if not app_id or not app_secret:
            error_msg = "failed to get app_id or app_secret"
            logger.error(error_msg)
            logger.error(request.data)
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        grant_type = os.getenv("WEIXIN_MINIPROGRAM_GRANT_TYPE",
                               "authorization_code")
        url = os.getenv("WEIXIN_MINIPROGRAM_JSCODE2SESSION_URL",
                        "https://api.weixin.qq.com/sns/jscode2session")

        params = {
            "appid": app_id,
            "secret": app_secret,
            "js_code": code,
            "grant_type": grant_type,
        }

        r = requests.get(url, params=params)
        if r.status_code != 200:
            error_msg = "failed to get openid"
            logger.error(error_msg)
            logger.error(request.data)
            logger.error(r.json())
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        openid = r.json().get("openid")
        if not openid:
            error_msg = "failed to get openid"
            logger.error(error_msg)
            logger.error(request.data)
            logger.error(r.json())
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        openid = 'lian-weixin-id'
        nickname = request.data.get("nickname", "")

        avatar_file = request.FILES.get('avatar')
        user_info, _ = WeixinUserInfo.objects.get_or_create(weixin_id=openid)

        if user_info.avatar:
            user_info.avatar.delete(save=False)

        user_info.nickname = nickname
        user_info.avatar = avatar_file
        user_info.save()

        data = {}
        data["weixin_id"] = user_info.weixin_id
        data["nickname"] = user_info.nickname
        data["avatar_url"] = request.build_absolute_uri(user_info.avatar.url)

        return Response(data)


class CheckListView(APIView):

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [PostAdminOnly, DeleteAdminOnly]

    def get(self, request):

        if 'id' not in request.GET:
            error_msg = "id is required"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        checklist_id = request.GET.get('id')
        try:
            checklist_id = int(checklist_id)
        except (TypeError, ValueError):
            error_msg = f"id {checklist_id} is not a valid integer"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        if checklist_id < 0:
            error_msg = f"id {checklist_id} can not be negative"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        depth = request.GET.get('depth', 1)
        try:
            depth = int(depth)
        except (TypeError, ValueError):
            error_msg = f"depth {depth} is not a valid integer"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            checklist = CheckList.objects.get(id=checklist_id)
            serializer = CheckListSerializer(checklist, depth=depth)
            return Response(serializer.data)
        except CheckList.DoesNotExist:
            error_msg = "CheckList does not exist"
            return Response({"error": error_msg}, status=404)

    def post(self, request):

        if 'parent_id' not in request.data:
            error_msg = "parent_id is required"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        parent_id = request.data['parent_id']
        try:
            parent_id = int(parent_id)
        except (TypeError, ValueError):
            error_msg = f"parent_id {parent_id} is not a valid integer"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        if parent_id < 0:
            error_msg = f"parent_id {parent_id} can not be negative"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        sub_items = request.data.get('sub_items')
        if not sub_items:
            error_msg = "sub_items is required"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            parent_checklist = CheckList.objects.get(id=parent_id)
        except CheckList.DoesNotExist:
            error_msg = f"parent_id {parent_id} does not exist"
            return Response({"error": error_msg},
                            status=status.HTTP_404_NOT_FOUND)

        for order, item in enumerate(sub_items, start=1):
            for title, sub_sub_items in item.items():
                sub_checklist = CheckList.objects.create(
                    title=title,
                    parent=parent_checklist,
                    order_num=order
                )
                for sub_order, sub_title in enumerate(sub_sub_items, start=1):
                    CheckList.objects.create(
                        title=sub_title,
                        parent=sub_checklist,
                        order_num=sub_order
                    )

        return Response({"message": "Sub-items added successfully"}, status=201)

    def delete(self, request):

        if 'parent_id' not in request.data:
            error_msg = "parent_id is required"
            return Response({"error": error_msg}, status=400)

        parent_id = request.data.get('parent_id')
        try:
            parent_id = int(parent_id)
        except (TypeError, ValueError):
            error_msg = f"parent_id {parent_id} is not a valid integer"
            return Response({"error": error_msg}, status=400)

        if parent_id < 0:
            error_msg = f"parent_id {parent_id} can not be negative"
            return Response({"error": error_msg}, status=400)

        try:
            parent_checklist = CheckList.objects.get(id=parent_id)
        except CheckList.DoesNotExist:
            error_msg = "parent checklist does not exist"
            return Response({"error": error_msg}, status=404)

        children = parent_checklist.children.all()
        children.delete()

        return Response(
            {"message": f"All sub-items under parent node {parent_id} have been deleted"},
            status=status.HTTP_200_OK)


class CheckListSearchView(APIView):

    def get(self, request):

        if 'keyword' not in request.GET:
            error_msg = "keyword is required"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        keyword = request.GET.get('keyword')
        checklists = CheckList.objects.filter(title__icontains=keyword)
        serializer = CheckListSerializer(checklists, many=True)
        return Response(serializer.data)


def require_activity_exists(view_func):
    """
    装饰器：验证活动是否存在
    """
    @wraps(view_func)
    def wrapper(self, request, activity_id, *args, **kwargs):
        try:
            activity = Activities.objects.get(id=activity_id)
        except Activities.DoesNotExist:
            return Response({
                'error': '活动不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        # 将活动对象传递给视图方法
        return view_func(self, request, activity, *args, **kwargs)
    return wrapper


def get_avatar_url(request, weixin_id):
    cache_key = f"avatar_url_{weixin_id}"
    avatar_url = cache.get(cache_key)

    if not avatar_url:
        try:
            user_info = WeixinUserInfo.objects.get(weixin_id=weixin_id)
            avatar_url = request.build_absolute_uri(user_info.avatar.url)
            cache.set(cache_key, avatar_url)
        except WeixinUserInfo.DoesNotExist:
            avatar_url = ''

    return avatar_url


def serialize_activity(request, activity):

    items_with_avatar_url = {}
    for key, item in activity.activity_items.items():

        operator = item.get('operator', '')
        if item['status'] != '' and operator:
            item['operator_avatar_url'] = get_avatar_url(request, operator)
        else:
            item['operator_avatar_url'] = ''

        items_with_avatar_url[key] = item

    white_list_with_avatar_url = []
    for item in activity.white_list:
        avatar_url = get_avatar_url(request, item.get('weixin_id', ''))
        item['avatar_url'] = avatar_url
        white_list_with_avatar_url.append(item)

    return {
        'id': activity.id,
        'creator_weixin_id': activity.creator_weixin_id,
        'creator_weixin_name': activity.creator_weixin_name,
        'activity_title': activity.activity_title,
        'activity_items': items_with_avatar_url,
        'white_list': white_list_with_avatar_url
    }


class ActivitiesView(APIView):
    """
    处理活动列表的获取和创建
    GET: 获取用户可访问的活动列表
    POST: 创建新活动
    """

    def get(self, request):

        weixin_id = request.GET.get('weixin_id')
        if not weixin_id:
            return Response({
                'error': '参数 weixin_id 不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        if connection.vendor == 'sqlite':
            accessible_activities = Activities.objects.filter(white_list__icontains=weixin_id)
        else:
            accessible_activities = Activities.objects.filter(white_list__contains=[weixin_id])

        # 手动序列化数据
        serialized_data = []
        for activity in accessible_activities:
            serialized_data.append(serialize_activity(request, activity))

        return Response({
            'count': len(accessible_activities),
            'data': serialized_data
        })

    def post(self, request):

        data = request.data

        # 手动验证必需字段
        required_fields = ['creator_weixin_id', 'activity_title', 'activity_items']
        for field in required_fields:
            if field not in data:
                return Response({
                    'error': f'字段 {field} 是必需的'
                }, status=status.HTTP_400_BAD_REQUEST)

        # 处理活动事项列表
        activity_item_list = data['activity_items']
        if not isinstance(activity_item_list, list):
            return Response({
                'error': 'activity_items 必须是列表'
            }, status=status.HTTP_400_BAD_REQUEST)

        processed_activity_items = {}
        for index, item_name in enumerate(activity_item_list):
            processed_activity_items[str(index + 1)] = {
                "name": item_name,
                "status": "",
                "operator": ""
            }

        creator_weixin_id = data['creator_weixin_id']
        white_list = [
            {
                'weixin_id': creator_weixin_id,
                'avatar_url': get_avatar_url(request, creator_weixin_id),
                'permission': 'creator'
            }
        ]

        # 创建活动
        activity = Activities.objects.create(
            creator_weixin_id=data['creator_weixin_id'],
            creator_weixin_name=data['creator_weixin_name'],
            activity_title=data['activity_title'],
            activity_items=processed_activity_items,
            white_list=white_list
        )

        return Response(serialize_activity(request, activity))


class ActivityView(APIView):
    """
    处理单个活动的详情、更新和删除
    GET: 获取活动详情
    PUT: 更新活动标题
    DELETE: 删除活动
    """

    @require_activity_exists
    def get(self, request, activity):

        weixin_id = request.GET.get('weixin_id')
        if not weixin_id:
            return Response({
                'error': '参数 weixin_id 不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        # add new visitor to white list
        white_list = activity.white_list
        if weixin_id not in white_list:
            white_list.append({
                'weixin_id': weixin_id,
                'avatar_url': get_avatar_url(request, weixin_id),
                'permission': ''
            })

        activity.white_list = white_list
        activity.save()

        return Response(serialize_activity(request, activity))

    @require_activity_exists
    def put(self, request, activity):

        data = request.data
        weixin_id = data.get('weixin_id')
        new_title = data.get('activity_title')

        if not weixin_id:
            return Response({
                'error': 'weixin_id 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not new_title:
            return Response({
                'error': 'activity_title 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 权限验证：只有创建者可以更新活动标题
        if weixin_id != activity.creator_weixin_id:
            return Response({
                'error': '权限不足，只有活动创建者可以更新活动标题'
            }, status=status.HTTP_403_FORBIDDEN)

        # 更新活动标题
        activity.activity_title = new_title
        activity.save()

        return Response(serialize_activity(request, activity))

    @require_activity_exists
    def delete(self, request, activity):

        data = request.data
        weixin_id = data.get('weixin_id')

        if not weixin_id:
            return Response({
                'error': 'weixin_id 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 权限验证：只有创建者可以删除活动
        if weixin_id != activity.creator_weixin_id:
            return Response({
                'error': '权限不足，只有活动创建者可以删除活动'
            }, status=status.HTTP_403_FORBIDDEN)

        # 删除活动
        activity.delete()

        return Response({
            'message': '活动删除成功'
        }, status=status.HTTP_200_OK)


class ActivityWhiteListView(APIView):
    """
    处理活动白名单的更新
    PUT: 更新活动白名单
    """

    @require_activity_exists
    def put(self, request, activity):

        data = request.data
        weixin_id = data.get('weixin_id')
        white_list_dict = data.get('white_list')

        if not weixin_id:
            return Response({
                'error': 'weixin_id 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        if white_list_dict is None:
            return Response({
                'error': 'white_list 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(white_list_dict, dict):
            return Response({
                'error': 'white_list 必须是 dict 类型'
            }, status=status.HTTP_400_BAD_REQUEST)

        permission = white_list_dict['permission']
        if permission not in ('admin', ''):
            return Response({
                'error': 'white_list 中的 permission 必须是 "admin" 或 ""'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 权限验证：只有创建者可以操作白名单
        if weixin_id != activity.creator_weixin_id:
            return Response({
                'error': '权限不足，只有活动创建者可以操作白名单'
            }, status=status.HTTP_403_FORBIDDEN)

        white_list_exists = False
        new_white_list = []
        for dict_item in activity.white_list:
            if dict_item['weixin_id'] == white_list_dict['weixin_id']:
                white_list_exists = True
                dict_item.update(white_list_dict)

            new_white_list.append(dict_item)

        if not white_list_exists:
            new_white_list.append(white_list_dict)

        activity.white_list = new_white_list
        activity.save()

        return Response(serialize_activity(request, activity))


class ActivityItemsView(APIView):
    """
    处理活动事项的添加
    POST: 添加新的活动事项
    """

    @require_activity_exists
    def post(self, request, activity):

        data = request.data
        weixin_id = data.get('weixin_id')
        item_name = data.get('activity_item_name')

        if not weixin_id:
            return Response({
                'error': 'weixin_id 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not item_name:
            return Response({
                'error': 'activity_item_name 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 权限验证：只有创建者可以更新活动标题
        if weixin_id != activity.creator_weixin_id:
            return Response({
                'error': '权限不足，只有活动创建者可以新增活动事项'
            }, status=status.HTTP_403_FORBIDDEN)

        # 找到最大的键值并生成下一个键
        if activity.activity_items:
            max_key = max(int(k) for k in activity.activity_items.keys())
            next_key = str(max_key + 1)
        else:
            next_key = "1"
            activity.activity_items = {}

        # 添加新的事项
        activity.activity_items[next_key] = {
            "name": item_name,
            "status": "",
            "operator": ""
        }
        activity.save()

        return Response(serialize_activity(request, activity))


class ActivityItemView(APIView):
    """
    处理单个活动事项的更新和删除
    PUT: 更新活动事项状态
    DELETE: 删除活动事项
    """

    @require_activity_exists
    def put(self, request, activity, item_id):

        data = request.data
        weixin_id = data.get('weixin_id')
        item_status = data.get('activity_item_status')

        if not weixin_id:
            return Response({
                'error': 'weixin_id 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        if item_status is None:
            return Response({
                'error': 'activity_item_status 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        if item_status not in ['completed', 'deleted', '']:
            return Response({
                'error': 'activity_item_status 必须是 "completed", "deleted" 或空字符串'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 权限验证：操作者必须在白名单中
        if weixin_id not in [item['weixin_id'] for item in activity.white_list]:
            return Response({
                'error': '权限不足，操作者不在白名单中'
            }, status=status.HTTP_403_FORBIDDEN)

        # 检查事项是否存在
        if item_id not in activity.activity_items:
            return Response({
                'error': f'活动事项ID {item_id} 不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        current_item = activity.activity_items[item_id]

        # 检查是否可以更新：状态为空或操作者是同一个人
        if (current_item.get('status', '') != '' and
                current_item.get('operator', '') != weixin_id):
            return Response({
                'error': '无法操作，该活动事项已被其他人操作'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 更新事项状态
        if item_status == '':
            activity.activity_items[item_id]['status'] = ''
            activity.activity_items[item_id]['operator'] = ''
        else:
            activity.activity_items[item_id]['status'] = item_status
            activity.activity_items[item_id]['operator'] = weixin_id

        activity.save()

        return Response(serialize_activity(request, activity))

    @require_activity_exists
    def delete(self, request, activity, item_id):

        data = request.data
        weixin_id = data.get('weixin_id')

        if not weixin_id:
            return Response({
                'error': 'weixin_id 是必需的'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 权限验证：操作者必须在白名单中
        if weixin_id != activity.creator_weixin_id:
            return Response({
                'error': '权限不足，只有活动创建者可以删除活动事项'
            }, status=status.HTTP_403_FORBIDDEN)

        # 检查事项是否存在
        if item_id not in activity.activity_items:
            return Response({
                'error': f'活动事项ID {item_id} 不存在'
            }, status=status.HTTP_404_NOT_FOUND)

        # 删除事项
        activity.activity_items.pop(item_id)
        activity.save()

        return Response(serialize_activity(request, activity))
