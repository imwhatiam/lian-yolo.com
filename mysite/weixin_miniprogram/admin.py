from django.contrib import admin
from django.utils.html import format_html
from .models import UserActivity, CheckList


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('openid', 'nickname', 'avatar_image',
                    'formatted_activities', 'created_at', 'updated_at')
    readonly_fields = ('avatar_image', 'created_at', 'updated_at')

    def avatar_image(self, obj):
        if obj.avatar_url:
            return format_html('<img src="{}" width="50" height="50" />', obj.avatar_url)
        return "-"

    def formatted_activities(self, obj):
        """
        格式化 activities 字段显示：
        - 每个活动以活动名称为标题
        - 下方显示所有活动条目，包含名称、完成状态、删除状态
        """
        try:
            activities = obj.activities
            if not activities:
                return "-"
            html = "<div>"
            for activity in activities:
                activity_name = activity.get("activityName", "未命名活动")
                html += f"<div style='margin-bottom:10px;'><strong>{activity_name}</strong>"
                html += "<ul style='margin: 0 0 0 15px;'>"
                items = activity.get("activityItems", [])
                for item in items:
                    # 对于完成状态，可能存在 "complete" 或 "completed" 键
                    complete = item.get("complete", item.get("completed", False))
                    status = "已完成" if complete else "未完成"
                    # 如果 deleted 为 True，则标记为已删除
                    if item.get("deleted", False):
                        status += " (已删除)"
                    item_name = item.get("itemName", "")
                    html += f"<li>{item_name} - {status}</li>"
                html += "</ul></div>"
            html += "</div>"
            return format_html(html)
        except Exception as e:
            return str(e)

    formatted_activities.short_description = "活动详情"

    avatar_image.short_description = "Avatar"


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
