import pandas as pd
from decimal import Decimal
from django.http import HttpResponse
from .models import StockBasicInfo


def fupan(request):

    # get all code
    # [{'code': '000001'}, {'code': '000002'}, ...]
    distinct_codes = StockBasicInfo.objects.values('code').distinct()
    codes_list = [code_dict['code'] for code_dict in distinct_codes]

    codes_list = ['603990']
    for code in codes_list:

        # get latest 10 days data for each stock
        basic_infos = StockBasicInfo.objects.filter(code=code).order_by('-date')[:20]

        data_list = []
        for basic_info in basic_infos:
            data_list.append({
                'date': basic_info.date,
                'code': basic_info.code,
                'name': basic_info.name,
                'open_price': basic_info.open_price,
                'close_price': basic_info.close_price,
                'high_price': basic_info.high_price,
                'low_price': basic_info.low_price,
                'money': basic_info.money
            })

        df = pd.DataFrame(data_list)
        print(df)
        df = df.sort_values(by='date', ascending=False)

        # 计算每日涨幅（相较于前一天的涨幅）
        df['change_percentage'] = df.groupby('code')['close_price'].pct_change() * 100
        print(df)

        def analyze_stock_data(df):
            first_high_change = df[df['change_percentage'] > 8]
            if first_high_change.empty:
                return None

            # 获取第一次涨幅大于 8% 的日期及相关收盘价
            first_high_date = first_high_change.iloc[0]['date']
            high_close_price = df[df['date'] == first_high_date].iloc[0]['close_price']

            # 计算 95% 的阈值
            # threshold_price = high_close_price * Decimal('0.98')
            threshold_price = high_close_price

            # 2. 过滤条件
            filtered_data = df[df['date'] > first_high_date]
            filtered_data = filtered_data[
                (filtered_data['close_price'] >= threshold_price) &
                (filtered_data['change_percentage'].abs() <= 3)
            ]

            if filtered_data.empty:
                return None

            return filtered_data

        # 示例调用
        result = analyze_stock_data(df)

        if result is not None:
            print(result)

    return HttpResponse()
