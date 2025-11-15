from trade.models import Coin, Candle_stick, TradeLog, Order_block, Day_Candle_stick, Hour_Candle_stick
from trade.market_api import get_server_time, get_candle_data
from trade.target_coins import symbols, candle_sizes
from celery import shared_task
from trade.smc_utils import compute_vw_tsmom_and_ar
@shared_task
def fetch_coin():
    for symbol in symbols:
        for candle_size in candle_sizes:
            Coin.objects.get_or_create(
                tag=symbol,
                candle_size=candle_size
            )

@shared_task
def fetch_candle_data(coin):
    try:    
        candle_stick_filter = Candle_stick.objects.filter(coin=coin).order_by('open_time')
        num_candle = candle_stick_filter.count()
        last_open_candle = candle_stick_filter.last()
        first_open_candle = candle_stick_filter.first()

        now_ms = get_server_time()
        if coin.candle_size == '5m':
            minutes = 5
        elif coin.candle_size == '15m':
            minutes = 15
        elif coin.candle_size == '30m':
            minutes = 30
        elif coin.candle_size =='1h':
            minutes = 60
        elif coin.candle_size =='2h':
            minutes = 120

        elif coin.candle_size =='4h':
            minutes = 240
        elif coin.candle_size =='6h':
            minutes = 360
        elif coin.candle_size =='8h':
            minutes = 480
        elif coin.candle_size =='12h':
            minutes = 720
    
        if num_candle < 499 or last_open_candle.open_time < now_ms - 2 * 60000 * minutes:

            past_prices = get_candle_data(coin, 499)
            Candle_stick.objects.filter(coin=coin).delete()
            TradeLog.objects.filter(coin=coin).delete()
            Order_block.objects.filter(coin=coin).delete()
            to_create = []
            for candle in past_prices:
                    to_create.append(Candle_stick(
                        coin=coin,
                        open=candle['open'],
                        high=candle['high'],
                        low=candle['low'],
                        close=candle['close'],
                        volume=candle['volume'],
                        open_time=candle['open_time']
                    ))
            
            Candle_stick.objects.filter(coin=coin).delete()
            Candle_stick.objects.bulk_create(to_create)


        elif last_open_candle.open_time < now_ms - 1 * 60000 * minutes:

            past_prices = get_candle_data(coin, 99)
            first_open_candle.delete()
            Candle_stick.objects.create(
                    coin=coin,
                    open=past_prices[-1]['open'],
                    high=past_prices[-1]['high'],
                    low=past_prices[-1]['low'],
                    close=past_prices[-1]['close'],
                    volume=past_prices[-1]['volume'],
                    open_time=past_prices[-1]['open_time']
                )
            
        else:
            past_prices = get_candle_data(coin, 99)
            last_open_candle.delete()
            Candle_stick.objects.create(
                    coin=coin,
                    open=past_prices[-1]['open'],
                    high=past_prices[-1]['high'],
                    low=past_prices[-1]['low'],
                    close=past_prices[-1]['close'],
                    volume=past_prices[-1]['volume'],
                    open_time=past_prices[-1]['open_time']
                )

    except Exception as e:
        print(f"[ERROR] {coin.tag}-{coin.candle_size} 캔들 데이터 확보 실패: {e}")


