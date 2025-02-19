from django.db import models


class IndustryStockManager(models.Manager):

    def get_industry_name_list(self):
        return self.values('industry').distinct()

    def get_stock_code_industry_dict(self):
        values = self.values_list('code', 'industry')
        return {code: industry for code, industry in values}

    def get_stock_code_name_dict(self, industry=''):
        if not industry:
            return self.values('code', 'name')
        return self.filter(industry=industry).values('code', 'name')

    def get_stock_code_list(self, industry=''):
        if not industry:
            return self.values_list('code', flat=True)
        return self.filter(industry=industry).values_list('code', flat=True)


class IndustryStock(models.Model):

    code = models.CharField(max_length=10, db_index=True, unique=True)
    name = models.CharField(max_length=100, db_index=True)
    industry = models.CharField(max_length=100, db_index=True)

    objects = IndustryStockManager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.zfill(6)
        super().save(*args, **kwargs)


class StockTradeInfoManager(models.Manager):

    def get_trade_date_list(self, count=30):
        return self.values_list('date', flat=True).distinct().order_by('-date')[:count]

    def get_trade_info_by_date(self, date):
        return self.filter(date=date)


class StockTradeInfo(models.Model):

    date = models.DateField(db_index=True)
    code = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=100, db_index=True)

    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    money = models.DecimalField(max_digits=10, decimal_places=2)

    objects = StockTradeInfoManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['date', 'code'], name='unique_date_code')
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 自动补齐 code 字段为 6 位
        if self.code:
            self.code = self.code.zfill(6)
        super().save(*args, **kwargs)
