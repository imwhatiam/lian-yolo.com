from rest_framework import serializers
from .models import CheckList


class CheckListSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = CheckList
        fields = ['id', 'title', 'items']

    def __init__(self, *args, **kwargs):
        self.depth = kwargs.pop('depth', 0)
        super().__init__(*args, **kwargs)

    def get_items(self, obj):
        if self.depth == 3:
            return []

        chinese_order = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                         '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}

        children = sorted(
            obj.get_children(),
            key=lambda x: (chinese_order.get(x.title[0], 99), x.title),
            reverse=True
        )
        return CheckListSerializer(children, many=True, depth=self.depth + 1).data
