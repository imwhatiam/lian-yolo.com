import csv
import logging
import chardet
import pandas as pd

from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.http import HttpResponseForbidden, HttpResponse

from .models import StockTradeInfo, IndustryStock

logger = logging.getLogger(__name__)


# Cache this view for 24 hours
@cache_page(60 * 60 * 24)
def fupan(request):

    last_x_days = int(request.GET.get('last_x_days', 11))

    gwhp_big_increase_rate = int(request.GET.get('gwhp_big_increase_rate', 6))
    gwhp_increase_rate_after = int(request.GET.get('gwhp_increase_rate_after', 3))

    xsbjc_days = int(request.GET.get('xsbjc_days', 5))
    xsbjc_increase_rate = int(request.GET.get('xsbjc_increase_rate', 2))

    # get all code
    # [{'code': '000001'}, {'code': '000002'}, ...]
    distinct_codes = StockTradeInfo.objects.values('code').distinct()
    codes_list = [code_dict['code'] for code_dict in distinct_codes]

    result = []
    xsbjc_result = []
    for code in codes_list:

        # get latest X days data for each stock
        trade_infos = StockTradeInfo.objects.filter(code=code)
        trade_infos = trade_infos.order_by('-date')[:last_x_days]

        data_list = []
        for trade_info in trade_infos:
            data_list.append({
                'date': trade_info.date,
                'code': trade_info.code,
                'name': trade_info.name,
                # 'open_price': trade_info.open_price,
                'close_price': trade_info.close_price,
                # 'high_price': trade_info.high_price,
                # 'low_price': trade_info.low_price,
                # 'money': trade_info.money
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

        # find xsbjc
        threshold_min, threshold_max = 0.1, xsbjc_increase_rate
        df['change_pct'] = pd.to_numeric(df['change_pct'], errors='coerce')
        df['in_range'] = df['change_pct'].between(threshold_min, threshold_max)
        df['streak'] = (df['in_range'] != df['in_range'].shift()).cumsum()
        xsbjc_df = df[df['in_range']].groupby('streak').filter(lambda x: len(x) >= xsbjc_days)
        if not xsbjc_df.empty:
            first_recort = xsbjc_df.groupby('streak').first()
            date = first_recort['date'].tolist()[0]
            name = first_recort['name'].tolist()[0]
            xsbjc_result.append({
                'date': date.strftime('%Y-%m-%d'),
                'name': name,
            })

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

    # for xsbjc
    formatted_result = {}
    xsbjc_result = sorted(xsbjc_result, key=lambda x: x['date'], reverse=True)
    for item in xsbjc_result:
        date = item['date']
        name = item['name']
        if date not in formatted_result:
            formatted_result[date] = []
        formatted_result[date].append(name)

    xsbjc_stock_list = []
    for date, names in formatted_result.items():
        xsbjc_stock_list.append({'date': date, 'name_list': names})

    data = {
        'last_x_days': last_x_days,

        'gwhp_big_increase_rate': gwhp_big_increase_rate,
        'gwhp_increase_rate_after': gwhp_increase_rate_after,
        'gwhp_stock_list': gwhp_stock_list,

        'xsbjc_days': xsbjc_days,
        'xsbjc_increase_rate': xsbjc_increase_rate,
        'xsbjc_stock_list': xsbjc_stock_list,
    }

    return render(request, 'stock/fupan.html', data)


def import_industry_stock(request):

    def detect_encoding(uploaded_file):
        raw_data = uploaded_file.read(10000)
        uploaded_file.seek(0)  # 重要！重置文件指针，以便后续读取不受影响
        encoding_detected = chardet.detect(raw_data)["encoding"]
        return encoding_detected

    if request.method == 'GET':
        return render(request, 'stock/import_industry_stock.html')

    if request.method == 'POST' and request.FILES.get('file'):

        if not (request.user.is_authenticated and request.user.is_superuser):
            return HttpResponseForbidden("权限不足：需要管理员身份")

        csv_file = request.FILES['file']
        encoding_str = detect_encoding(csv_file)
        decoded_file = csv_file.read().decode(encoding_str).splitlines()

        # 使用制表符分隔的DictReader
        reader = csv.DictReader(decoded_file, delimiter='\t')

        changed_entries = []
        for row in reader:
            code = row.get('代码', '').lstrip("'")
            name = row.get('名称', '')
            industry = row.get('所属行业', '')

            if industry == '--':
                continue

            stock, created = IndustryStock.objects.get_or_create(
                code=code,
                defaults={'name': name, 'industry': industry}
            )

            if created:
                changed_entries.append({'代码': code,
                                        '名称': name,
                                        '所属行业': industry,
                                        '类型': '新增'})
            else:
                if stock.name != name or stock.industry != industry:
                    changed_entries.append({'代码': code,
                                            '名称': name,
                                            '所属行业': industry,
                                            '类型': '更新'})
                    stock.name = name
                    stock.industry = industry
                    stock.save()

        response_data = {
            'data_list': changed_entries,
            'success': True
        }
        return render(request,
                      'stock/import_industry_stock.html',
                      response_data)

    # 处理非POST请求
    return HttpResponse("请使用POST方法上传CSV文件")
