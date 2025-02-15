import logging
import requests

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

    def get(self, request, *args, **kwargs):

        trade_date_list = StockTradeInfo.objects.get_trade_date_list()
        result = {
            "trade_date_list": trade_date_list,
        }
        return Response({"data": result},
                        status=status.HTTP_200_OK)


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
