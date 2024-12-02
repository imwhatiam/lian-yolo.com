source /root/django-5.0/bin/activate
cd /root/lian-yolo.com/mysite
python manage.py scrape_jiaoyou >> /root/scrape_douban_jiaoyou.log  2>&1
