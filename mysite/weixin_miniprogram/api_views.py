import os
import time
import json
import requests

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from .models import UserActivity, CheckList
from .serializers import CheckListSerializer
from utils.admin_permission import PostAdminOnly, DeleteAdminOnly


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

        openid = r.json().get("openid")
        if not openid:
            error_msg = "failed to get openid"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        result = {}
        result["openid"] = openid
        return Response({"data": result}, status=status.HTTP_200_OK)


class UserActivities(APIView):

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [PostAdminOnly]

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
