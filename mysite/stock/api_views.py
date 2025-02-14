import logging
import requests

from django.core.cache import cache

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from .models import Stock, Industry, IndustryStock
from .utils import get_trade_info_pd

logger = logging.getLogger(__name__)


class StockIndustryInfoAPIView(APIView):
    """
    API View to handle POST requests for adding stock data.
    """
    permission_classes = [IsAdminUser]

    def create_or_update_record(self, model, unique_field, data_dict, defaults):
        """
        A helper function to handle get_or_create logic and logging warnings for mismatched data.

        :param model: Django model to perform operations on
        :param unique_field: Field name to filter the model
        :param data_dict: Dictionary of data to filter or create
        :param defaults: Default values for creating a new record
        """
        obj, created = model.objects.get_or_create(
            **{unique_field: data_dict[unique_field]},
            defaults=defaults
        )

        if not created:
            db_data = {field: getattr(obj, field) for field in data_dict.keys()}
            if data_dict != db_data:
                msg = f"{model.__name__} info mismatch: {data_dict} != {db_data}"
                logger.warning(msg)

    def handle_industries(self, industries_dict, level):
        """
        A helper function to process industry data.

        :param industries_dict: Dictionary containing industry data
        :param level: Industry level (2 or 3)
        """
        for code, name in industries_dict.items():
            if code:
                self.create_or_update_record(
                    model=Industry,
                    unique_field="code",
                    data_dict={"code": code, "name": name, "level": level},
                    defaults={"name": name, "level": level}
                )

    def post(self, request, *args, **kwargs):

        json_data = request.data

        # Process stock data
        stock_data_list = json_data.get('stocks', [])
        for stock_data in stock_data_list:
            code, name, sw_l2, sw_l3 = (
                stock_data[0],
                stock_data[1] or '',
                stock_data[2] or '',
                stock_data[3] or ''
            )
            if code and name:
                self.create_or_update_record(
                    model=Stock,
                    unique_field="code",
                    data_dict={"code": code, "name": name, "sw_l2": sw_l2, "sw_l3": sw_l3},
                    defaults={"name": name, "sw_l2": sw_l2, "sw_l3": sw_l3}
                )

        # Process industry data
        industries = json_data.get('industris', {})
        self.handle_industries(industries.get('sw_l2', {}), level='2')
        self.handle_industries(industries.get('sw_l3', {}), level='3')

        return Response({"message": "Record created successfully."},
                        status=status.HTTP_201_CREATED)


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
