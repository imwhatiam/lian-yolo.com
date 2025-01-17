from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Stocks, Industris


class StockIndustryInfoAPIView(APIView):
    """
    API View to handle POST requests for adding stock data.
    """

    def post(self, request, *args, **kwargs):

        # {
        #     'stocks': [
        #         ['000001', '平安银行', '801783', '857831'],
        #         ['000011', '深物业A', '801181', '851811']
        #         ...
        #     ],
        #     'industris': {
        #         'sw_l2': {
        #             '801783': '股份制银行',
        #             '801181': '房地产开发',
        #             ...
        #         },
        #         'sw_l3': {
        #             '857831': '股份制银行',
        #             '851811': '房地产开发',
        #         }
        #     }
        # }

        json_data = request.data

        # add stock info
        stock_data_list = json_data.get('stocks')
        for stock_data in stock_data_list:

            code = stock_data[0]
            if not code:
                continue

            name = stock_data[1] or ''
            if not name:
                continue

            sw_l2 = stock_data[2] or ''
            sw_l3 = stock_data[3] or ''

            stock, created = Stocks.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "sw_l2": sw_l2,
                    "sw_l3": sw_l3,
                },
            )

        # add industry info
        sw_l2_dict = json_data.get('industris').get('sw_l2')
        for code, name in sw_l2_dict.items():
            if not code:
                continue
            industry, created = Industris.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "level": 2,
                },
            )

        sw_l3_dict = json_data.get('industris').get('sw_l3')
        for code, name in sw_l3_dict.items():
            if not code:
                continue
            industry, created = Industris.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "level": 3,
                },
            )

        return Response({"message": "Record created successfully."},
                        status=status.HTTP_201_CREATED)
