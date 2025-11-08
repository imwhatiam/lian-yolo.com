from django.contrib import admin
from django.utils.html import format_html

from .models import CheckList, Activities, WeixinUserInfo


@admin.register(CheckList)
class CheckListAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'order_num', 'image',
                    'image_preview', 'desc', 'parent')
    search_fields = ('title',)
    list_filter = ('parent',)
    ordering = ['id']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url
            )
        return "-"


@admin.register(Activities)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        'activity_title',
        'creator_avatar',
        'formatted_items',
        'formatted_white_list',
    ]

    search_fields = ['activity_title', 'creator_weixin_name', 'creator_weixin_id']
    list_per_page = 20
    ordering = ('-id',)

    def creator_avatar(self, obj):
        """Show the creator's Weixin avatar."""
        try:
            user = WeixinUserInfo.objects.get(weixin_id=obj.creator_weixin_id)
            if user.avatar:
                return format_html(
                    '<img src="{}" width="50" height="50" style="border-radius: 50%;" title="{}" />',
                    user.avatar.url,
                    user.nickname or user.weixin_id,
                )
            else:
                return user.nickname or user.weixin_id
        except WeixinUserInfo.DoesNotExist:
            return obj.creator_weixin_name or obj.creator_weixin_id

    creator_avatar.short_description = "Creator Avatar"

    def formatted_items(self, obj):
        """Pretty print activity_items JSON"""
        try:
            items = obj.activity_items
            if not items:
                return "-"
            lines = []
            for key, value in items.items():
                name = value.get("name", "")
                status = value.get("status", "")
                operator = value.get("operator", "")
                lines.append(f"<b>{key}</b>: {name} (status: {status}, operator: {operator})")
            return format_html("<br>".join(lines))
        except Exception:
            return format_html("<span style='color:red;'>Invalid JSON</span>")

    formatted_items.short_description = "Activity Items"
    formatted_items.allow_tags = True

    def formatted_white_list(self, obj):
        """Pretty print white_list JSON"""
        try:
            white_list = obj.white_list
            if not white_list:
                return "-"
            lines = []
            for entry in white_list:
                weixin_id = entry.get("weixin_id", "")
                permission = entry.get("permission", "")
                avatar_url = entry.get("avatar_url", "")
                if avatar_url:
                    lines.append(
                        f'<img src="{avatar_url}" width="25" height="25" style="border-radius:50%; margin-right:5px;">'
                        f'{weixin_id} ({permission})'
                    )
                else:
                    lines.append(f"{weixin_id} ({permission})")
            return format_html("<br>".join(lines))
        except Exception:
            return format_html("<span style='color:red;'>Invalid JSON</span>")

    formatted_white_list.short_description = "White List"
    formatted_white_list.allow_tags = True


@admin.register(WeixinUserInfo)
class WeixinUserInfoAdmin(admin.ModelAdmin):
    list_display = ['weixin_id', 'nickname', 'avatar_image']
    search_fields = ['weixin_id', 'nickname']
    readonly_fields = ['avatar_preview']

    def avatar_image(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.avatar.url
            )
        return "无头像"
    avatar_image.short_description = '头像'

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="150" height="150" style="border-radius: 50%;" />',
                obj.avatar.url
            )
        return "无头像"
    avatar_preview.short_description = '头像预览'
