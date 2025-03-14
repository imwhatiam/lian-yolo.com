import time
from django.db import models


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
