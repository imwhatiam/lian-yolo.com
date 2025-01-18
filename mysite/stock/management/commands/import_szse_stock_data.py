import os
import pytz
import pandas as pd
from decimal import Decimal
from datetime import datetime

from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand

from mysite.settings import BASE_DIR
from mysite.utils import normalize_folder_path

from stock.models import StockTradeInfo
from stock.utils import is_future_date, get_date_list, is_weekend_or_holiday

BASE_DIR = normalize_folder_path(str(BASE_DIR))
STOCK_EXCEL_PARENT_FOLDER = f'{BASE_DIR}stock/stock-data/'


class Command(BaseCommand):

    help = "Import stock data from szse Excel file"

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
                record_count = StockTradeInfo.objects.filter(date=date_str).count()
                self.stderr.write(self.style.ERROR(f"Record count: {record_count}"))
                continue

            stock_excel_file = f"{stock_excel_parent_folder}stock_data_{date_str}.xlsx"
            if not os.path.exists(stock_excel_file):
                self.stderr.write(self.style.ERROR(f"File not found: {stock_excel_file}"))
                continue

            print(f'Processing {stock_excel_file}...')
            df = pd.read_excel(stock_excel_file,
                               engine='openpyxl',
                               parse_dates=["交易日期"])

            # clean up the data
            for column in ["开盘", "今收", "最高", "最低", "成交金额(万元)"]:
                df[column] = df[column].astype(str).str.replace(",", "").str.strip()
                df[column] = pd.to_numeric(df[column], errors="coerce").round(2)

            for _, row in df.iterrows():

                if 'B' in row["证券简称"] or 'b' in row["证券简称"]:
                    continue

                date = make_aware(row["交易日期"], timezone=pytz.timezone("Asia/Shanghai"))
                code = str(row["证券代码"])
                code = code.zfill(6)

                trade_info = StockTradeInfo.objects.filter(date=date, code=code).first()

                if not trade_info:
                    StockTradeInfo.objects.create(
                        date=date,
                        code=code,
                        name=row["证券简称"],
                        open_price=row["开盘"],
                        close_price=row["今收"],
                        high_price=row["最高"],
                        low_price=row["最低"],
                        money=row["成交金额(万元)"],
                    )
                    # self.stdout.write(self.style.SUCCESS(f"New record created for date={date_str}, code={code}"))
                    continue

                # print(f'Record found for date={date_str}, code={code}')
                # compare excel data with the existing record
                discrepancies = []
                fields_to_check = {
                    "name": row["证券简称"],
                    "open_price": row["开盘"],
                    "close_price": row["今收"],
                    "high_price": row["最高"],
                    "low_price": row["最低"],
                    "money": row["成交金额(万元)"],
                }

                for field, value in fields_to_check.items():
                    db_value = getattr(trade_info, field)
                    if isinstance(db_value, Decimal):
                        # convert Decimal to float
                        db_value = float(db_value)
                    if db_value != value:
                        discrepancies.append(f"{field}: DB({db_value}) != EXCEL({value})")

                if discrepancies:
                    self.stderr.write(self.style.ERROR(
                        f"Data mismatch for date={date_str}, code={code}:\n" + "\n".join(discrepancies)
                    ))

        print('Done')
