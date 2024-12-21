from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import StockBasicInfo


class StockBasicInfoAPIView(APIView):
    """
    API View to handle POST requests for adding stock data.
    """

    def post(self, request, *args, **kwargs):

        json_data = request.data
        for data in json_data:

            date = data.get('date')
            code = data.get('code')
            name = data.get('name')
            open_price = data.get('open_price')
            close_price = data.get('close_price')
            high_price = data.get('high_price')
            low_price = data.get('low_price')
            money = data.get('money')

            stock, created = StockBasicInfo.objects.get_or_create(
                date=date,
                code=code,
                defaults={
                    "name": name,
                    "open_price": open_price,
                    "close_price": close_price,
                    "high_price": high_price,
                    "low_price": low_price,
                    "money": money,
                },
            )

        return Response({"message": "Record created successfully."},
                        status=status.HTTP_201_CREATED)
