#!/usr/bin/bash

# 0 1 * * * /root/lian-yolo.com/mysite/bash_script/download_and_import_szse_stock_data.sh >> /tmp/download_and_import_szse_stock_data.log 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') - Running download_and_import_szse_stock_data.sh"
source /Users/lian/python3.12-venv/bin/activate
cd /Users/lian/lian-yolo.com/mysite

python manage.py download_szse_stock_data
python manage.py import_szse_stock_data
