import os
import time
import fitz  # PyMuPDF
import zipfile
from io import BytesIO
from functools import wraps

from django.core.cache import cache
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import FileSystemStorage

from .models import UploadPDF
from .settings import PDF_MAX_SIZE


def rate_limit(ip_limit=10, duration=86400):  # 默认24小时 = 86400秒
    """
    装饰器：限制同一 IP 在指定时间内的访问次数。

    :param ip_limit: 每个 IP 的最大访问次数
    :param duration: 时间窗口（秒）
    """
    def decorator(view_func):

        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):

            if request.method != 'POST':
                return view_func(request, *args, **kwargs)

            ip = get_client_ip(request)

            cache_key = f"rate_limit_{ip}"
            request_data = cache.get(cache_key)

            if request_data is None:
                request_data = {"count": 1, "start_time": time.time()}
            else:
                elapsed_time = time.time() - request_data["start_time"]
                if elapsed_time > duration:
                    request_data = {"count": 1, "start_time": time.time()}
                else:
                    request_data["count"] += 1

            cache.set(cache_key, request_data, duration)

            if request_data["count"] > ip_limit:
                return JsonResponse({
                    "error": "Rate limit exceeded. Try again later.",
                    "limit": ip_limit,
                    "duration": duration
                }, status=429)  # HTTP 429 Too Many Requests

            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator


def get_client_ip(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


@rate_limit()
def upload_pdf(request):

    if request.method == 'POST' and request.FILES.get('file'):

        uploaded_file = request.FILES['file']

        obj = UploadPDF(
            ip=get_client_ip(request),
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
        )
        obj.save()

        if uploaded_file.content_type != 'application/pdf':
            error_msg = 'The uploaded file is not a PDF.'
            return JsonResponse({'error': error_msg}, status=400)

        if uploaded_file.size > PDF_MAX_SIZE:
            max_size_mb = PDF_MAX_SIZE / 1024 / 1024
            error_msg = f'The uploaded PDF file exceeds the {max_size_mb} MB size limit.'
            return JsonResponse({'error': error_msg}, status=400)

        fs = FileSystemStorage(location='/tmp')
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(filename)

        images = []
        try:
            doc = fitz.open(file_path)
            for page_number in range(len(doc)):
                page = doc[page_number]
                pix = page.get_pixmap(dpi=150)
                img_bytes = BytesIO(pix.tobytes("png"))
                images.append((f'{uploaded_file.name}_{page_number + 1}.png', img_bytes))
            doc.close()
        except Exception as e:
            return JsonResponse({'error': f'Failed to process PDF: {str(e)}'}, status=500)
        finally:
            os.remove(file_path)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for image_name, image_data in images:
                zip_file.writestr(image_name, image_data.getvalue())

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="converted_images.zip"'
        return response

    return render(request, 'pdf_to_img/upload.html')
