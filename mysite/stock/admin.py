from django.contrib import admin
from .models import StockBasicInfo


@admin.register(StockBasicInfo)
class StockBasicInfoAdmin(admin.ModelAdmin):

    list_display = [
        "formatted_date",
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

    def formatted_date(self, obj):
        """格式化日期为 'YYYY-MM-DD'"""
        return obj.date.strftime("%Y-%m-%d")

    formatted_date.admin_order_field = "date"  # 允许按日期排序
