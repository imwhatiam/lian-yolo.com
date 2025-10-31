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

    list_display = ('openid', 'nickname', 'avatar')
    search_fields = ('nickname',)

    def avatar(self, obj):
        if obj.avatar_url:
            return format_html(
                '<img src="{}" style="max-height: 30px; max-width: 30px;" />',
                obj.avatar_url
            )
        return "-"
