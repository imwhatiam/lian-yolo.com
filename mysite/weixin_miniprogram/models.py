import os
import uuid
import time
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder


def current_timestamp():
    return int(time.time())


class CheckList(models.Model):
    title = models.CharField(max_length=255)
    desc = models.TextField(null=True, blank=True)
    order_num = models.IntegerField(default=0, null=False, blank=False)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.title

    def get_children(self):
        return self.children.all()

    @property
    def image_url(self):
        return self.image.url if self.image else ''


class Activities(models.Model):
    creator_weixin_id = models.CharField(max_length=255, verbose_name="用户微信ID")
    creator_weixin_name = models.CharField(max_length=255, verbose_name="用户微信名称")
    activity_title = models.CharField(max_length=255, verbose_name="活动名称")
    activity_items = models.JSONField(encoder=DjangoJSONEncoder, verbose_name="活动事项列表")
    white_list = models.JSONField(encoder=DjangoJSONEncoder, default=list, verbose_name="白名单")

    class Meta:
        db_table = 'activity'

    def __str__(self):
        return f"{self.activity_title} (ID: {self.id})"


class WeixinUserInfoManager(models.Manager):

    def get_avatar_url(self, openid):
        try:
            return self.get(openid=openid).avatar_url
        except self.model.DoesNotExist:
            return ''


def user_avatar_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('avatars', 'weixin', instance.openid, filename)


class WeixinUserInfo(models.Model):
    openid = models.CharField(db_index=True, max_length=100, unique=True)
    nickname = models.CharField(blank=True, max_length=100, null=True)
    avatar_url = models.URLField(blank=True, max_length=500, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        max_length=500,
        verbose_name='头像文件'
    )

    objects = WeixinUserInfoManager()

    class Meta:
        db_table = 'weixin_user_info'

    def __str__(self):
        return f'{self.nickname} ({self.openid})'
