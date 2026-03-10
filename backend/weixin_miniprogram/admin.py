import time
from django.contrib import admin
from .models import Activities, WeixinUserInfo, current_timestamp


@admin.register(Activities)
class ActivitiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity_title', 'creator_weixin_name', 'activity_type', 'last_modified')
    list_filter = ('activity_type', 'last_modified')
    search_fields = ('activity_title', 'creator_weixin_name', 'creator_weixin_id')
    readonly_fields = ('last_modified',)  # 设置为只读，通过 save_model 自动更新

    def save_model(self, request, obj, form, change):
        """在更新操作时自动更新 last_modified 字段"""
        if change:
            obj.last_modified = current_timestamp()
        super().save_model(request, obj, form, change)


@admin.register(WeixinUserInfo)
class WeixinUserInfoAdmin(admin.ModelAdmin):
    list_display = ('weixin_id', 'nickname', 'avatar')
    search_fields = ('weixin_id', 'nickname')
