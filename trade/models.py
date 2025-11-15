# models.py (Django ORM)

from django.db import models

class Coin(models.Model):
    tag = models.CharField(max_length=10) #'BTC'
    candle_size = models.CharField(max_length=10) #'15m'
    last_updated = models.DateTimeField(auto_now=True)

class allowed_comb(models.Model):
    direction = models.CharField(max_length=10) #'BTC'
    candle_size = models.CharField(max_length=10) #'15m'
    inefficiency_restrict = models.FloatField() # 0.02
    orderblock_restrict = models.FloatField() # 0.02
    win_rate = models.FloatField() # 0.535

class TradeLog(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    candle_size = models.CharField(max_length=10)
    direction = models.CharField(max_length=10)  # BUY or SELL
    entry_price = models.FloatField()
    stop_loss = models.FloatField()
    coin_tag = models.CharField(max_length=40)
    take_profit = models.FloatField()
    opened_at = models.FloatField()
    closed_at = models.FloatField(null=True, blank=True)
    log_type = models.CharField(max_length=40, default='back_testing')
    profit_loss = models.CharField(max_length=4,null=True, blank=True) #win or lose
    seed_ratio = models.FloatField()


class Candle_stick(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()
    structure_regime = models.CharField(  # 'up' | 'down' | 'range'
        max_length=8, null=True, blank=True, db_index=True
    )
    structure_event = models.CharField(   # 'BOS' | 'CHoCH' | 'none'
        max_length=6, null=True, blank=True, db_index=True
    )
    open_time = models.FloatField()

class Day_Candle_stick(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()
    open_time = models.FloatField()

    direction = models.CharField(max_length=10, null=True, blank=True) #bullish or bearish

    abnormal_return = models.FloatField(null=True, blank=True)   # z-score 값
    ar_upper = models.FloatField(null=True, blank=True)          # AR 상단 경계 가격
    ar_lower = models.FloatField(null=True, blank=True)          # AR 하단 경계 가격
    vs_tsmom = models.FloatField(null=True, blank=True)          # z-score 값


class Hour_Candle_stick(models.Model):
    day_candle_stick = models.ForeignKey(Day_Candle_stick, on_delete=models.CASCADE)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()
    open_time = models.FloatField()

    direction = models.CharField(max_length=4, null=True, blank=True) #bullish or bearish
    structure = models.CharField(max_length=6, null=True, blank=True) # 'BOS' | 'CHoCH' | 'none'
    # ar_trigered = models.BooleanField(default=False)
    # vs_trigered = models.BooleanField(default=False)


class Order_block(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    open_time = models.FloatField()

    

class Entry_point(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    tag = models.CharField(max_length=40)
    direction = models.CharField(max_length=40) # BUY/SELL
    entry_price = models.FloatField()
    take_profit = models.FloatField()
    stop_loss = models.FloatField()
    gap = models.FloatField()