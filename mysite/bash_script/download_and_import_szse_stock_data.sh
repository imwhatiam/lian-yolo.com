#!/usr/bin/bash
DATE_PARAM="${1:-$(date '+%Y-%m-%d')}"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Running download_and_import_szse_stock_data.sh"
source /Users/lian/python3.12-venv/bin/activate
cd /Users/lian/lian-yolo.com/mysite

python manage.py download_szse_stock_data --date "$DATE_PARAM" >> /tmp/lian-yolo.com.log  2>&1
python manage.py import_szse_stock_data --date "$DATE_PARAM" >> /tmp/lian-yolo.com.log  2>&1

# dates=('2024-07-11' '2024-07-12' '2024-07-15' '2024-07-16' '2024-07-17'
# '2024-07-18' '2024-07-19' '2024-07-22' '2024-07-23' '2024-07-24'
# '2024-07-25' '2024-07-26' '2024-07-29' '2024-07-30' '2024-07-31'
# '2024-08-01' '2024-08-02' '2024-08-05' '2024-08-06' '2024-08-07'
# '2024-08-08' '2024-08-09' '2024-08-12' '2024-08-13' '2024-08-14'
# '2024-08-15' '2024-08-16' '2024-08-19' '2024-08-20' '2024-08-21'
# '2024-08-22' '2024-08-23' '2024-08-26' '2024-08-27' '2024-08-28'
# '2024-08-29' '2024-08-30' '2024-09-02' '2024-09-03' '2024-09-04'
# '2024-09-05' '2024-09-06' '2024-09-09' '2024-09-10' '2024-09-11'
# '2024-09-12' '2024-09-13' '2024-09-18' '2024-09-19' '2024-09-20'
# '2024-09-23' '2024-09-24' '2024-09-25' '2024-09-26' '2024-09-27'
# '2024-09-30' '2024-10-08' '2024-10-09' '2024-10-10' '2024-10-11'
# '2024-10-14' '2024-10-15' '2024-10-16' '2024-10-17' '2024-10-18'
# '2024-10-21' '2024-10-22' '2024-10-23' '2024-10-24' '2024-10-25'
# '2024-10-28' '2024-10-29' '2024-10-30' '2024-10-31' '2024-11-01'
# '2024-11-04' '2024-11-05' '2024-11-06' '2024-11-07' '2024-11-08'
# '2024-11-11' '2024-11-12' '2024-11-13' '2024-11-14' '2024-11-15'
# '2024-11-18' '2024-11-19' '2024-11-20' '2024-11-21' '2024-11-22'
# '2024-11-25' '2024-11-26' '2024-11-27' '2024-11-28' '2024-11-29'
# '2024-12-02' '2024-12-03' '2024-12-04' '2024-12-05' '2024-12-06')
#
# for date in "${dates[@]}"; do
#     python manage.py download_szse_stock_data --date "$date"
#     python manage.py import_szse_stock_data --date "$date"
# done
