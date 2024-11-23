from django.db import models


class UploadPDF(models.Model):

    ip = models.GenericIPAddressField(null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True)
    file_size = models.PositiveIntegerField(null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

