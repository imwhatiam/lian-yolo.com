import os
import random
import requests
import datetime

from django.core.management.base import BaseCommand

from mysite.settings import BASE_DIR
from mysite.utils import normalize_folder_path

BASE_DIR = normalize_folder_path(str(BASE_DIR))
STOCK_EXCEL_PARENT_FOLDER = f'{BASE_DIR}stock/stock-data/'

if not os.path.exists(STOCK_EXCEL_PARENT_FOLDER):
    os.makedirs(STOCK_EXCEL_PARENT_FOLDER)


class Command(BaseCommand):

    help = "Download stock Excel file"

    def add_arguments(self, parser):

        parser.add_argument(
            "--date",
            type=str,
            nargs="?",  # Makes 'date' argument optional
            default=datetime.date.today().strftime('%Y-%m-%d'),
            help="Date in YYYY-MM-DD format"
        )
        parser.add_argument(
            "--stock_excel_parent_folder",
            type=str,
            nargs="?",  # Makes 'date' argument optional
            default=STOCK_EXCEL_PARENT_FOLDER,  # Default save path
            help="Path to save the downloaded file (default: /tmp/)"
        )

    def handle(self, *args, **kwargs):

        random_value = random.random()
        random_value = f"{random_value:.15f}"

        date_str = kwargs["date"]
        stock_excel_parent_folder = normalize_folder_path(kwargs["stock_excel_parent_folder"])

        url = (
            "https://www.szse.cn/api/report/ShowReport"
            "?SHOWTYPE=xlsx&CATALOGID=1815_stock_snapshot&TABKEY=tab1&"
            f"txtBeginDate={date_str}&txtEndDate={date_str}&"
            "archiveDate=2022-12-01&random={random_value}"
        )
        response = requests.get(url)

        if response.status_code == 200:
            stock_excel_file = f"{stock_excel_parent_folder}stock_data_{date_str}.xlsx"
            with open(stock_excel_file, 'wb') as f:
                f.write(response.content)
            print(f"Excel file downloaded and saved to {stock_excel_file}")
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
