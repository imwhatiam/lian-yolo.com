from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_pdf, name='pdf_to_img_upload_pdf'),
]
