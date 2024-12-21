import pandas as pd

from django.shortcuts import render
from django.views.decorators.cache import cache_page

from .models import StockBasicInfo


# Cache this view for 24 hours
@cache_page(60 * 60 * 24)
def fupan(request):

    last_x_days = request.GET.get('last_x_days', 20)

    big_increase_rate = request.GET.get('big_increase_rate', 6)
    increase_rate_after = request.GET.get('increase_rate_after', 3)

    last_x_days = int(last_x_days)
    big_increase_rate = int(big_increase_rate)
    increase_rate_after = int(increase_rate_after)

    # get all code
    # [{'code': '000001'}, {'code': '000002'}, ...]
    distinct_codes = StockBasicInfo.objects.values('code').distinct()
    codes_list = [code_dict['code'] for code_dict in distinct_codes]

    result = []
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
        # 序号翻转
        df = df.iloc[::-1].reset_index(drop=True)

        # 计算每日涨幅（相较于前一天的涨幅）
        df['change_percentage'] = (
            df.groupby('code')['close_price'].pct_change() * 100
        ).round(2)

        for i, row in df.iterrows():

            # 1. 涨幅大于 x%
            if row["change_percentage"] > big_increase_rate:

                # 当天收盘价
                start_close_price = row["close_price"]

                # range(3, 6) 生成从 3 到 5 的数，不包括 6
                # 之后 3-5 天
                for days in list(range(3, 6)):

                    if i + days < len(df):

                        # 条件 1：大涨幅之后每天涨跌幅都小于 3
                        future_data = df.loc[i+1:i+days]
                        if all(future_data["change_percentage"].abs() < increase_rate_after):

                            # 条件 2：大涨幅之后第3(或4或5)天的close_price较大涨那天的涨跌幅不超过 3%
                            final_close_price = future_data.iloc[-1]["close_price"]
                            increase_rate = (final_close_price-start_close_price)/start_close_price*100
                            if abs(increase_rate) <= increase_rate_after:
                                result.append({
                                    'date': row["date"].strftime('%Y-%m-%d'),
                                    'code': row["code"],
                                    'name': row["name"],
                                })
                                break  # 找到符合条件的，不再检查下一个范围

    result = sorted(result, key=lambda x: x['date'], reverse=True)

    data = {
        'last_x_days': last_x_days,
        'big_increase_rate': big_increase_rate,
        'increase_rate_after': increase_rate_after,
        'stock_list': result
    }

    return render(request, 'stock/fupan.html', data)
