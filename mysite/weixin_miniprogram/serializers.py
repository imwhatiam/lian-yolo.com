from rest_framework import serializers
from .models import CheckList, Activities


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


class ActivityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activities
        fields = ['creator_weixin_id', 'creator_weixin_name',
                  'activity_title', 'activity_items', 'white_list']


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activities
        fields = '__all__'


class ActivityDeleteSerializer(serializers.Serializer):
    weixin_id = serializers.CharField(max_length=255)


class ActivityTitleUpdateSerializer(serializers.Serializer):
    weixin_id = serializers.CharField(max_length=255)
    activity_title = serializers.CharField(max_length=255)


class ActivityWhiteListUpdateSerializer(serializers.Serializer):
    weixin_id = serializers.CharField(max_length=255)
    white_list = serializers.ListField(
        child=serializers.CharField(max_length=255)
    )


class ActivityItemsAddSerializer(serializers.Serializer):
    weixin_id = serializers.CharField(max_length=255)
    activity_item_name = serializers.JSONField()


class ActivityItemUpdateSerializer(serializers.Serializer):
    weixin_id = serializers.CharField(max_length=255)
    activity_item_status = serializers.ChoiceField(
        choices=['completed', 'deleted', '']
    )


class ActivityItemDeleteSerializer(serializers.Serializer):
    weixin_id = serializers.CharField(max_length=255)
