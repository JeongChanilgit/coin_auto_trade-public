from django.contrib import admin
from .models import Coin, TradeLog, Candle_stick, Entry_point,Order_block,allowed_comb, Day_Candle_stick, Hour_Candle_stick

admin.site.register(Coin)
admin.site.register(TradeLog)
admin.site.register(Candle_stick)
admin.site.register(Entry_point)
admin.site.register(Order_block)
admin.site.register(allowed_comb)
admin.site.register(Day_Candle_stick)
admin.site.register(Hour_Candle_stick)