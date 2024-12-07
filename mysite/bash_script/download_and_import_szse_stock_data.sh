#!/usr/bin/bash
DATE_PARAM="${1:-$(date '+%Y-%m-%d')}"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Running download_szse_stock_excel.sh"
source /Users/lian/python3.12-venv/bin/activate
cd /Users/lian/lian-yolo.com/mysite
python manage.py download_szse_stock_excel --date "$DATE_PARAM" >> /tmp/lian-yolo.com.log  2>&1
python manage.py import_data_from_szse_stock_excel --date "$DATE_PARAM" >> /tmp/lian-yolo.com.log  2>&1
