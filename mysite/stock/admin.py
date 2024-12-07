from django.contrib import admin
from .models import StockBasicInfo


@admin.register(StockBasicInfo)
class StockBasicInfoAdmin(admin.ModelAdmin):
    list_display = [
        "date",
        "code",
        "name",
        "open_price",
        "close_price",
        "high_price",
        "low_price",
        "money",
    ]
    ordering = ["-date"]  # 按日期倒序排序
    search_fields = ["name", "code"]  # 支持按名称和代码搜索
    list_filter = ["date"]  # 过滤器
    list_per_page = 20  # 每页显示 20 条记录
