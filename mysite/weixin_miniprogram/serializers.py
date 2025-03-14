from rest_framework import serializers
from .models import CheckList


class CheckListSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = CheckList
        fields = ['id', 'title', 'image_url',
                  'desc', 'order_num', 'items']

    def __init__(self, *args, **kwargs):
        self.depth = kwargs.pop('depth', 0)
        super().__init__(*args, **kwargs)

    def get_items(self, obj):
        if self.depth == 3:
            return []
        children = obj.get_children().order_by('order_num')
        return CheckListSerializer(children, many=True, depth=self.depth + 1).data
