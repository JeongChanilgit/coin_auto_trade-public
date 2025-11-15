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

    candle_sizes = ['15m']
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
                   'KAVA', 'AVAX', 'THETA']

    candle_sizes = ['30m']
    for tag in coin_list:
        for candle_size in candle_sizes:
            a,b=Coin.objects.get_or_create(
                    tag = tag,
                    candle_size = candle_size
                    )
            
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
            elif coin.candle_size =='1d':
                minutes = 1440
            elif coin.candle_size =='3d':
                minutes = 4320
        
            if num_candle < 1499 or last_open_candle.open_time < now_ms - 2 * 60000 * minutes:

                past_prices = get_candle_data(coin, 1499)
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
                        new_entry = backtesting_and_find_entry(past_prices, coin, allowed_combination, 3)
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
def final_geometric_return_100pct(winrate, earnrate, trades):
    """
    100% 베팅 시의 올바른 기하 평균 복리 수익률을 계산합니다.
    (귀하의 원본 코드에서 복리 계산 오류를 수정한 버전)
    """
    
    # --- 1. 기본 상수 및 실제 수익률 정의 ---
    R_win_base = 0.0098
    R_loss_fixed = -0.011
    if earnrate == 2:
        R_win = 0.0192
        R_loss = -0.0114
    elif earnrate == 3:
        R_win = 0.0292
        R_loss = -0.0114
    elif earnrate == 4:
        R_win = 0.0392
        R_loss = -0.0114
    
    p = winrate
    q = 1 - winrate
    
    # --- 2. 100% 베팅 시의 기하 평균 팩터(G) 계산 ---
    # G_factor = [ (1 + R_win)^p ] * [ (1 + R_loss)^q ]
    
    try:
        factor_win = (1 + R_win) ** p
        factor_loss = (1 + R_loss) ** q # (1 - 0.011)
        
        G_factor = factor_win * factor_loss
        
    except ValueError:
        return -100.0 # 파산

    # --- 3. 최종 수익률 계산 ---
    total_factor = G_factor ** trades
    final_return_percent = (total_factor - 1) * 100
    
    return final_return_percent



@shared_task
def find_allowed_combination():
    candle_sizes = ['15m']
    direction = ['BUY', 'SELL']
    inefficiency_restricts = [0.005, 0.007, 0.01, 0.013, 0.016, 0.02]
    orderblock_restricts = [0.005, 0.007, 0.01, 0.013, 0.016, 0.02]
    magic_rate = 0.5#  ***** 0.525 # 이 비율을 넘겨야 수익 가능!
    trade_rate_result = []
    Candle_stick_data = {}
    earn_rate = 3
    tags = Coin.objects.values_list('tag', flat=True).distinct()
    max_expect = 0
    max_expect_comb = None
    for candle_size in candle_sizes:
        for tag in tags:
            coin = Coin.objects.get(tag=tag, candle_size=candle_size)
            Candle_stick_data[tag+candle_size] = Candle_stick.objects.filter(coin=coin).order_by('open_time')
    
    for size in candle_sizes:
        for inef_res in inefficiency_restricts:
            for ob_res in orderblock_restricts:
                buy_win, buy_lose, sell_win, sell_lose = 1, 1, 1, 1
                for tag in tags:
                   
                        past_prices = Candle_stick_data[tag+size]
                        coin = Coin.objects.get(tag=tag, candle_size=size)
                    
                        b_w, b_l, s_w, s_l = backtesting_for_allowed_comb(past_prices, coin, earn_rate, inef_res, ob_res)

                        
                        if (b_w+b_l+s_w+s_l) > 1:
                            buy_win += b_w
                            buy_lose += b_l
                            sell_win += s_w
                            sell_lose += s_l

                # print(size,'BUY',inef_res,ob_res,buy_win/(buy_win+buy_lose),buy_win+buy_lose)
                # print(size,'SELL',inef_res,ob_res,sell_win/(sell_win+sell_lose),sell_win+sell_lose)
                if buy_win+buy_lose+sell_win+sell_lose > 100:
                    print(inef_res,ob_res)
                    expect = final_geometric_return_100pct(round((buy_win+sell_win)/(buy_win+buy_lose+sell_win+sell_lose),3),earn_rate,buy_win+buy_lose+sell_win+sell_lose)
                    print(expect)
                    if expect > max_expect:
                        max_expect = expect
                        max_expect_comb = [size,inef_res,ob_res]
                    print('long',size,final_geometric_return_100pct(round((buy_win)/(buy_win+buy_lose),3),earn_rate,buy_win+buy_lose))
                    print('short',size,final_geometric_return_100pct(round((sell_win)/(sell_win+sell_lose),3),earn_rate,sell_win+sell_lose))
                    print('')


                trade_rate_result.append([size,'BUY',inef_res,ob_res,buy_win/(buy_win+buy_lose),buy_win+buy_lose])
                trade_rate_result.append([size,'SELL',inef_res,ob_res,sell_win/(sell_win+sell_lose),sell_win+sell_lose])
    allowed_combination = []
    allowed_combination.append(allowed_comb(direction = 'BUY', candle_size = max_expect_comb[0], inefficiency_restrict = max_expect_comb[1], orderblock_restrict = max_expect_comb[2],win_rate=max_expect))
    allowed_combination.append(allowed_comb(direction = 'SELL', candle_size = max_expect_comb[0], inefficiency_restrict = max_expect_comb[1], orderblock_restrict = max_expect_comb[2],win_rate=max_expect))

    allowed_comb.objects.all().delete()
    for comb in allowed_combination:
        print(comb.direction, comb.candle_size, comb.inefficiency_restrict, comb.orderblock_restrict, comb.win_rate)
  
    allowed_comb.objects.bulk_create(allowed_combination)
    
@shared_task
def eraser():
    TradeLog.objects.all().delete()
    Order_block.objects.all().delete()


