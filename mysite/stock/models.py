from django.db import models


class StockBasicInfo(models.Model):

    date = models.DateField(db_index=True)
    code = models.CharField(max_length=10, db_index=True)
    name = models.CharField(max_length=10, db_index=True)

    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    money = models.DecimalField(max_digits=10, decimal_places=2)

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
