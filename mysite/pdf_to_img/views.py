import io
from zipfile import ZipFile
from pdf2image import convert_from_bytes

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse


def upload_pdf(request):

    if request.method == 'POST' and request.FILES.get('file'):

        uploaded_file = request.FILES['file']

        # 1. 判断文件类型是否为 PDF
        if uploaded_file.content_type != 'application/pdf':
            return JsonResponse({'error': 'The uploaded file is not a PDF.'}, status=400)

        # 2. 判断文件大小是否超过 10MB
        if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
            return JsonResponse({'error': 'The uploaded PDF file exceeds the 10MB size limit.'}, status=400)

        try:
            # 3. 使用 BytesIO 处理文件内容
            pdf_file = io.BytesIO(uploaded_file.read())

            # 4. 使用 pdf2image 将 PDF 文件转换为图像
            pdf_bytes = pdf_file.read()  # 获取字节数据
            images = convert_from_bytes(pdf_bytes, dpi=300)

            # 创建一个内存中的 Zip 文件
            zip_buffer = io.BytesIO()
            with ZipFile(zip_buffer, 'w') as zip_file:
                for i, image in enumerate(images):
                    # 将每个图像保存为 PNG 格式到内存
                    image_buffer = io.BytesIO()
                    image.save(image_buffer, format='PNG')
                    image_buffer.seek(0)  # 重置内存文件指针

                    # 将图像添加到 ZIP 文件
                    image_filename = f"page_{i + 1}.png"
                    zip_file.writestr(image_filename, image_buffer.read())

            # 将 zip 文件内容写入响应并返回给前端
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="converted_images.zip"'

            return response

        except Exception as e:
            return JsonResponse({'error': f'An error occurred while processing the PDF: {str(e)}'}, status=500)

    return render(request, 'pdf_to_img/upload.html')
