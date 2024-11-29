import re
import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand

from mysite.utils import normalize_folder_path

from douban.models import DoubanPost


class Command(BaseCommand):

    help = "Scrape discussions from Douban group and save to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            '--local-html-folder',
            type=str,
            help='The local file path to save the scraped discussions',
            required=False
        )

    def handle(self, *args, **options):

        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        headers = {'User-Agent': user_agent}

        start = 0
        group_id = '641424'
        skipped_list = ['193662234', '198931411']

        while start < 300:

            url = f"https://www.douban.com/group/{group_id}/discussion?start={start}"
            self.stdout.write(f"Scraping: {url}")

            start += 25

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                contents = response.text
            except requests.RequestException as e:
                self.stderr.write(f"Request failed: {e}")
                self.stdout.write("Now trying open local html file.")

                local_html_folder = options['local_html_folder']
                if local_html_folder:
                    local_html_folder = normalize_folder_path(local_html_folder)
                    local_file_path = f'{local_html_folder}{start}.htm'
                else:
                    local_file_path = f'/tmp/{start}.htm'

                if os.path.exists(local_file_path):
                    with open(local_file_path, 'r', encoding='utf-8') as f:
                        contents = f.read()
                else:
                    self.stderr.write(f"{local_file_path} not found")
                    continue

            # parse page content
            soup = BeautifulSoup(contents, 'html.parser')
            table = soup.find('table', attrs={'class': 'olt'})
            if not table:
                self.stderr.write("No discussion table found.")
                continue

            rows = table.find_all('tr')
            if not rows:
                self.stderr.write("No rows found in the table.")
                continue

            for row in rows:
                if 'class="th"' in str(row):
                    continue

                good = False
                if row.find('span', attrs={'class': 'elite_topic_lable'}):
                    good = True

                try:
                    a_element = row.find('a', href=True)
                    title = a_element['title']
                    url = a_element['href']
                    count = int(row.find('td', attrs={'class': 'r-count'}).text.strip() or 0)
                    last_reply = row.find('td', attrs={'class': 'time'}).text.strip()

                    # 11-21 13:34
                    date_time_format = r"^\d{2}-\d{2} \d{2}:\d{2}$"
                    if re.match(date_time_format, last_reply):
                        current_year = datetime.now().year
                        full_date_str = f"{current_year}-{last_reply}"
                        date_with_year = datetime.strptime(full_date_str, "%Y-%m-%d %H:%M")

                    # 2023-06-03
                    only_date_format = r"^\d{4}-\d{2}-\d{2}$"
                    if re.match(only_date_format, last_reply):
                        date_with_year = datetime.strptime(last_reply, "%Y-%m-%d")

                    aware_datetime = make_aware(date_with_year,
                                                timezone=ZoneInfo(settings.TIME_ZONE))

                    # Skip URLs in skipped_list
                    if any(item in url for item in skipped_list):
                        continue

                    # Save or update the record in the database
                    post, created = DoubanPost.objects.update_or_create(
                        topic='jiaoyou',
                        url=url,
                        defaults={
                            'title': title,
                            'count': count,
                            'last_reply': aware_datetime,
                            'good': good,
                        }
                    )

                    if created:
                        post.is_new = True
                        action = "Created"
                    else:
                        post.is_new = False
                        action = "Updated"

                    post.save()
                    self.stdout.write(f"{action} post: {title} ({url})")

                except Exception as e:
                    self.stderr.write(f"Error processing row: {row}")
                    self.stderr.write(str(e))

            time.sleep(5)
