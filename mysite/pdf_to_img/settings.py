from django.conf import settings

PDF_MAX_SIZE = getattr(settings, 'PDF_MAX_SIZE', 10 * 1024 * 1024)

