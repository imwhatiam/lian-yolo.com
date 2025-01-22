import pandas as pd
import chinese_calendar as calendar
from datetime import datetime, timedelta

from django.db.models import QuerySet

from .models import Stock, Industry, StockTradeInfo


def is_future_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date() > datetime.today().date()


def get_date_list(start_date_str='',
                  end_date_str=datetime.today().strftime('%Y-%m-%d')):

    if not start_date_str:
        return [end_date_str]

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    date_list = []
    while start_date <= end_date:
        date_list.append(start_date.strftime("%Y-%m-%d"))
        start_date += timedelta(days=1)

    return date_list


def is_weekend_or_holiday(date_str):

    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

    if date_obj.isoweekday() > 5:
        error_msg = f"{date_str} is a weekend! {date_obj.strftime('%a')}"
        return True, error_msg

    on_holiday, holiday_name = calendar.get_holiday_detail(date_obj)
    if on_holiday:
        holiday_name == calendar.Holiday.labour_day.value
        error_msg = f"{date_str} is a holiday! {holiday_name}"
        return True, error_msg

    return False, ''


def get_stock_info_dict() -> dict:

    """
    获取所有股票信息，返回以股票代码为键的字典。

    :return: 字典，格式为 {code: {'name': ..., 'sw_l2': ..., 'sw_l3': ...}}
    """

    stocks: QuerySet = Stock.objects.all()

    stock_info_dict = {
        stock.code: {
            'name': stock.name,
            'sw_l2': stock.sw_l2,
            'sw_l3': stock.sw_l3
        }
        for stock in stocks
    }

    return stock_info_dict


def get_industry_info_dict() -> dict:

    """
    获取所有行业信息，返回以行业代码为键的字典。

    :return: 字典，格式为 {code: {'name': ..., 'level': ...}}
    """

    industries: QuerySet = Industry.objects.all()

    industry_info_dict = {
        industry.code: {
            'name': industry.name,
            'level': industry.level
        }
        for industry in industries
    }

    return industry_info_dict


def get_trade_info_pd(stock_code_list, last_x_days):

    data_list = []
    for code in stock_code_list:
        trade_infos = StockTradeInfo.objects.filter(code=code)
        trade_infos = trade_infos.order_by('-date')[:last_x_days]

        for trade_info in trade_infos:
            data_list.append({
                'date': trade_info.date,
                'code': trade_info.code,
                'name': trade_info.name,
                'close_price': trade_info.close_price,
                'money': trade_info.money
            })

    df = pd.DataFrame(data_list)
    df = df.iloc[::-1].reset_index(drop=True)  # reverse id
    df['change_pct'] = df.groupby('code')['close_price'].pct_change() * 100
    df["change_pct"] = pd.to_numeric(df["change_pct"], errors="coerce").fillna(0).round(2)

    return df
