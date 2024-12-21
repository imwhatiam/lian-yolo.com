import os
import random
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

            random_value = random.random()
            random_value = f"{random_value:.15f}"

            stock_excel_file = f"{stock_excel_parent_folder}stock_data_{date_str}.xlsx"

            if os.path.exists(stock_excel_file):
                error_msg = f"File already exists: {stock_excel_file}"
                self.stderr.write(self.style.ERROR(error_msg))
                continue

            url = (
                "https://www.szse.cn/api/report/ShowReport"
                "?SHOWTYPE=xlsx&CATALOGID=1815_stock_snapshot&TABKEY=tab1&"
                f"txtBeginDate={date_str}&txtEndDate={date_str}&"
                "archiveDate=2022-12-01&random={random_value}"
            )
            response = requests.get(url)

            if response.status_code == 200:
                with open(stock_excel_file, 'wb') as f:
                    f.write(response.content)
                print(f"Excel file downloaded and saved to {stock_excel_file}")
            else:
                print(f"Failed to download {date_str} file. Status code: {response.status_code}")
