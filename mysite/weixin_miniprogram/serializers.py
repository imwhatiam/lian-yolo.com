from rest_framework import serializers
from .models import CheckList, Activity


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
        model = Activity
        fields = ['creator_weixin_id', 'creator_weixin_name', 'activity_title', 'activity_item']


class WhiteListUpdateSerializer(serializers.Serializer):
    creator_weixin_id = serializers.CharField(max_length=255)
    guest_weixin_id_list = serializers.ListField(
        child=serializers.CharField(max_length=255)
    )


class ActivityItemUpdateSerializer(serializers.Serializer):
    activity_item_id = serializers.IntegerField()
    activity_item_operator = serializers.CharField(max_length=255)
    activity_item_status = serializers.ChoiceField(
        choices=['checked', 'deleted', '']
    )


class ActivityItemAddSerializer(serializers.Serializer):
    creator_weixin_id = serializers.CharField(max_length=255)
    activity_item = serializers.DictField()


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
