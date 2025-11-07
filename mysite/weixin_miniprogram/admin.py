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
        'id',
        'activity_title',
        'creator_weixin_name',
        'creator_weixin_id',
        'white_list',
    ]

    search_fields = [
        'activity_title',
        'creator_weixin_name',
        'creator_weixin_id'
    ]

    list_per_page = 20

    ordering = ('-id',)


@admin.register(WeixinUserInfo)
class WeixinUserInfoAdmin(admin.ModelAdmin):
    list_display = ['weixin_id', 'nickname', 'avatar_image']
    search_fields = ['weixin_id', 'nickname']
    readonly_fields = ['avatar_preview']

    def avatar_image(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.avatar.url)
        return "无头像"
    avatar_image.short_description = '头像'

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="150" height="150" style="border-radius: 50%;" />', obj.avatar.url)
        return "无头像"
    avatar_preview.short_description = '头像预览'
