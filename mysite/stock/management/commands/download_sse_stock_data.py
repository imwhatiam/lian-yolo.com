import os
import csv
import requests
from datetime import datetime

from django.core.management.base import BaseCommand

from mysite.settings import BASE_DIR
from mysite.utils import normalize_folder_path

from stock.utils import is_future_date, get_date_list, is_weekend_or_holiday

BASE_DIR = normalize_folder_path(str(BASE_DIR))
STOCK_EXCEL_PARENT_FOLDER = f'{BASE_DIR}stock/stock-data/'

if not os.path.exists(STOCK_EXCEL_PARENT_FOLDER):
    os.makedirs(STOCK_EXCEL_PARENT_FOLDER)


class Command(BaseCommand):

    help = "Download stock Excel file"

    def add_arguments(self, parser):

        parser.add_argument(
            "--start-date",
            type=str,
            nargs="?",  # Makes 'start-date' argument optional
            default='',
            help="Date in YYYY-MM-DD format"
        )

        parser.add_argument(
            "--end-date",
            type=str,
            nargs="?",  # Makes 'end-date' argument optional
            default=datetime.today().strftime('%Y-%m-%d'),
            help="Date in YYYY-MM-DD format"
        )

        parser.add_argument(
            "--stock-excel-parent-folder",
            type=str,
            nargs="?",  # Makes 'date' argument optional
            default=STOCK_EXCEL_PARENT_FOLDER,  # Default save path
            help="Path to save the downloaded file"
        )

    def handle(self, *args, **kwargs):

        start_date_str = kwargs["start_date"]
        end_date_str = kwargs["end_date"]

        if start_date_str and is_future_date(start_date_str):
            error_msg = f"Start date {start_date_str} is a future date! "
            self.stderr.write(self.style.ERROR(error_msg))
            return

        if end_date_str and is_future_date(end_date_str):
            error_msg = f"End date {end_date_str} is a future date! "
            self.stderr.write(self.style.ERROR(error_msg))
            return

        stock_excel_parent_folder = normalize_folder_path(kwargs["stock_excel_parent_folder"])

        date_list = get_date_list(start_date_str, end_date_str)
        for date_str in date_list:

            should_pass, error_msg = is_weekend_or_holiday(date_str)
            if should_pass:
                self.stderr.write(self.style.ERROR(error_msg))
                continue

            stock_excel_file = f"{stock_excel_parent_folder}stock_data_{date_str}.csv"

            if os.path.exists(stock_excel_file):
                error_msg = f"File already exists: {stock_excel_file}"
                self.stderr.write(self.style.ERROR(error_msg))
                continue

            url = (
                "https://yunhq.sse.com.cn:32042/v1/sh1/list/exchange/equity"
                "?select=code,name,open,last,high,low,amount&begin=0&end=5000"
            )
            response = requests.get(url)

            if response.status_code == 200:
                resp_json = response.json()
                stock_list = resp_json.get('list')
                print(f'{date_str} Get total {len(stock_list)} records')
            else:
                print(f"Failed to download {date_str} file. Status code: {response.status_code}")

            headers = ["交易日期", "证券代码", "证券简称",
                       "开盘", "今收", "最高", "最低", "成交金额(万元)"]
            with open(stock_excel_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                for row in stock_list:
                    row.insert(0, date_str)
                    row[-1] = row[-1] / 10000
                    writer.writerow(row)

        print('Done')
