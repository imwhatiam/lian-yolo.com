import logging
import requests
import pandas as pd
from datetime import datetime

from django.core.cache import cache

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import IndustryStock, StockTradeInfo
from .utils import get_trade_info_pd

logger = logging.getLogger(__name__)


class BigRiseVolumeAPIView(APIView):

    def get(self, request, *args, **kwargs):

        # Extract and parse query parameters with defaults
        last_x_days = int(request.GET.get('last_x_days', 5))
        rise = int(request.GET.get('rise', 8))

        # Generate unique cache key based on parameters
        cache_key = f"big_rise_volume_{last_x_days}_{rise}"
        cached_data = cache.get(cache_key)

        # Return cached response if available
        if cached_data:
            return Response({"data": cached_data}, status=status.HTTP_200_OK)

        # Fetch stock codes and retrieve trade data
        stock_code_list = IndustryStock.objects.get_stock_code_list()
        df = get_trade_info_pd(stock_code_list, last_x_days)

        # Data preprocessing
        # Convert money unit from 10k to yuan (assuming original unit is 10k RMB)
        df["money"] *= 10000

        # Filter stocks based on rise percentage
        filtered_df = df[df["change_pct"] > rise]

        # Sort by percentage change descending
        sorted_df = filtered_df.sort_values(
            by="change_pct",
            ascending=False
        )

        # Process and organize data
        result = {}

        # Group by date and industry
        for (date, industry), group in sorted_df.groupby(['date', 'industry'], sort=False):
            str_date = str(date)

            # Initialize date entry if not exists
            if str_date not in result:
                result[str_date] = {}

            # Sort group entries by change_pct and money
            sorted_entries = group[
                ['name', 'change_pct', 'money']
            ].sort_values(
                by=['change_pct', 'money'],
                ascending=[False, False]
            ).values.tolist()

            result[str_date][industry] = sorted_entries

        # Reorder final structure
        # 1. Sort dates in descending order
        # 2. Sort industries by number of entries descending within each date
        ordered_result = {
            date: {
                industry: result[date][industry]
                for industry in sorted(
                    result[date].keys(),
                    key=lambda k: len(result[date][k]),
                    reverse=True
                )
            }
            for date in sorted(result.keys(), reverse=True)
        }

        # Cache results for 24 hours
        cache.set(cache_key, ordered_result, timeout=60 * 60 * 24)

        return Response({"data": ordered_result}, status=status.HTTP_200_OK)


class TradingCrowdingAPIView(APIView):

    def post(self, request, *args, **kwargs):

        try:
            json_data = request.data
        except ValueError:
            error_msg = "Invalid JSON format"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        cache_key_parts = ["trading_crowding"]

        # check parameters and generate cache key
        last_x_days = int(request.GET.get('last_x_days', 50))
        try:
            last_x_days = int(last_x_days)
            cache_key_parts.append(str(last_x_days))
        except ValueError:
            error_msg = f"Invalid last_x_days: {last_x_days}"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        latest_trade_date = json_data.get("latest_trade_date")
        if latest_trade_date:
            try:
                # 2025-01-01
                latest_trade_date_obj = datetime.strptime(latest_trade_date,
                                                          "%Y-%m-%d").date()
                cache_key_parts.append(latest_trade_date)
            except ValueError:
                error_msg = f"Invalid latest_trade_date: {latest_trade_date}"
                return Response({"error": error_msg},
                                status=status.HTTP_400_BAD_REQUEST)

        industry_list = json_data.get("industry_list", [])
        if not industry_list:
            error_msg = "Industry list is empty"
            return Response({"error": error_msg},
                            status=status.HTTP_400_BAD_REQUEST)

        # check if data is already cached
        cache_key_parts.append(','.join(industry_list))
        cache_key = '_'.join(cache_key_parts)
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        # get trade date list
        if latest_trade_date:
            trade_dates = StockTradeInfo.objects.filter(
                date__lte=latest_trade_date_obj
            ).order_by('-date').values_list('date', flat=True).distinct()[:last_x_days]

            trade_date_list = sorted(trade_dates)
        else:
            trade_date_list = StockTradeInfo.objects.get_trade_date_list(count=last_x_days)

        # Process and generate result
        result = {}
        for trade_date in trade_date_list:

            trade_infos = StockTradeInfo.objects.filter(date=trade_date)
            trade_data = list(trade_infos.values('code', 'money'))
            df_trade = pd.DataFrame(trade_data)
            if df_trade.empty:
                continue

            total_money = df_trade['money'].sum()

            codes = df_trade['code'].unique()
            stocks = IndustryStock.objects.filter(code__in=codes)

            code_to_industry = {stock.code: stock.industry for stock in stocks}
            df_trade['industry'] = df_trade['code'].map(code_to_industry)

            industry_money = {}
            for industry in industry_list:
                money_sum = df_trade[df_trade['industry'] == industry]['money'].sum()
                industry_money[f"{industry}"] = money_sum

            result[str(trade_date)] = {
                'total_money': total_money,
                **industry_money
            }

        cache.set(cache_key, result, timeout=60 * 60 * 24)

        return Response({"data": result}, status=status.HTTP_200_OK)


class WindInfoAPIView(APIView):

    def get(self, request, *args, **kwargs):

        # Generate unique cache key
        cache_key = "wind_info"

        # Check if data is already cached
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        wind_api_url = "https://index_api.wind.com.cn/indexofficialwebsite/Kline"

        # Send a GET request to the Wind API
        response = requests.get(wind_api_url, verify=False)
        result = response.json()

        # Check if the request was successful
        if response.status_code == 200:

            # Cache results for 24 hours
            cache.set(cache_key, result, timeout=60 * 60 * 24)

            # Return the Wind API's response
            return Response(result, status=status.HTTP_200_OK)
        else:
            # Return an error response if the request failed
            return Response({"error": "Failed to fetch data from Wind API"},
                            status=status.HTTP_400_BAD_REQUEST)
