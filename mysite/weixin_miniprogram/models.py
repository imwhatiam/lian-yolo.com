import time
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder


def current_timestamp():
    return int(time.time())


class UserActivity(models.Model):

    openid = models.CharField(max_length=100, unique=True, db_index=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    activities = models.JSONField(default=list)
    created_at = models.BigIntegerField(default=current_timestamp)
    updated_at = models.BigIntegerField(default=current_timestamp)

    def save(self, *args, **kwargs):
        self.updated_at = current_timestamp()
        if not self.pk:
            self.created_at = self.updated_at
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nickname


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


class Activity(models.Model):
    creator_weixin_id = models.CharField(max_length=255, verbose_name="用户微信ID")
    creator_weixin_name = models.CharField(max_length=255, verbose_name="用户微信名称")
    activity_title = models.CharField(max_length=255, verbose_name="活动名称")
    activity_item = models.JSONField(encoder=DjangoJSONEncoder, verbose_name="活动事项列表")
    white_list = models.JSONField(encoder=DjangoJSONEncoder, default=list, verbose_name="白名单")

    class Meta:
        db_table = 'activity'
        verbose_name = '活动'
        verbose_name_plural = '活动'

    def __str__(self):
        return f"{self.activity_title} (ID: {self.id})"
