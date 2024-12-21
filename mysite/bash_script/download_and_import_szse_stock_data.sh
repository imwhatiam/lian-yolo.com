#!/usr/bin/bash
DATE_PARAM="${1:-$(date '+%Y-%m-%d')}"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Running download_and_import_szse_stock_data.sh"
source /Users/lian/python3.12-venv/bin/activate
cd /Users/lian/lian-yolo.com/mysite

python manage.py download_szse_stock_data >> /tmp/download-szse-stock-data.log
# python manage.py import_szse_stock_data >> /tmp/import-szse-stock-data.log
