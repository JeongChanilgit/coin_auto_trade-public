from celery import shared_task
from trade.utils import backtesting_and_find_entry, get_candle_data, orderblock,  get_server_time, backtesting_for_allowed_comb
from trade.models import Coin, TradeLog, Candle_stick, Entry_point, Order_block, allowed_comb
import time


@shared_task
def fetch_coin():
    coin_list = ['BTC', 'ETH', 'XRP', 'SUI', 'BNB', 'EOS', 'BCH', 'LAYER', 'LTC', 'FARTCOIN', 'API3', 
                 'TRUMP', 'LINK', 'AAVE', 'AUCTION', 'ZRO', 'SOL', 'NEO', 'WIF', 'BERA', 'CRV', 'TON', 
                 'IP', 'MLN', 'ONDO', 'FIL', 'OP', 'NIL', 'DOT', 'TAO', 'KAITO', 'ORDI', 'ORCA', 'APT', 
                 'ETC', 'FORM', 'W', 'AI16Z', 'ARB', 'RENDER', 'INJ', 'MKR', 'ATOM', 'EIGEN', 'ADA', 
                 'ALGO', 'DYDX', 'OM', 'ENS', 'ZEN', 'BANANA', 'GRASS', 'AR', 'THE', 'VIRTUAL', 'PAXG',
                   'KAVA', 'AVAX', 'THETA']

    candle_sizes = ['3m','5m','15m']
    for tag in coin_list:
        for candle_size in candle_sizes:
            a,b=Coin.objects.get_or_create(
                    tag = tag,
                    candle_size = candle_size
                    )
@shared_task        
def fix():
    coin_list = ['BTC', 'ETH', 'XRP', 'SUI', 'BNB', 'EOS', 'BCH', 'LAYER', 'LTC', 'FARTCOIN', 'API3', 
                 'TRUMP', 'LINK', 'AAVE', 'AUCTION', 'ZRO', 'SOL', 'NEO', 'WIF', 'BERA', 'CRV', 'TON', 
                 'IP', 'MLN', 'ONDO', 'FIL', 'OP', 'NIL', 'DOT', 'TAO', 'KAITO', 'ORDI', 'ORCA', 'APT', 
                 'ETC', 'FORM', 'W', 'AI16Z', 'ARB', 'RENDER', 'INJ', 'MKR', 'ATOM', 'EIGEN', 'ADA', 
                 'ALGO', 'DYDX', 'OM', 'ENS', 'ZEN', 'BANANA', 'GRASS', 'AR', 'THE', 'VIRTUAL', 'PAXG',
                   'KAVA', 'AVAX', 'THETA','PET','NEAR','AXL','MOODENG',"NEIRO",'PET','DOGE','UNI','ENA','HYPE','MASK','PNUT','ANIME']

    # candle_sizes = ['30m','8h']
    # for tag in coin_list:
    #     for candle_size in candle_sizes:
    #         a,b=Coin.objects.get_or_create(
    #                 tag = tag,
    #                 candle_size = candle_size
    #                 )
            
@shared_task
def fetch_candle_data():

    coins = Coin.objects.all()
    for coin in coins:
        try:    
            candle_stick_filter = Candle_stick.objects.filter(coin=coin).order_by('open_time')
            num_candle = candle_stick_filter.count()
            last_open_candle = candle_stick_filter.last()
            first_open_candle = candle_stick_filter.first()

            now_ms = get_server_time()
            if coin.candle_size == '3m':
                minutes = 3
            elif coin.candle_size == '5m':
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
                        open_time=past_prices[-1]['open_time']
                    )

        except Exception as e:
            print(f"[ERROR] {coin.tag}-{coin.candle_size} 캔들 데이터 확보 실패: {e}")

@shared_task
def back_testing_and_fetch_entry_point():
    allowed_combinations = allowed_comb.objects.all()
    new_entry_points = []
    coins = Coin.objects.all()

    Candle_stick_data = {}
    for coin in coins:
        Candle_stick_data[coin.tag+coin.candle_size] = Candle_stick.objects.filter(coin=coin).order_by('open_time')
    
    for allowed_combination in allowed_combinations: # direction, candle_size, inefficiency_restrict, ob_restrict
            for coin in coins:
                if coin.candle_size == allowed_combination.candle_size:
                    try:
                        past_prices = Candle_stick_data[coin.tag+coin.candle_size]
                        new_entry = backtesting_and_find_entry(past_prices, coin, allowed_combination, 2.1)
                        if new_entry != None:
                            new_entry_points.append(new_entry)
                        
                    except Exception as e:
                        print(f"[ERROR] {coin.tag}-{coin.candle_size} 분석 실패: {e}")
    Entry_point.objects.all().delete()
    entrys = []
    save = []
    for e_p in new_entry_points:
        if e_p.entry_price not in save:
            entrys.append(e_p)
            save.append(e_p.entry_price)
    Entry_point.objects.bulk_create(entrys)

@shared_task
def find_allowed_combination():
    candle_sizes = ['3m']
    direction = ['BUY', 'SELL']
    inefficiency_restricts = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03]
    orderblock_restricts = [0.003,0.005]
    magic_rate = 0.45#  ***** 0.525 # 이 비율을 넘겨야 수익 가능!
    trade_rate_result = []
    Candle_stick_data = {}
    tags = Coin.objects.values_list('tag', flat=True).distinct()
    for coin in Coin.objects.all():
        Candle_stick_data[coin.tag+coin.candle_size] = Candle_stick.objects.filter(coin=coin).order_by('open_time')

    for size in candle_sizes:

        for inef_res in inefficiency_restricts:
            for ob_res in orderblock_restricts:
                buy_win, buy_lose, sell_win, sell_lose = 1, 1, 1, 1
                for tag in tags:
                    try:
                        past_prices = Candle_stick_data[tag+size]

                        b_w, b_l, s_w, s_l = backtesting_for_allowed_comb(past_prices, coin, 2, inef_res, ob_res)
                        buy_win += b_w
                        buy_lose += b_l
                        sell_win += s_w
                        sell_lose += s_l
                    except:
                        print(tag+size)
                if buy_win+buy_lose > 10:
                    trade_rate_result.append([size,'BUY',inef_res,ob_res,buy_win/(buy_win+buy_lose),buy_win+buy_lose])
                if sell_win+sell_lose > 10:
                    trade_rate_result.append([size,'SELL',inef_res,ob_res,sell_win/(sell_win+sell_lose),sell_win+sell_lose])
    trade_rate_result.sort(key = lambda x: x[2])
    trade_rate_result.sort(key = lambda x: x[3])
    trade_rate_result.sort(reverse = True,key = lambda x: x[4])
    print(trade_rate_result)
    allowed_combination = []

    temp_rate = 1.0
    for comb in trade_rate_result:
        if temp_rate > round(comb[4],5) > magic_rate:
        #     temp_rate = round(comb[4],5)
           
        #     if comb[5] >= 0:

        #         flag = 1
        #         for  combination in allowed_combination:
        #             if combination.direction == comb[1] and combination.candle_size == comb[0] and combination.inefficiency_restrict <= comb[2]  and combination.orderblock_restrict <= comb[3]:
        #                 flag = 0
        #             if flag:
                    
               
            allowed_combination.append(allowed_comb(direction = comb[1], candle_size = comb[0], inefficiency_restrict = comb[2], orderblock_restrict = comb[3]))

    allowed_comb.objects.all().delete()
    allowed_comb.objects.bulk_create(allowed_combination)
    
@shared_task
def eraser():
    TradeLog.objects.all().delete()
    Order_block.objects.all().delete()