@shared_task
def fetch_day_candle_data(coin):
    """Day_Candle_stick만 업데이트하거나 저장하는 함수"""
    try:    
        candle_stick_filter = Day_Candle_stick.objects.filter(coin=coin).order_by('open_time')
        num_candle = candle_stick_filter.count()
        last_open_candle = candle_stick_filter.last()
        first_open_candle = candle_stick_filter.first()
        tag = coin.tag
        candle_size = coin.candle_size
        now_ms = get_server_time()
        
        if coin.candle_size == '5m':
            minutes = 5
        elif coin.candle_size == '15m':
            minutes = 15
        elif coin.candle_size == '30m':
            minutes = 30
        elif coin.candle_size =='1h':
            minutes = 60
        elif coin.candle_size =='2h':
            minutes = 120
        elif coin.candle_size =='4h':
            minutes = 240
        elif coin.candle_size =='6h':
            minutes = 360
        elif coin.candle_size =='8h':
            minutes = 480
        elif coin.candle_size =='12h':
            minutes = 720
        elif coin.candle_size =='1d':
            minutes = 1440

        if num_candle < 499 or last_open_candle.open_time < now_ms - 2 * 60000 * minutes:
            # 전체 캔들 데이터를 새로 가져와서 재구축
            past_prices = get_candle_data(tag, candle_size, 499)
            Day_Candle_stick.objects.filter(coin=coin).delete()
            TradeLog.objects.filter(coin=coin).delete()
            Order_block.objects.filter(coin=coin).delete()
            
            to_create = []
            for candle in past_prices:
                to_create.append(Day_Candle_stick(
                    coin=coin,
                    open=candle['open'],
                    high=candle['high'],
                    low=candle['low'],
                    close=candle['close'],
                    volume=candle['volume'],
                    open_time=candle['open_time']
                ))
            
            Day_Candle_stick.objects.bulk_create(to_create)

        elif last_open_candle.open_time < now_ms - 1 * 60000 * minutes:
            # 새로운 캔들 하나 추가하고 가장 오래된 캔들 삭제
            past_prices = get_candle_data(tag, candle_size, 99)
            first_open_candle.delete()
            Day_Candle_stick.objects.create(
                coin=coin,
                open=past_prices[-1]['open'],
                high=past_prices[-1]['high'],
                low=past_prices[-1]['low'],
                close=past_prices[-1]['close'],
                volume=past_prices[-1]['volume'],
                open_time=past_prices[-1]['open_time']
            )
            
        else:
            # 마지막 캔들 업데이트
            past_prices = get_candle_data(tag, candle_size, 99)
            last_open_candle.delete()
            Day_Candle_stick.objects.create(
                coin=coin,
                open=past_prices[-1]['open'],
                high=past_prices[-1]['high'],
                low=past_prices[-1]['low'],
                close=past_prices[-1]['close'],
                volume=past_prices[-1]['volume'],
                open_time=past_prices[-1]['open_time']
            )

    except Exception as e:
        print(f"[ERROR] {coin.tag}-{coin.candle_size} Day 캔들 데이터 확보 실패: {e}")


