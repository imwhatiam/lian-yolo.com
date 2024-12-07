import os
import pytz
import datetime
import pandas as pd
from decimal import Decimal

from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand

from mysite.settings import BASE_DIR
from mysite.utils import normalize_folder_path
from stock.models import StockBasicInfo

BASE_DIR = normalize_folder_path(str(BASE_DIR))
STOCK_EXCEL_PARENT_FOLDER = f'{BASE_DIR}stock/stock-data/'


class Command(BaseCommand):

    help = "Import stock data from szse Excel file"

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
        date_str = kwargs["date"]
        stock_excel_parent_folder = normalize_folder_path(kwargs["stock_excel_parent_folder"])
        stock_excel_file = f"{stock_excel_parent_folder}stock_data_{date_str}.xlsx"

        if not os.path.exists(stock_excel_file):
            self.stderr.write(self.style.ERROR(f"File not found: {stock_excel_file}"))
            return

        try:
            df = pd.read_excel(stock_excel_file,
                               engine='openpyxl',
                               parse_dates=["交易日期"])

            # clean up the data
            for column in ["开盘", "今收", "最高", "最低", "成交金额(万元)"]:
                df[column] = df[column].astype(str).str.replace(",", "").str.strip()
                df[column] = pd.to_numeric(df[column], errors="coerce")

            records_created = 0
            errors_detected = 0

            # allowing for some rounding errors
            tolerance = 1e-6

            for _, row in df.iterrows():
                date = make_aware(row["交易日期"], timezone=pytz.timezone("Asia/Shanghai"))
                code = str(row["证券代码"])

                stock = StockBasicInfo.objects.filter(date=date, code=code).first()

                if stock:
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
                        db_value = getattr(stock, field)
                        if isinstance(db_value, Decimal) and isinstance(value, float):
                            # convert Decimal to float, then compare
                            if not abs(float(db_value) - value) <= tolerance:
                                discrepancies.append(f"{field}: DB({float(db_value)}) != EXCEL({value})")
                        elif db_value != value:
                            discrepancies.append(f"{field}: DB({db_value}) != EXCEL({value})")

                    if discrepancies:
                        errors_detected += 1
                        self.stderr.write(self.style.ERROR(
                            f"Data mismatch for date={date}, code={code}:\n" + "\n".join(discrepancies)
                        ))
                else:
                    StockBasicInfo.objects.create(
                        date=date,
                        code=code,
                        name=row["证券简称"],
                        open_price=row["开盘"],
                        close_price=row["今收"],
                        high_price=row["最高"],
                        low_price=row["最低"],
                        money=row["成交金额(万元)"],
                    )
                    records_created += 1

            self.stdout.write(self.style.SUCCESS(f"Successfully created {records_created} records."))
            if errors_detected > 0:
                self.stderr.write(self.style.WARNING(f"Detected {errors_detected} discrepancies in existing records."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))
