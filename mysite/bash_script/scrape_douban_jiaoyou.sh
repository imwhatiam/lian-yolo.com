#!/usr/bin/bash
echo "$(date '+%Y-%m-%d %H:%M:%S') - Running scrape_douban_jiaoyou.sh"
source /root/django-5.0/bin/activate && cd /root/lian-yolo.com/mysite && python manage.py scrape_jiaoyou