@shared_task
def fetch_day_hour_candle_data(coin):
    try:    
        candle_stick_filter = Day_Candle_stick.objects.filter(coin=coin).order_by('open_time')
        num_candle = candle_stick_filter.count()
        last_open_candle = candle_stick_filter.last()
        first_open_candle = candle_stick_filter.first()
        tag = coin.tag
        candle_size = coin.candle_size
        now_ms = get_server_time()
        if coin.candle_size == '5m':
            minutes = 5
        elif coin.candle_size == '15m':
            minutes = 15
        elif coin.candle_size == '30m':
            minutes = 30
        elif coin.candle_size =='1h':
            minutes = 60
        elif coin.candle_size =='2h':
            minutes = 120

        elif coin.candle_size =='4h':
            minutes = 240
        elif coin.candle_size =='6h':
            minutes = 360
        elif coin.candle_size =='8h':
            minutes = 480
        elif coin.candle_size =='12h':
            minutes = 720
        elif coin.candle_size =='1d':
            minutes = 1440


        if num_candle < 499 or last_open_candle.open_time < now_ms - 2 * 60000 * minutes:

            past_prices = get_candle_data(tag, candle_size, 499)
            Day_Candle_stick.objects.filter(coin=coin).delete()
            TradeLog.objects.filter(coin=coin).delete()
            Order_block.objects.filter(coin=coin).delete()
            to_create = []
            for candle in past_prices:
                    to_create.append(Day_Candle_stick(
                        coin=coin,
                        open=candle['open'],
                        high=candle['high'],
                        low=candle['low'],
                        close=candle['close'],
                        volume=candle['volume'],
                        open_time=candle['open_time']
                    ))
            

            Day_Candle_stick.objects.filter(coin=coin).delete()
            Day_Candle_stick.objects.bulk_create(to_create)
            for day_candle in Day_Candle_stick.objects.filter(coin=coin):
                to_create = []
                hour_past_prices = get_candle_data(tag, '1h', 24, start_time=day_candle.open_time)
                for hour_candle in hour_past_prices:
                    to_create.append(Hour_Candle_stick(
                        day_candle_stick=day_candle,
                        open=hour_candle['open'],
                        high=hour_candle['high'],
                        low=hour_candle['low'],
                        close=hour_candle['close'],
                        volume=hour_candle['volume'],
                        open_time=hour_candle['open_time']
                    ))
            
                Hour_Candle_stick.objects.filter(day_candle_stick=day_candle).delete()
                Hour_Candle_stick.objects.bulk_create(to_create)


        elif last_open_candle.open_time < now_ms - 1 * 60000 * minutes:

            past_prices = get_candle_data(tag, candle_size, 99)
            Hour_Candle_stick.objects.filter(day_candle_stick=first_open_candle).delete()
            first_open_candle.delete()
            Day_Candle_stick.objects.create(
                    coin=coin,
                    open=past_prices[-1]['open'],
                    high=past_prices[-1]['high'],
                    low=past_prices[-1]['low'],
                    close=past_prices[-1]['close'],
                    volume=past_prices[-1]['volume'],
                    open_time=past_prices[-1]['open_time']
                )
            to_create = []
            hour_past_prices = get_candle_data(tag, '1h', 24, start_time=past_prices[-1]['open_time'])
            for hour_candle in hour_past_prices:
                to_create.append(Hour_Candle_stick(
                    day_candle_stick=Day_Candle_stick.objects.filter(coin=coin).last(),
                    open=hour_candle['open'],
                    high=hour_candle['high'],
                    low=hour_candle['low'],
                    close=hour_candle['close'],
                    volume=hour_candle['volume'],
                    open_time=hour_candle['open_time']
                ))
            Hour_Candle_stick.objects.bulk_create(to_create)
        else:
            past_prices = get_candle_data(tag, candle_size, 99)
            Hour_Candle_stick.objects.filter(day_candle_stick=last_open_candle).delete()
            last_open_candle.delete()
            Day_Candle_stick.objects.create(
                    coin=coin,
                    open=past_prices[-1]['open'],
                    high=past_prices[-1]['high'],
                    low=past_prices[-1]['low'],
                    close=past_prices[-1]['close'],
                    volume=past_prices[-1]['volume'],
                    open_time=past_prices[-1]['open_time']
                )
            to_create = []
            hour_past_prices = get_candle_data(tag, '1h', 24, start_time=past_prices[-1]['open_time'])
            for hour_candle in hour_past_prices:
                to_create.append(Hour_Candle_stick(
                    day_candle_stick=Day_Candle_stick.objects.filter(coin=coin).last(),
                    open=hour_candle['open'],
                    high=hour_candle['high'],
                    low=hour_candle['low'],
                    close=hour_candle['close'],
                    volume=hour_candle['volume'],
                    open_time=hour_candle['open_time']
                ))
            Hour_Candle_stick.objects.bulk_create(to_create)

    except Exception as e:
        print(f"[ERROR] {coin.tag}-{coin.candle_size} 캔들 데이터 확보 실패: {e}")

@shared_task
def fetch_vw_tsmom_and_ar(coin):
    compute_vw_tsmom_and_ar(coin.tag, coin.candle_size)

def fetch_all():
    for coin in Coin.objects.all():
        fetch_day_candle_data(coin)
        fetch_vw_tsmom_and_ar(coin)

