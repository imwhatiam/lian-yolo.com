import os
import zipfile
import fitz  # PyMuPDF
from io import BytesIO

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.core.files.storage import FileSystemStorage

from .models import UploadPDF
from .settings import PDF_MAX_SIZE


def get_client_ip(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


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
                pix = page.get_pixmap()
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
