import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from douban.models import DoubanPost


class Command(BaseCommand):

    help = "Scrape discussions from Douban group and save to the database"

    def handle(self, *args, **options):

        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        headers = {'User-Agent': user_agent}

        group_id = '641424'
        start = 0
        skipped_list = ['193662234', '198931411']

        while start < 300:

            time.sleep(5)
            url = f"https://www.douban.com/group/{group_id}/discussion?start={start}"
            start += 25
            print(f"Scraping: {url}")

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.RequestException as e:
                self.stderr.write(f"Request failed: {e}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
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

                    count = int(row.find('td', attrs={'class': 'r-count'}).text.strip())
                    last_reply = row.find('td', attrs={'class': 'time'}).text.strip()

                    # Skip URLs in skipped_list
                    if any(item in url for item in skipped_list):
                        continue

                    # Save or update the record in the database
                    post, created = DoubanPost.objects.update_or_create(
                        url=url,
                        defaults={
                            'title': title,
                            'count': count,
                            'last_reply': last_reply,
                            'good': good,
                        }
                    )
                    action = "Created" if created else "Updated"
                    self.stdout.write(f"{action} post: {title} ({url})")

                except Exception as e:
                    self.stderr.write(f"Error processing row: {row}")
                    self.stderr.write(str(e))
