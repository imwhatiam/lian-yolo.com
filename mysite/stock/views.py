import logging
import pandas as pd

from django.shortcuts import render
from django.views.decorators.cache import cache_page

from .models import StockBasicInfo

logger = logging.getLogger(__name__)


# Cache this view for 24 hours
# @cache_page(60 * 60 * 24)
def fupan(request):

    logger.error('in fupan')
    last_x_days = int(request.GET.get('last_x_days', 11))

    gwhp_big_increase_rate = int(request.GET.get('gwhp_big_increase_rate', 6))
    gwhp_increase_rate_after = int(request.GET.get('gwhp_increase_rate_after', 3))

    xsbjc_days = int(request.GET.get('xsbjc_days', 3))
    xsbjc_increase_rate = int(request.GET.get('xsbjc_increase_rate', 3))

    # get all code
    # [{'code': '000001'}, {'code': '000002'}, ...]
    distinct_codes = StockBasicInfo.objects.values('code').distinct()
    codes_list = [code_dict['code'] for code_dict in distinct_codes]

    result = []
    xsbjc_result = []
    for code in codes_list:

        # get latest X days data for each stock
        basic_infos = StockBasicInfo.objects.filter(code=code)
        basic_infos = basic_infos.order_by('-date')[:last_x_days]

        data_list = []
        for basic_info in basic_infos:
            data_list.append({
                'date': basic_info.date,
                'code': basic_info.code,
                'name': basic_info.name,
                # 'open_price': basic_info.open_price,
                'close_price': basic_info.close_price,
                # 'high_price': basic_info.high_price,
                # 'low_price': basic_info.low_price,
                # 'money': basic_info.money
            })

        df = pd.DataFrame(data_list)
        df = df.iloc[::-1].reset_index(drop=True)  # reverse id
        df['change_pct'] = (
            df.groupby('code')['close_price'].pct_change() * 100
        ).round(2)

        # find gwhp
        for i, row in df.iterrows():
            if row["change_pct"] > gwhp_big_increase_rate:
                start_price = row["close_price"]
                # range(3, 6) => [3, 4, 5]
                for days in list(range(3, 6)):
                    if i + days < len(df):
                        future_data = df.loc[i+1:i+days]
                        if all(future_data["change_pct"].abs() < gwhp_increase_rate_after):
                            final_price = future_data.iloc[-1]["close_price"]
                            increase_rate = (final_price-start_price)/start_price*100
                            if abs(increase_rate) <= gwhp_increase_rate_after:
                                result.append({
                                    'date': row["date"].strftime('%Y-%m-%d'),
                                    'name': row["name"],
                                })
                                break

        # # find xsbjc
        # threshold_min, threshold_max = 0, 3
        # df['change_pct'] = pd.to_numeric(df['change_pct'], errors='coerce')
        # df['in_range'] = df['change_pct'].between(threshold_min, threshold_max)
        # # 标记连续块
        # df['streak'] = (df['in_range'] != df['in_range'].shift()).cumsum()
        # # 找到满足条件的块
        # xsbjc_result = df[df['in_range']].groupby('streak').filter(lambda x: len(x) >= 3)
        # first_dates = xsbjc_result.groupby('streak').first()['date']
        # xsbjc_date_list = first_dates.tolist()
        # if xsbjc_date_list:
        #     xsbjc_result.append({
        #         'date': xsbjc_date_list[0].strftime('%Y-%m-%d'),
        #         'name': code,
        #     })

    # for gwhp
    formatted_result = {}
    result = sorted(result, key=lambda x: x['date'], reverse=True)
    for item in result:
        date = item['date']
        name = item['name']
        if date not in formatted_result:
            formatted_result[date] = []
        formatted_result[date].append(name)

    gwhp_stock_list = []
    for date, names in formatted_result.items():
        gwhp_stock_list.append({'date': date, 'name_list': names})

    # # for xsbjc
    # formatted_result = {}
    # xsbjc_result = sorted(xsbjc_result, key=lambda x: x['date'], reverse=True)
    # for item in xsbjc_result:
    #     date = item['date']
    #     name = item['name']
    #     if date not in formatted_result:
    #         formatted_result[date] = []
    #     formatted_result[date].append(name)

    # xsbjc_stock_list = []
    # for date, names in formatted_result.items():
    #     xsbjc_stock_list.append({'date': date, 'name_list': names})

    data = {
        'last_x_days': last_x_days,

        'gwhp_big_increase_rate': gwhp_big_increase_rate,
        'gwhp_increase_rate_after': gwhp_increase_rate_after,
        'gwhp_stock_list': gwhp_stock_list,

        'xsbjc_days': xsbjc_days,
        'xsbjc_increase_rate': xsbjc_increase_rate,
        'xsbjc_stock_list': [],
    }

    return render(request, 'stock/fupan.html', data)
