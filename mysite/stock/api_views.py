import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Stocks, Industris

logger = logging.getLogger('stock')


class StockIndustryInfoAPIView(APIView):
    """
    API View to handle POST requests for adding stock data.
    """

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
                logger.warning(f"{model.__name__} info mismatch: {data_dict} != {db_data}")

    def handle_industries(self, industries_dict, level):
        """
        A helper function to process industry data.

        :param industries_dict: Dictionary containing industry data
        :param level: Industry level (2 or 3)
        """
        for code, name in industries_dict.items():
            if code:
                self.create_or_update_record(
                    model=Industris,
                    unique_field="code",
                    data_dict={"code": code, "name": name, "level": level},
                    defaults={"name": name, "level": level}
                )

    def post(self, request, *args, **kwargs):

        json_data = request.data

        # Process stock data
        stock_data_list = json_data.get('stocks', [])
        for stock_data in stock_data_list:
            code, name, sw_l2, sw_l3 = \
                    stock_data[0], stock_data[1] or '', stock_data[2] or '', stock_data[3] or ''
            if code and name:
                self.create_or_update_record(
                    model=Stocks,
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
