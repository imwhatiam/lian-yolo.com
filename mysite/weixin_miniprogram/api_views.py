import os
import time
import json
import requests

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import UserActivity, CheckList
from .serializers import CheckListSerializer


class JSCode2SessionView(APIView):

    def post(self, request, *args, **kwargs):

        code = request.data.get("code")
        if not code:
            error_msg = "code is required"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        app_id = os.getenv("WEIXIN_MINIPROGRAM_APP_ID")
        app_secret = os.getenv("WEIXIN_MINIPROGRAM_APP_SECRET")
        if not app_id or not app_secret:
            error_msg = "failed to get app_id or app_secret"
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
            error_msg = "failed to get session_key"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        print(r.json())
        openid = r.json().get("openid")
        if not openid:
            error_msg = "failed to get openid"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        result = {}
        result["openid"] = openid
        return Response({"data": result}, status=status.HTTP_200_OK)


class UserActivities(APIView):

    def get(self, request, *args, **kwargs):

        openid = request.GET.get("openid")
        if not openid:
            error_msg = "openid is required"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        user_activity = UserActivity.objects.filter(openid=openid).first()
        if not user_activity:
            return Response({"data": {"activities": []}},
                            status=status.HTTP_200_OK)

        return Response({"data": {"activities": user_activity.activities}},
                        status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        openid = request.data.get("openid")
        if not openid:
            error_msg = "openid is required"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        nickname = request.data.get("nickname")
        avatar_url = request.data.get("avatar_url")
        activities = request.data.get("activities", [])
        activities_json = json.loads(activities)

        obj, created = UserActivity.objects.update_or_create(
            openid=openid,
            defaults={
                "nickname": nickname,
                "avatar_url": avatar_url,
                "activities": activities_json,
                "updated_at": int(time.time())
                }
        )

        return Response({"data": {"success": True}},
                        status=status.HTTP_200_OK)


class CheckListView(APIView):

    def get(self, request):

        checklist_id = request.GET.get('id')
        if not checklist_id:
            return Response({"error": "缺少id参数"}, status=400)

        depth = int(request.GET.get('depth', 1))
        try:
            checklist = CheckList.objects.get(id=checklist_id)
            serializer = CheckListSerializer(checklist, depth=depth)
            return Response(serializer.data)
        except CheckList.DoesNotExist:
            return Response({"error": "清单不存在"}, status=404)

    def post(self, request):
        """
        处理 POST 请求，接收子项数据并添加到数据库中。
        """
        # 获取请求数据
        parent_id = request.data.get('parent_id')
        sub_items = request.data.get('sub_items')

        # 检查参数是否完整
        if not parent_id or not sub_items:
            return Response({"error": "parent_id 和 sub_items 是必须的"}, status=400)

        # 查找父清单
        try:
            parent_checklist = CheckList.objects.get(id=parent_id)
        except CheckList.DoesNotExist:
            return Response({"error": "父清单不存在"}, status=404)

        # 添加子项
        for item in sub_items:
            for title, sub_sub_items in item.items():
                # 创建子清单
                sub_checklist = CheckList.objects.create(title=title, parent=parent_checklist)
                # 创建子子清单
                for sub_title in sub_sub_items:
                    CheckList.objects.create(title=sub_title, parent=sub_checklist)

        return Response({"message": "子项添加成功"}, status=201)
