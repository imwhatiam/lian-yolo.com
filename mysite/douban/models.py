from django.db import models


class DoubanPost(models.Model):

    topic = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500, blank=True, null=True)
    count = models.PositiveIntegerField(default=0)
    last_reply = models.DateTimeField(blank=True, null=True)
    good = models.BooleanField(default=False)

    def __str__(self):
        return self.title
