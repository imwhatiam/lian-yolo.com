"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import index, react_home

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', index),

    path('pdf-to-img/', include('pdf_to_img.urls')),
    path('douban/', include('douban.urls')),
    path('stock/', include('stock.urls')),
    path('weixin-miniprogram/', include('weixin_miniprogram.urls')),

    path('react/', react_home),
    path('react-naive-book/', include('react_naive_book.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
