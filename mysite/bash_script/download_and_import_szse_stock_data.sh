#!/usr/bin/bash
echo "$(date '+%Y-%m-%d %H:%M:%S') - Running download_szse_stock_excel.sh"
source /root/django-5.0/bin/activate
cd /root/lian-yolo.com/mysite
python manage.py download_szse_stock_excel
python manage.py import_data_from_szse_stock_excel
